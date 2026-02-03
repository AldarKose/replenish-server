import os
import math
from datetime import date, timedelta
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

HORIZON_DAYS = 7
SAFETY_DAYS = 2

def main():
    today = date.today()
    calc_date = today

    with psycopg2.connect(DATABASE_URL) as c:
        with c.cursor() as cur:
            cur.execute("select distinct store_id from sales_daily where date >= %s",
                        (today - timedelta(days=60),))
            stores = [r[0] for r in cur.fetchall()]
            if not stores:
                return

            for store_id in stores:
                # последний снимок остатков
                cur.execute("""
                    select sku, on_hand
                    from stock_daily
                    where store_id=%s
                    order by date desc
                """, (store_id,))
                stock_map = {}
                for sku, on_hand in cur.fetchall():
                    stock_map.setdefault(sku, float(on_hand))

                # активные SKU
                cur.execute("""
                    select distinct sku
                    from sales_daily
                    where store_id=%s and date >= %s
                """, (store_id, today - timedelta(days=60)))
                skus = [r[0] for r in cur.fetchall()]
                if not skus:
                    continue

                for sku in skus:
                    cur.execute("""
                      select min_pack, pack_multiple, lead_time_days
                      from sku_params
                      where sku=%s
                    """, (sku,))
                    row = cur.fetchone()
                    if row:
                        min_pack = float(row[0])
                        pack_multiple = float(row[1])
                        lead_time_days = int(row[2])
                    else:
                        min_pack, pack_multiple, lead_time_days = 0.0, 1.0, 3

                    period = lead_time_days + HORIZON_DAYS

                    cur.execute("""
                        select coalesce(sum(qty),0)
                        from sales_daily
                        where store_id=%s and sku=%s and date >= %s
                    """, (store_id, sku, today - timedelta(days=14)))
                    sum14 = float(cur.fetchone()[0])
                    avg_day = sum14 / 14.0

                    forecast_sum = avg_day * period
                    safety_stock = avg_day * SAFETY_DAYS
                    on_hand = float(stock_map.get(sku, 0.0))

                    need = forecast_sum + safety_stock - on_hand
                    if need < 0:
                        need = 0.0

                    if pack_multiple <= 0:
                        pack_multiple = 1.0
                    recommended = math.ceil(need / pack_multiple) * pack_multiple
                    if 0 < recommended < min_pack:
                        recommended = min_pack

                    reasons = []
                    if on_hand < avg_day * lead_time_days:
                        reasons.append("low_stock")
                    if avg_day > 0:
                        reasons.append("avg14d_based")
                    reasons.append(f"lead_time_{lead_time_days}d")

                    cur.execute("""
                        insert into replenishment(calc_date, store_id, sku, forecast_sum, safety_stock, recommended_order, reason_json)
                        values (%s,%s,%s,%s,%s,%s,%s::jsonb)
                        on conflict (calc_date, store_id, sku)
                        do update set
                          forecast_sum=excluded.forecast_sum,
                          safety_stock=excluded.safety_stock,
                          recommended_order=excluded.recommended_order,
                          reason_json=excluded.reason_json
                    """, (calc_date, store_id, sku, forecast_sum, safety_stock, recommended, str(reasons).replace("'", '"')))

if __name__ == "__main__":
    main()

