# Expense Reimbursement System

A full-stack expense submission and approval application built with FastAPI, SQLAlchemy, PostgreSQL, React, JWT authentication, and an optional fine-tuned DONUT receipt model.

## Resume feature mapping

- **Submission and approvals:** employees submit expenses; managers view the shared queue and approve or reject requests.
- **Progress tracking:** status counts expose draft, submitted, approved, and rejected work.
- **Receipt understanding:** a lazy DONUT inference adapter extracts vendor, date, total, and line items from receipt images.
- **Fine-tuning:** `ml/train_donut.py` trains the base DONUT model on a JSONL receipt manifest and saves deployable processor/model artifacts.
- **Smart categories:** deterministic vendor and description rules assign travel, meals, software, office, or training categories.
- **Security:** PBKDF2 password hashing, expiring JWTs, employee/manager authorization, upload limits, and content-type validation.

Model weights and private receipt datasets are intentionally excluded. Train the model, then set `DONUT_MODEL_PATH` to the saved directory.

## Run the web application

```bash
docker compose up --build
```

Open <http://localhost:5173>. Demo accounts:

- `employee@example.com` / `employee123`
- `manager@example.com` / `manager123`

Change all demo credentials and secrets before deployment.

## Train the receipt model

```bash
cd backend
pip install -e ".[ml]"
python ../ml/train_donut.py ../private-receipts/manifest.jsonl --output ../models/receipt-donut
```

## Test

```bash
cd backend
pip install -e ".[dev]"
pytest -q
ruff check .
```

The resume's productivity percentages require comparison against the original manual workflow. This repository implements the complete measurable workflow without treating those percentages as synthetic benchmark output.

## Author

Yash Bhausaheb Desai
