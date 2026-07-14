import psycopg2
from psycopg2.extras import execute_values
import os

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    port=os.getenv("POSTGRES_PORT", 5432)
)

def _load_by_industry_geo(conn, rows):
    if not rows:
        return
    snapshot_date = rows[0]["snapshot_date"]
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM analytics.agg_jobs_by_industry_geo WHERE snapshot_date = %s",
            (snapshot_date,),
        )
        sql = """
            INSERT INTO analytics.agg_jobs_by_industry_geo
                (industry_name, country, job_count, avg_salary_min, avg_salary_max, snapshot_date)
            VALUES %s
        """
        values = [(
            r["industry_name"], r["country"], r["job_count"],
            r["avg_salary_min"], r["avg_salary_max"], r["snapshot_date"],
        ) for r in rows]
        execute_values(cur, sql, values)

def _load_by_company(conn, rows):
    if not rows:
        return
    snapshot_date = rows[0]["snapshot_date"]
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM analytics.agg_jobs_by_company WHERE snapshot_date = %s",
            (snapshot_date,),
        )
        sql = """
            INSERT INTO analytics.agg_jobs_by_company (company_name, total_jobs, avg_salary_avg, snapshot_date)
            VALUES %s
        """
        values = [(r["company_name"], r["total_jobs"], r["avg_salary_avg"], r["snapshot_date"]) for r in rows]
        execute_values(cur, sql, values)


def _load_daily(conn, rows):
    if not rows:
        return
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE analytics.agg_jobs_daily")
        sql = "INSERT INTO analytics.agg_jobs_daily (full_date, job_count, avg_salary) VALUES %s"
        values = [(r["full_date"], r["job_count"], r["avg_salary"]) for r in rows]
        execute_values(cur, sql, values)


def run_analytics_load(payload, conn=None):
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        _load_by_industry_geo(conn, payload["by_industry_geo"])
        _load_by_company(conn, payload["by_company"])
        _load_daily(conn, payload["daily"])
        conn.commit()
        print(f"[analytics] refreshed {len(payload['daily'])} daily rows")
    except Exception:
        conn.rollback()
        raise
    finally:
        if own_conn:
            conn.close()