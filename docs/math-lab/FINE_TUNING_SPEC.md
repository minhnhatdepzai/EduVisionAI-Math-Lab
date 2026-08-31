# Math Lab semantic-to-visual fine-tuning specification

## What is fine-tuned

Fine-tune Qwen3-VL to perform perception and semantic extraction only:

`text/image -> strict ProviderDocument JSON -> deterministic decision engine -> pedagogy steps -> renderer`

The model must not generate SVG, coordinates, JavaScript or a hidden answer. This keeps arithmetic, units and scene state testable and prevents a fluent model from drawing a mathematically false picture.

## What the learner sees

| Problem family | Required visual progression |
|---|---|
| Fraction addition/subtraction | Two original bars, equal partition to the LCM, equivalent numerators, combine/remove colored pieces, then reduce |
| Fraction multiplication | Horizontal shading for the first factor, vertical shading for the second, intersection grid for the product |
| Multiplication/division | Concrete objects, equal groups, rectangular array, symbolic equation |
| Ratio from a known value | Known parts, value of one part, target parts, resulting quantity |
| Linear equation | Physical balance, same inverse operation on both pans, equal division into x blocks, substitution check |
| Linear function | x-y axes with equal scale, point table, intercept, one-run/m-rise slope step, connected line |
| 2D geometry | Given dimensions and constraints on the same shape, decomposition/rearrangement, area/perimeter conclusion |
| Cuboid volume | Base on the x-y plane, base area, height on z, repeated layers, volume |
| Binomial square | Square of side a+b, split both sides, areas a²/ab/ab/b², combine like terms |
| Motion/time | One shared progress state drives path, timeline and clock so the views cannot drift |

## Data curriculum

1. **Target SFT:** deterministic Vietnamese grade 1-9 templates rendered as both text and problem images; every target passes the runtime Pydantic schema.
2. **Human correction:** add only teacher-reviewed real failures from the review UI, after redaction and license/consent checks.
3. **OCR auxiliary:** train 25K Equation separately if formula perception is weak; do not mix its raw LaTeX target into the semantic adapter.
4. **External reasoning data:** use AIMO3 only as a reviewed structural seed. The 2026 VLM curriculum remains an eval candidate until upstream image licenses are audited.
5. **Untouched holdout:** We-Math, MathVista and MathNet never enter training.

## Acceptance gates

- JSON/schema validity: 100%.
- Unknown/result leakage: 0%.
- Exact operand, unit and semantic-role accuracy: at least 99%.
- Correct deterministic renderer decision: at least 98% overall and at least 95% per family.
- Scene invariants: 100% (same denominator parts, same operation on both equation sides, paired x/y points, x-y-z dimensions).
- Visual E2E: all 14 target families render and every reveal step changes the visible mathematical state.
- Regression holdout: prompt-only baseline versus adapter, with no score loss on existing motion/time/ratio flows.

## Current training constraint

The host has a 16 GB RTX 5060 Ti, but it is shared and had less than 1 GB free during preparation. The 8B LoRA run must wait for the memory gate instead of terminating other users' processes or destabilizing the live Ollama-backed Math Lab.
