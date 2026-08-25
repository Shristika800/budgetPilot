from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.transactions import router as transaction_router
from app.api.budgets import router as budget_router
from app.db.database import Base, engine
from app.models.transaction import Transaction  # noqa: F401
from app.models.budget import Budget            # noqa: F401


Base.metadata.create_all(bind=engine)

app = FastAPI(title="BudgetPilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transaction_router)
app.include_router(chat_router)
app.include_router(budget_router)


@app.get("/")
def root():
    return {"message": "BudgetPilot API is running"}
