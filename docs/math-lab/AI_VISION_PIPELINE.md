# AI Vision pipeline design

AI Vision is not implemented in Phase 1. The required future boundary is:

```text
image/camera/text/sketch
        v
VisionProvider adapter in Master
        v
provider structured output
        v
MathSemanticModel.model_validate
        v
teacher correction
        v
rule engine + planner + verifier
        v
MathScene
```

Providers are configured adapters, never imported by renderers. Raw free-form
answers are not parsed with regex. Every inferred fact carries confidence and
provenance. Unknown or low-confidence geometry remains uncertain and cannot
become a locked constraint. No provider output contains executable frontend
code or arbitrary asset URLs.

Worker classroom vision remains separate from mathematical OCR/VLM analysis.
A later adapter may consume a captured frame, but authorization, provider
selection and validation stay in Master.
