from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.routes import router
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Role, User


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as database:
        if database.scalar(select(User.id).limit(1)) is None:
            database.add_all([
                User(email="employee@example.com", name="Demo Employee", password_hash=hash_password("employee123"), role=Role.employee),
                User(email="manager@example.com", name="Demo Manager", password_hash=hash_password("manager123"), role=Role.manager),
            ])
            database.commit()
    yield


app = FastAPI(title="Expense Reimbursement System", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
