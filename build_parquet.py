"""Turn the COCO-OOD zips into ETNF parquet, filtered to the 523 licence-clean images.

WHY PARQUET AND NOT AN ARCHIVE. CLAUDE.md: tabular data is parquet plus zstd. A tar of JPEGs
is an opaque blob that has to be unpacked before anything can be asked of it. As parquet the
renditions join to `dataflow-coco-gemx`'s `images.parquet` on `image_id`, so the licence of
every row is one join away rather than an assumption.

WHY 523 AND NOT 5,000. `dataflow-coco-gemx` measured that only 523 of val2017's 5,000 person
images are commercial-and-derivatives safe. The COCO-OOD sets restyle all 5,000, and a restyle
is exactly the derivative an ND licence forbids, so publishing the full set would undo the
filter `filter_coco_licenses.py` exists to apply. The allowlist is what makes this releasable.

ESSENTIAL TUPLE NORMAL FORM. Interned vocabulary for the style, satellite relation for the
payload, no NULLs, no derivable columns.

    styles.parquet      style_id int8 PK, name string
    renditions.parquet  style_id int8 FK, image_id int32 FK, jpeg binary

`image_id` is the COCO id, so it joins straight to `images.parquet` and through it to
`licenses.parquet`. Width, height and a payload hash are all derivable from `jpeg` or already
carried by `images.parquet`, so none of them are stored.

Also drops `__MACOSX/` entries: roughly half of every zip is macOS resource forks with no
image data in them.

Coverage is counted, not assumed. If a set is missing some of the 523 the shortfall is printed
and carried in the result, because a silent shortfall reads exactly like a clean filter.
"""

import hashlib
import json
import pathlib
import sys
import zipfile

import pyarrow as pa
import pyarrow.parquet as pq

ALLOWLIST = "6-datasource/dataflow-coco-gemx/coco_person_commercial_val2017/images.parquet"

# The directory each zip unpacks to, and the style name it carries. Read from the archives
# rather than guessed: monet.zip holds `val2017oil/`, which is why the style is named for what
# the directory says rather than for the file it arrived in.
SETS = [
    ("monet.zip", "val2017oil/", "oil"),
    ("ukiyoe.zip", "val2017ukiyoe/", "ukiyoe"),
    ("corruption.zip", "val2017_corr/", "corruption"),
]


def load_allowlist(root):
    t = pq.read_table(pathlib.Path(root) / ALLOWLIST)
    names = dict(zip(t.column("file_name").to_pylist(), t.column("image_id").to_pylist()))
    if len(names) != 523:
        raise SystemExit(f"allowlist is {len(names)} rows, expected 523")
    return names


def read_set(zip_path, prefix, allow):
    """Return rows and a coverage record. Hashes are kept only to verify the round trip."""
    rows, digests = [], {}
    with zipfile.ZipFile(zip_path) as z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        macosx = sum(1 for i in infos if i.filename.startswith("__MACOSX/"))
        for i in infos:
            if i.filename.startswith("__MACOSX/"):
                continue
            base = pathlib.PurePosixPath(i.filename).name
            if base not in allow:
                continue
            payload = z.read(i)
            rows.append((allow[base], payload))
            digests[allow[base]] = hashlib.sha256(payload).hexdigest()
    return rows, digests, len(infos), macosx


def main(root, out_dir):
    root, out_dir = pathlib.Path(root), pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    allow = load_allowlist(root)
    print(f"allowlist: {len(allow)} licence-clean val2017 images\n", flush=True)

    styles = [(i, name) for i, (_, _, name) in enumerate(SETS)]
    pq.write_table(
        pa.table(
            {
                "style_id": pa.array([s[0] for s in styles], pa.int8()),
                "name": pa.array([s[1] for s in styles], pa.string()),
            }
        ),
        out_dir / "styles.parquet",
        compression="zstd",
    )

    all_rows, report = [], []
    for style_id, (zname, prefix, sname) in enumerate(SETS):
        src = root / "6-datasource/coco-ood-eval" / zname
        rows, digests, entries, macosx = read_set(src, prefix, allow)
        found = {r[0] for r in rows}
        missing = sorted(set(allow.values()) - found)
        all_rows.extend((style_id, iid, blob) for iid, blob in rows)
        rec = {
            "style": sname,
            "source": zname,
            "zip_entries": entries,
            "macosx_dropped": macosx,
            "kept": len(rows),
            "allowlist": len(allow),
            "missing": len(missing),
            "bytes": sum(len(b) for _, b in rows),
        }
        report.append(rec)
        print(
            f"[{sname}] {entries} entries, {macosx} __MACOSX dropped, "
            f"kept {len(rows)}/{len(allow)}, missing {len(missing)}",
            flush=True,
        )
        if missing:
            print(f"[{sname}] first missing image_ids: {missing[:5]}", flush=True)

    tbl = pa.table(
        {
            "style_id": pa.array([r[0] for r in all_rows], pa.int8()),
            "image_id": pa.array([r[1] for r in all_rows], pa.int32()),
            "jpeg": pa.array([r[2] for r in all_rows], pa.binary()),
        }
    )
    dst = out_dir / "renditions.parquet"
    pq.write_table(tbl, dst, compression="zstd")

    # Read back and compare every payload. Writing and trusting is not verifying.
    back = pq.read_table(dst)
    ok = back.num_rows == tbl.num_rows
    bad = 0
    for sid, iid, blob in zip(
        back.column("style_id").to_pylist(),
        back.column("image_id").to_pylist(),
        back.column("jpeg").to_pylist(),
    ):
        if hashlib.sha256(blob).hexdigest() != hashlib.sha256(
            dict(((r[0], r[1]), r[2]) for r in all_rows)[(sid, iid)]
        ).hexdigest():
            bad += 1
    ok = ok and bad == 0

    print(
        f"\nrenditions.parquet: {tbl.num_rows} rows, "
        f"{dst.stat().st_size/1e6:.1f} MB, round-trip verified={ok} mismatches={bad}",
        flush=True,
    )
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
