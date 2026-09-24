from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import current_user, manager_only
from app.core.security import create_token, verify_password
from app.database import get_db
from app.models import Expense, ExpenseStatus, Role, User
from app.schemas.api import DecisionRequest, ExpenseCreate, ExpenseView, LoginRequest, TokenResponse
from app.services.categorization import suggest_category
from app.services.receipt_extractor import DonutReceiptExtractor, serialize_items

router = APIRouter(prefix="/api")
extractor = DonutReceiptExtractor()


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, database: Session = Depends(get_db)):
    user = database.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_token(user.id, user.role.value), user=user)


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@router.post("/expenses", response_model=ExpenseView, status_code=201)
def create_expense(payload: ExpenseCreate, database: Session = Depends(get_db), user: User = Depends(current_user)):
    category = payload.category or suggest_category(payload.vendor, payload.description)
    expense = Expense(employee_id=user.id, category=category, status=ExpenseStatus.submitted, **payload.model_dump(exclude={"category"}))
    database.add(expense)
    database.commit()
    database.refresh(expense)
    return expense


@router.post("/expenses/from-receipt", response_model=ExpenseView, status_code=201)
async def create_from_receipt(
    receipt: UploadFile = File(),
    description: str = Form(default=""),
    database: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if receipt.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=415, detail="Receipt must be a JPEG or PNG image")
    if not extractor.configured:
        raise HTTPException(status_code=503, detail="Receipt model is not configured; set DONUT_MODEL_PATH")
    content = await receipt.read()
    if len(content) > 10_000_000:
        raise HTTPException(status_code=413, detail="Receipt exceeds 10 MB")
    parsed = extractor.extract(content)
    expense = Expense(
        employee_id=user.id,
        vendor=parsed.vendor or "Review required",
        expense_date=date.fromisoformat(parsed.expense_date),
        total=parsed.total,
        category=suggest_category(parsed.vendor, description),
        description=description,
        line_items_json=serialize_items(parsed.line_items),
        receipt_name=receipt.filename,
        extraction_confidence=parsed.confidence,
        status=ExpenseStatus.draft if parsed.total <= 0 else ExpenseStatus.submitted,
    )
    database.add(expense)
    database.commit()
    database.refresh(expense)
    return expense


@router.get("/expenses", response_model=list[ExpenseView])
def list_expenses(database: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Expense).order_by(Expense.created_at.desc())
    if user.role == Role.employee:
        query = query.where(Expense.employee_id == user.id)
    return list(database.scalars(query))


@router.patch("/expenses/{expense_id}/decision", response_model=ExpenseView)
def decide(expense_id: int, payload: DecisionRequest, database: Session = Depends(get_db), _manager: User = Depends(manager_only)):
    if payload.decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=422, detail="decision must be approved or rejected")
    expense = database.get(Expense, expense_id)
    if not expense or expense.status != ExpenseStatus.submitted:
        raise HTTPException(status_code=404, detail="Submitted expense not found")
    expense.status = ExpenseStatus(payload.decision)
    expense.reviewer_note = payload.note
    database.commit()
    database.refresh(expense)
    return expense


@router.get("/progress")
def progress(database: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Expense.status, func.count(Expense.id)).group_by(Expense.status)
    if user.role == Role.employee:
        query = query.where(Expense.employee_id == user.id)
    counts = {status.value: count for status, count in database.execute(query)}
    return {status.value: counts.get(status.value, 0) for status in ExpenseStatus}
