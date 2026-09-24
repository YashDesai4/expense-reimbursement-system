from __future__ import annotations

import enum
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(str, enum.Enum):
    employee = "employee"
    manager = "manager"


class ExpenseStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.employee)
    expenses: Mapped[list["Expense"]] = relationship(back_populates="employee")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vendor: Mapped[str] = mapped_column(String(200))
    expense_date: Mapped[date] = mapped_column(Date)
    total: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    line_items_json: Mapped[str] = mapped_column(Text, default="[]")
    receipt_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[ExpenseStatus] = mapped_column(Enum(ExpenseStatus), default=ExpenseStatus.submitted, index=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    employee: Mapped[User] = relationship(back_populates="expenses")
