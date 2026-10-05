# datasource-coco-ood-eval

Stylized restylings of the licence-clean COCO `val2017` person images, stored as parquet, for evaluating pose robustness and nothing else.

## What it is for

The restylings come from the SDPose-OOD benchmark, which made them with style-transfer networks rather than a diffusion model, and this repository keeps only the images whose licences allow commercial use and derivatives. The set is evaluation-only twice over: it derives from the blinded `val2017` holdout, and it is generated rather than constructed. It never enters a training corpus and is not consulted while developing; RFD 1141 states the rule.

The data is in Essential Tuple Normal Form. `styles.parquet` is tracked, and the renditions are a release asset that `fetch.sh` downloads and validates. `build_parquet.py` rebuilds the release from the upstream archives, which `fetch_upstream.sh` fetches given their upstream file ids; those ids are not recorded here.

## Run

```sh
./fetch.sh
```

## Licence

The tooling is Apache-2.0 OR MIT; see `LICENSE-APACHE` and `LICENSE-MIT`. The images are not covered by that: each keeps its photographer's original licence, which `image_id` joins to through `licenses.parquet` in `datasource-dataflow-coco-gemx`. The restylings are the SDPose-OOD authors' work.
