# coco-ood-eval

The COCO-OOD stylized evaluation sets, filtered to the 523 licence-clean images and stored as
parquet.

Three restylings of COCO val2017 — oil, ukiyo-e and algorithmic corruption — from SDPose-OOD,
which built them with CycleGAN and StyTR² deliberately, *"to avoid introducing priors from
large-scale pretrained diffusion models"*. A benchmark restyled by a diffusion model would
have measured that model's idea of a person rather than the robustness under test.

## Evaluation only, twice over

**This data never enters a training corpus.** Two independent reasons, either sufficient:

1. It is derived from `val2017`, which is the blinded holdout. Anything derived from the
   holdout inherits its status. An image generated from a held-out photograph carries that
   photograph's content, so training on it trains on the holdout by a slower route.
2. It is generated rather than constructed, and the data rule evaluates on real or constructed
   data only. A model measured on its own generation distribution has not been measured.

The blinded rule is stricter than "unused for gradient steps". These images are not inspected
while developing, not used to pick a checkpoint, a hyperparameter, a threshold or a stopping
point, and not consulted to decide whether an approach is working.

## Why 523 and not 5,000

The upstream archives restyle all 5,000 val2017 images. This repository carries 523 of them.

`dataflow-coco-gemx` measured that only **523 of 5,000** val2017 person images are commercial
and derivatives safe. Every NC and ND image was dropped, and share-alike was dropped as
identifiable. A restyle is exactly the derivative an ND licence forbids, so redistributing the
full set would undo the filter `filter_coco_licenses.py` exists to apply.

All three sets carried all 523. Nothing was missing, and the shortfall was counted rather than
assumed.

## Shape

Essential Tuple Normal Form. Interned vocabulary, satellite relation for the payload, no
NULLs, no derivable columns.

| file | columns | rows | tracked |
| --- | --- | --- | --- |
| `styles.parquet` | `style_id` int8 PK, `name` string | 3 | yes |
| `renditions.parquet` | `style_id` int8 FK, `image_id` int32 FK, `jpeg` binary | 1,569 | release asset |

`image_id` is the COCO id, so a rendition joins straight to `dataflow-coco-gemx`'s
`images.parquet` and through it to `licenses.parquet`. The licence of any row is one join
away rather than an assumption.

Width, height and a payload hash are not stored. All three are derivable from `jpeg` or
already carried by `images.parquet`, and a derivable column can disagree with its source.

`renditions.parquet` is 120 MB, over GitHub's 100 MB file limit, so it is a release asset.
`fetch.sh` downloads it and checks the row count and schema.

```sh
./fetch.sh          # pulls renditions.parquet from the v1 release and validates it
```

## What was dropped on the way in

| | per archive |
| --- | --- |
| entries in the zip | 10,001 |
| `__MACOSX/` resource forks | 5,001 |
| images outside the 523 allowlist | ~4,477 |
| kept | 523 |

Roughly half of every upstream archive was macOS resource-fork junk carrying no image data.

The originals were zip, which the archive-format rule does not accept. Every kept payload was
hashed out of the zip and again out of the parquet before anything was removed, and the two
maps compared: 1,569 rows, zero mismatches.

## Licence

The tooling in this repository is licensed under either of

* Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE))
* MIT License ([LICENSE-MIT](LICENSE-MIT))

at your option. `SPDX-License-Identifier: Apache-2.0 OR MIT`

**The images are not ours and are not covered by that.** Each carries its original Flickr
licence, which is why only the 523 commercial-and-derivatives-safe ones are here. Join
`image_id` against `licenses.parquet` in `dataflow-coco-gemx` for the licence of any given
row. The restylings are SDPose-OOD's work.
