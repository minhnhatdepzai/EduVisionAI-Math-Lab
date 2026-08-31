# Math Lab fine-tuning workspace

The target of fine-tuning is the semantic analyzer, not renderer code. The model emits a strict `ProviderDocument`; the existing decision engine, pedagogy planner and deterministic renderers then create the visible simulation.

## Build the target dataset

```bash
python training/math_lab/scripts/prepare_sft.py
python training/math_lab/scripts/audit_sft.py
```

The generator creates schema-validated text and image pairs for 71 scene families, including arithmetic, fraction transformations, two-item discount systems, solution sets, trigonometric geometry, coordinate graphs, curved Oxyz surfaces, data charts, probability and solid geometry. Its default 5,680/852/852 semantic-case splits produce 11,360/1,704/1,704 text-plus-image records with deterministic stem diversity and no split leakage. Generated images, JSONL files, checkpoints and raw internet datasets are ignored by Git. `sources.lock.json` records immutable revisions, checksums, licenses and whether each source is allowed for training, seed-only reference or evaluation only.

The generated family list is not the same as full grade 1-9 exam coverage. Validate the separate exam-derived catalog before making a product claim:

```bash
python training/math_lab/scripts/audit_exam_coverage.py
```

The catalog at `catalogs/grade_1_9_exam_families.json` records exact, partial and missing renderer support. A fallback renderer is never counted as exact support.

## Training gate

Use `configs/qwen3vl_qlora.json`. The data contract is pinned to the official `QwenLM/Qwen3-VL` framework; the memory-efficient training entrypoint is pinned to current TRL/PEFT revisions in `sources.lock.json`.

1. Validate every assistant target with `ProviderDocument`.
2. Keep We-Math, MathVista, MathNet and the VLM curriculum holdout out of training.
3. Run a one-batch GPU memory probe; do not launch the 8B adapter on the shared host unless at least 12 GB VRAM is free.
4. Freeze the vision tower for the first semantic adapter. Treat 25K Equation as a separate OCR adapter candidate, never as Math Scene ground truth.
5. Use prompt-completion VLM records with completion-only loss. Current TRL intentionally rejects assistant-only loss for vision datasets.
6. Accept an adapter only when schema validity is 100%, unknown-answer leakage is 0%, semantic role accuracy is at least 99%, renderer selection is at least 98%, and all scene invariant/runtime tests pass.

Readiness check (does not install packages or load model weights):

```bash
python training/math_lab/scripts/train_qlora.py --dry-run
```

When the VRAM gate passes, create an isolated training environment from `requirements-qlora.txt`, rerun the audit, and launch the same command without `--dry-run`.

The exact production-oriented instruction is in `prompts/math_scene_analyzer_system.txt`.
