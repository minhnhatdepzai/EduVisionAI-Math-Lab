# Data governance

`training/math_lab/sources/source_manifest.jsonl` is the authoritative source
ledger. Every record carries URL, domain, grade, exam type, school, year,
retrieval time, content hash, robots result, license status and allowed usage.

Allowed policies:

- `TRAIN_ALLOWED`: explicit license and approved training use.
- `EVAL_ALLOWED`: evaluation only; never optimization.
- `TAXONOMY_ONLY`: discover/paraphrase family and format, never copy question,
  answer, solution or media into training.
- `METADATA_ONLY`: retain provenance/link only; do not fetch the artifact.
- `UNKNOWN` or `FORBIDDEN`: blocked.

The current web manifest has ten records covering grades 1–9 as provenance:
six are `TAXONOMY_ONLY`, four are `METADATA_ONLY`, and zero are training
records. Pages whose license is unknown therefore contribute no SFT text.
`extract_questions.py` rejects taxonomy-only and metadata-only inputs.

`training/math_lab/dataset_version.json` content-addresses the generated
manifest, source manifest, family catalog, semantic prompt and generator. Its
contamination scan currently reports zero duplicate stems across train,
validation and test. Raw downloads, credentials, generated media and
checkpoints remain Git-ignored.

Before publishing a new dataset version:

1. recheck robots and license;
2. hash the exact artifact;
3. run `audit_sft.py` and `build_dataset_version.py`;
4. keep external benchmarks and teacher failure holdouts out of training;
5. publish aggregate metrics, not personal or copyrighted source content.
