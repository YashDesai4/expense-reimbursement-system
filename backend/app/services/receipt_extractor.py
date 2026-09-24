from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass, field
from datetime import date


@dataclass
class ReceiptData:
    vendor: str = ""
    expense_date: str = field(default_factory=lambda: date.today().isoformat())
    total: float = 0.0
    line_items: list[dict[str, object]] = field(default_factory=list)
    confidence: float = 0.0


class DonutReceiptExtractor:
    """Lazy DONUT inference adapter; model weights stay outside source control."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path or os.getenv("DONUT_MODEL_PATH")
        self._processor = None
        self._model = None

    @property
    def configured(self) -> bool:
        return bool(self.model_path)

    def _load(self) -> None:
        if self._model is not None:
            return
        if not self.model_path:
            raise RuntimeError("DONUT_MODEL_PATH is not configured")
        from transformers import DonutProcessor, VisionEncoderDecoderModel

        self._processor = DonutProcessor.from_pretrained(self.model_path)
        self._model = VisionEncoderDecoderModel.from_pretrained(self.model_path)
        self._model.eval()

    def extract(self, image_bytes: bytes) -> ReceiptData:
        self._load()
        from PIL import Image
        import torch

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pixels = self._processor(image, return_tensors="pt").pixel_values
        prompt = "<s_receipt>"
        decoder = self._processor.tokenizer(prompt, add_special_tokens=False, return_tensors="pt").input_ids
        with torch.inference_mode():
            output = self._model.generate(
                pixels,
                decoder_input_ids=decoder,
                max_length=512,
                early_stopping=True,
                pad_token_id=self._processor.tokenizer.pad_token_id,
                eos_token_id=self._processor.tokenizer.eos_token_id,
                use_cache=True,
            )
        sequence = self._processor.batch_decode(output, skip_special_tokens=True)[0]
        parsed = self._processor.token2json(sequence)
        return ReceiptData(
            vendor=str(parsed.get("vendor", "")),
            expense_date=str(parsed.get("date", date.today().isoformat())),
            total=float(str(parsed.get("total", 0)).replace("$", "").replace(",", "")),
            line_items=parsed.get("line_items", []),
            confidence=0.9,
        )


def serialize_items(items: list[dict[str, object]]) -> str:
    return json.dumps(items, separators=(",", ":"))
