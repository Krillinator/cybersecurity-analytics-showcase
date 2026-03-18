from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="NordPay Demo", version="1.0.0")


# Fake data / demo database
partners = {
    "alpha": {
        "password": "alpha123",
        "partner_id": "partner_alpha"
    },
    "beta": {
        "password": "beta123",
        "partner_id": "partner_beta"
    }
}

tokens = {
    "token-alpha": {
        "partner_id": "partner_alpha",
        "username": "alpha"
    },
    "token-beta": {
        "partner_id": "partner_beta",
        "username": "beta"
    }
}

transactions = {
    "tx_1001": {
        "partner_id": "partner_alpha",
        "customer_id": "cust_001",
        "amount": 500,
        "status": "paid"
    },
    "tx_1002": {
        "partner_id": "partner_alpha",
        "customer_id": "cust_002",
        "amount": 1200,
        "status": "paid"
    },
    "tx_2001": {
        "partner_id": "partner_beta",
        "customer_id": "cust_010",
        "amount": 800,
        "status": "paid"
    },
    "tx_2002": {
        "partner_id": "partner_beta",
        "customer_id": "cust_011",
        "amount": 1500,
        "status": "paid"
    }
}

refund_log = []


# Models
class LoginRequest(BaseModel):
    username: str
    password: str


class RefundRequest(BaseModel):
    transaction_id: str
    amount: int


# Helper
def get_current_partner(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    token = authorization.replace("Bearer ", "").strip()

    current_partner = tokens.get(token)
    if not current_partner:
        raise HTTPException(status_code=401, detail="Invalid token")

    return current_partner


# Routes
@app.get("/")
def root():
    return {
        "message": "NordPay demo API is running",
        "commands": {
            "login": "/login first",
            "personal-transactions": "/transactions list all personal transactions",
            "refund": "/refund - start a refund process",
            },
    }


@app.get("/debug/data")
def debug_data():
    return {
        "info": "DEBUG ONLY - Exposes internal demo data for learning purposes",
        "partners": partners,
        "tokens": tokens,
        "transactions": transactions
    }


@app.post("/login")
def login(data: LoginRequest):
    partner = partners.get(data.username)

    if not partner or partner["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if data.username == "alpha":
        token = "token-alpha"
    else:
        token = "token-beta"

    return {
        "access_token": token,
        "token_type": "bearer",
        "partner_id": partner["partner_id"]
    }


@app.get("/transactions")
def list_transactions(authorization: Optional[str] = Header(default=None)):
    current_partner = get_current_partner(authorization)

    visible_transactions = {
        tx_id: tx_data
        for tx_id, tx_data in transactions.items()
        if tx_data["partner_id"] == current_partner["partner_id"]
    }

    return {
        "logged_in_as": current_partner["partner_id"],
        "transactions": visible_transactions
    }


@app.get("/transactions/all")
def list_all_transactions_for_demo():
    return transactions


@app.post("/refund")
def refund_vulnerable(
    data: RefundRequest,
    authorization: Optional[str] = Header(default=None)
):
    current_partner = get_current_partner(authorization)

    transaction = transactions.get(data.transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if transaction["status"] != "paid":
        raise HTTPException(status_code=400, detail="Transaction is not refundable")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Refund amount must be greater than 0")

    if data.amount > transaction["amount"]:
        raise HTTPException(status_code=400, detail="Refund amount exceeds original payment")


    refund_log.append({
        "mode": "vulnerable",
        "requested_by_partner": current_partner["partner_id"],
        "transaction_id": data.transaction_id,
        "transaction_owner_partner": transaction["partner_id"],
        "amount": data.amount,
        "result": "approved"
    })

    return {
        "status": "approved",
        "mode": "vulnerable",
        "message": "Refund processed automatically",
        "requested_by_partner": current_partner["partner_id"],
        "transaction_id": data.transaction_id,
        "transaction_owner_partner": transaction["partner_id"],
        "amount": data.amount
    }



@app.get("/refund-log")
def get_refund_log():
    return {
        "count": len(refund_log),
        "entries": refund_log
    }