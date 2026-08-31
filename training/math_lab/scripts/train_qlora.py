#!/usr/bin/env python3
"""Memory-gated QLoRA entrypoint for the Math Scene image adapter.

Run ``--dry-run`` first. Imports that require the training environment and
model loading are intentionally delayed until after data and VRAM gates.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / "training/math_lab/data/generated"


def free_vram_mib() -> int:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
    )
    return min(int(line.strip()) for line in result.stdout.splitlines() if line.strip())


def image_rows(split: str) -> list[dict]:
    rows: list[dict] = []
    path = DATA_ROOT / f"math_scene_{split}.jsonl"
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if "image" not in record:
                continue
            human = record["conversations"][0]["value"]
            if not human.startswith("<image>"):
                raise ValueError(f"Image record lacks <image> marker: {record['id']}")
            image_path = DATA_ROOT / record["image"]
            if not image_path.is_file():
                raise FileNotFoundError(image_path)
            rows.append({
                "id": record["id"],
                "image_path": str(image_path),
                "user_text": human.removeprefix("<image>").strip(),
                "assistant_text": record["conversations"][1]["value"],
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen3-VL-8B-Instruct")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "training/math_lab/checkpoints/qwen3vl-8b-math-scene")
    parser.add_argument("--min-free-vram-mib", type=int, default=12_000)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--train-samples", type=int, default=None)
    parser.add_argument("--eval-samples", type=int, default=None)
    parser.add_argument("--family", default=None)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=16)
    parser.add_argument("--save-steps", type=int, default=100)
    parser.add_argument("--eval-steps", type=int, default=100)
    parser.add_argument("--resume-from-checkpoint", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    train_rows = image_rows("train")
    validation_rows = image_rows("validation")
    if args.family:
        def matches_family(row: dict) -> bool:
            target = json.loads(row["assistant_text"])
            return target["questions"][0]["problem_type"] == args.family

        train_rows = [row for row in train_rows if matches_family(row)]
        validation_rows = [row for row in validation_rows if matches_family(row)]
    if args.train_samples is not None:
        train_rows = train_rows[:args.train_samples]
    if args.eval_samples is not None:
        validation_rows = validation_rows[:args.eval_samples]
    available = free_vram_mib()
    summary = {
        "train_image_records": len(train_rows),
        "validation_image_records": len(validation_rows),
        "free_vram_mib": available,
        "required_free_vram_mib": args.min_free_vram_mib,
        "model": args.model,
    }
    print(json.dumps(summary, indent=2))
    if args.dry_run:
        return
    if available < args.min_free_vram_mib:
        raise SystemExit(
            f"Training refused: {available} MiB VRAM free; require at least "
            f"{args.min_free_vram_mib} MiB without terminating other users' processes."
        )

    import torch
    from datasets import Dataset, Image as DatasetImage
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    def to_dataset(rows: list[dict]) -> Dataset:
        dataset = Dataset.from_list([{
            "image": row["image_path"],
            "prompt": [
                {"role": "user", "content": [
                    {"type": "image"},
                    {"type": "text", "text": row["user_text"]},
                ]},
            ],
            "completion": [
                {"role": "assistant", "content": [
                    {"type": "text", "text": row["assistant_text"]},
                ]},
            ],
        } for row in rows])
        return dataset.cast_column("image", DatasetImage())

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForImageTextToText.from_pretrained(
        args.model,
        quantization_config=quantization,
        dtype=torch.bfloat16,
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(
        args.model,
        min_pixels=64 * 28 * 28,
        max_pixels=512 * 28 * 28,
    )
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(model, LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    ))
    for name, parameter in model.named_parameters():
        if ("visual" in name or "vision" in name) and parameter.requires_grad:
            parameter.requires_grad = False
    model.config.use_cache = False

    training_args = SFTConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        bf16=True,
        gradient_checkpointing=True,
        assistant_only_loss=False,
        completion_only_loss=True,
        max_length=None,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        save_total_limit=2,
        logging_steps=10,
        report_to="none",
        max_steps=args.max_steps,
    )
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=to_dataset(train_rows),
        eval_dataset=to_dataset(validation_rows),
        processing_class=processor,
    )
    train_result = trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)
    trainer.save_model(str(args.output_dir))
    processor.save_pretrained(str(args.output_dir))
    metrics = dict(train_result.metrics)
    if validation_rows:
        metrics.update({f"final_{key}": value for key, value in trainer.evaluate().items()})
    trainer.save_metrics("all", metrics)


if __name__ == "__main__":
    main()
