from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="NordPay Demo", version="1.0.0")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_DAYS = int(os.getenv("JWT_EXPIRES_DAYS", 30))

partners = {
    "alpha": {
        "password": os.getenv("ALPHA_PASSWORD"),
        "partner_id": "partner_alpha"
    },
    "beta": {
        "password": os.getenv("BETA_PASSWORD"),
        "partner_id": "partner_beta"
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


class LoginRequest(BaseModel):
    username: str
    password: str


class RefundRequest(BaseModel):
    transaction_id: str
    amount: int


def create_access_token(username: str, partner_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "partner_id": partner_id,
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRES_DAYS),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def get_current_partner(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    token = authorization.replace("Bearer ", "").strip()

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    partner_id = payload.get("partner_id")

    if not username or not partner_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {
        "username": username,
        "partner_id": partner_id
    }


@app.get("/")
def root():
    return {
        "message": "NordPay demo API is running",
        "commands": {
            "login": "/login first",
            "personal-transactions": "/transactions list your transactions",
            "refund": "/refund - start a refund process",
            "refund-log": "/refund-log - list your refund requests",
        },
    }


@app.get("/debug/data")
def debug_data():
    return {
        "info": "DEBUG ONLY - Exposes internal demo data for learning purposes",
        "transactions": transactions # Although seemingly normal - a huge risk waiting
    }


@app.post("/login")
def login(data: LoginRequest):
    partner = partners.get(data.username)

    if not partner or partner["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(
        username=data.username,
        partner_id=partner["partner_id"]
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_days": JWT_EXPIRES_DAYS,
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


@app.post("/refund")
def refund_request(
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

    # Intentionally vulnerable:
    # authenticated partner is known, but ownership of the transaction is NOT verified
    refund_log.append({
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
def get_refund_log(authorization: Optional[str] = Header(default=None)):
    current_partner = get_current_partner(authorization)

    visible_logs = [
        entry for entry in refund_log
        if entry["requested_by_partner"] == current_partner["partner_id"]
    ]

    return {
        "logged_in_as": current_partner["partner_id"],
        "count": len(visible_logs),
        "entries": visible_logs
    }