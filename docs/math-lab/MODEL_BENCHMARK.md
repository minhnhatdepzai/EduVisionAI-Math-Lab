# Model benchmark ledger

| Candidate | Task | Result | Decision |
|---|---|---|---|
| `qwen3-vl:8b-instruct` | production OCR + semantic JSON | structured output is stable; typical local text smoke is about 7–10 seconds with full GPU load | current production model |
| `qwen3-vl:8b-thinking` | full production schema | did not complete within the recorded 180-second benchmark window | rejected for live demo latency |
| `Qwen/Qwen3-VL-4B-Instruct` smoke QLoRA | one train image + one validation image | train loss 0.247867, eval loss 0.241940, token accuracy 0.959119 | pipeline smoke only; not production |
| target 8B QLoRA | full reviewed dataset | blocked by the 12 GB free-VRAM gate during the recorded run | not trained yet |

The production comparison is not a complete model league: it does not yet
include per-grade/per-family accuracy, OCR corruption bands, p50/p95 latency,
VisualPlan faithfulness or pedagogical quality for every candidate. The base
8B remains preferred until an adapter beats it on a clean holdout and passes
all runtime tests. Official framework revisions are pinned in
`training/math_lab/sources.lock.json`; model weights and checkpoints are local.

GitHub HEAD was rechecked on 27/08/2026: Qwen3-VL still matches the tested pin
`9658872`. TRL and PEFT have newer development commits, but the changes are a
development-version bump and an FSDP2 fix; the Math Lab single-GPU QLoRA path
keeps its smoke-tested pins until the newer revisions pass the same pipeline.
