from fastapi import FastAPI

app = FastAPI(title="BudgetPilot API")


@app.get("/")
def root():
    return {"message": "BudgetPilot API is running"}
