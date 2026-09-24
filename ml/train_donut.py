"""Fine-tune DONUT on a receipt dataset manifest.

Manifest format (JSONL): {"image": "receipts/001.png", "target": {"vendor": "...", ...}}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import Dataset
from PIL import Image
from transformers import DonutProcessor, Seq2SeqTrainer, Seq2SeqTrainingArguments, VisionEncoderDecoderModel


def load_manifest(path: Path) -> Dataset:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        value["image"] = str((path.parent / value["image"]).resolve())
        rows.append(value)
    if not rows:
        raise ValueError("manifest is empty")
    return Dataset.from_list(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base-model", default="naver-clova-ix/donut-base")
    parser.add_argument("--output", type=Path, default=Path("models/receipt-donut"))
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()

    processor = DonutProcessor.from_pretrained(args.base_model)
    model = VisionEncoderDecoderModel.from_pretrained(args.base_model)
    task_start, task_end = "<s_receipt>", "</s_receipt>"
    processor.tokenizer.add_special_tokens({"additional_special_tokens": [task_start, task_end]})
    model.decoder.resize_token_embeddings(len(processor.tokenizer))
    model.config.decoder_start_token_id = processor.tokenizer.convert_tokens_to_ids(task_start)
    model.config.pad_token_id = processor.tokenizer.pad_token_id

    dataset = load_manifest(args.manifest)

    def prepare(example):
        image = Image.open(example["image"]).convert("RGB")
        target = task_start + json.dumps(example["target"], separators=(",", ":")) + task_end
        pixels = processor(image, return_tensors="pt").pixel_values.squeeze(0)
        labels = processor.tokenizer(target, max_length=512, padding="max_length", truncation=True, return_tensors="pt").input_ids.squeeze(0)
        labels[labels == processor.tokenizer.pad_token_id] = -100
        return {"pixel_values": pixels, "labels": labels}

    prepared = dataset.map(prepare, remove_columns=dataset.column_names)
    prepared.set_format("torch")
    training = Seq2SeqTrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=3e-5,
        save_strategy="epoch",
        logging_steps=10,
        report_to="none",
    )
    trainer = Seq2SeqTrainer(model=model, args=training, train_dataset=prepared)
    trainer.train()
    trainer.save_model(args.output)
    processor.save_pretrained(args.output)


if __name__ == "__main__":
    main()
