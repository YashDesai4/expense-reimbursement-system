from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ExpenseStatus, Role


class LoginRequest(BaseModel):
    email: str
    password: str


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    role: Role


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserView


class ExpenseCreate(BaseModel):
    vendor: str = Field(min_length=1, max_length=200)
    expense_date: date
    total: float = Field(gt=0, le=1_000_000)
    category: str | None = None
    description: str = Field(default="", max_length=2_000)


class ExpenseView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    vendor: str
    expense_date: date
    total: float
    category: str
    description: str
    status: ExpenseStatus
    receipt_name: str | None
    extraction_confidence: float | None
    reviewer_note: str | None
    created_at: datetime


class DecisionRequest(BaseModel):
    decision: str
    note: str = Field(default="", max_length=2_000)
