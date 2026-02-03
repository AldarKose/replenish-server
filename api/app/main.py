import os
from datetime import date
from typing import Optional, Dict, Any, List

import psycopg2
from fastapi import FastAPI, Header, HTTPException

DATABASE_URL = os.environ["DATABASE_URL"]
API_KEY = os.environ["API_KEY"]

app = FastAPI(title="Replenish API")

def _conn():
    return psycopg2.connect(DATABASE_URL)

def _auth(x_api_key: Optional[str]):
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    with _conn() as c:
        with c.cursor() as cur:
            cur.execute("select 1;")
    return {"ok": True}

@app.get("/replenishment")
def get_replenishment(
    store_id: str,
    calc_date: Optional[date] = None,
    x_api_key: Optional[str] = Header(default=None),
):
    _auth(x_api_key)

    with _conn() as c:
        with c.cursor() as cur:
            if calc_date is None:
                cur.execute(
                    "select max(calc_date) from replenishment where store_id=%s",
                    (store_id,),
                )
                row = cur.fetchone()
                calc_date = row[0]
                if calc_date is None:
                    return []

            cur.execute(
                """
                select sku, forecast_sum, safety_stock, recommended_order, reason_json
                from replenishment
                where store_id=%s and calc_date=%s
                order by recommended_order desc
                limit 5000
                """,
                (store_id, calc_date),
            )

            res: List[Dict[str, Any]] = []
            for sku, forecast_sum, safety_stock, recommended_order, reason_json in cur.fetchall():
                res.append({
                    "sku": sku,
                    "forecast_sum": float(forecast_sum),
                    "safety_stock": float(safety_stock),
                    "recommended_order": float(recommended_order),
                    "reason": reason_json,
                    "calc_date": str(calc_date),
                })
            return res

