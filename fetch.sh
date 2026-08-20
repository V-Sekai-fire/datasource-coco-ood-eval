#!/usr/bin/env bash
# Fetch renditions.parquet from this repository's release.
#
# It is 120 MB, which is over GitHub's 100 MB file limit, so it is a release asset rather
# than a tracked file. styles.parquet is 793 bytes and is tracked.
set -euo pipefail
tag="${1:-v1}"
out="${2:-renditions.parquet}"
gh release download "$tag" --repo weftspun/coco-ood-eval --pattern renditions.parquet --output "$out" --clobber
python - "$out" <<'PY'
import sys, pyarrow.parquet as pq
t = pq.read_table(sys.argv[1])
assert t.num_rows == 1569, f"expected 1569 rows, got {t.num_rows}"
assert set(t.column_names) == {"style_id", "image_id", "jpeg"}, t.column_names
print(f"ok: {t.num_rows} rows, {len(set(t.column('image_id').to_pylist()))} distinct images")
PY
