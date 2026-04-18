from datetime import datetime, timedelta, timezone
from decimal import Decimal
from .db import connect


def cleanup_expired():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM sent_alerts WHERE expires_at < NOW()")


def was_sent(alert_key):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM sent_alerts WHERE alert_key = %s AND expires_at > NOW()",
            (alert_key,),
        )
        return cur.fetchone() is not None


def mark_sent(alert_key, price, ttl_hours=20):
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sent_alerts (alert_key, price, expires_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (alert_key) DO UPDATE SET
                price = EXCLUDED.price,
                sent_at = NOW(),
                expires_at = EXCLUDED.expires_at
            """,
            (alert_key, Decimal(str(price)), expires_at),
        )
