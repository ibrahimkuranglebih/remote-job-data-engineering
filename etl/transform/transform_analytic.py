from datetime import date, datetime, timezone

import psycopg2

def _fetch_all(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def build_analytics_payload(conn=None, snapshot_date=None):
    own_conn = conn is None
    conn = conn or get_connection()
    snapshot_date = snapshot_date or date.today()

    try:
        by_industry_geo = _fetch_all(conn, """
            SELECT
                di.industry_name,
                dl.country,
                COUNT(DISTINCT f.job_key)      AS job_count,
                AVG(f.salary_min)              AS avg_salary_min,
                AVG(f.salary_max)              AS avg_salary_max
            FROM mart.fact_remote_jobs f
            JOIN mart.bridge_job_industry bji ON bji.job_key = f.job_key
            JOIN mart.dim_industry di ON di.industry_key = bji.industry_key
            LEFT JOIN mart.dim_location dl ON dl.location_key = f.location_key
            GROUP BY di.industry_name, dl.country
        """)

        by_company = _fetch_all(conn, """
            SELECT
                c.company_name,
                COUNT(DISTINCT f.job_key) AS total_jobs,
                AVG(f.salary_avg)         AS avg_salary_avg
            FROM mart.fact_remote_jobs f
            JOIN mart.dim_company c ON c.company_key = f.company_key
            GROUP BY c.company_name
        """)

        daily = _fetch_all(conn, """
            SELECT
                d.full_date,
                COUNT(DISTINCT f.job_key) AS job_count,
                AVG(f.salary_avg)         AS avg_salary
            FROM mart.fact_remote_jobs f
            JOIN mart.dim_date d ON d.date_key = f.date_key
            GROUP BY d.full_date
        """)

        for row in by_industry_geo:
            row["snapshot_date"] = snapshot_date
        for row in by_company:
            row["snapshot_date"] = snapshot_date

        return {
            "by_industry_geo": by_industry_geo,
            "by_company": by_company,
            "daily": daily,
        }
    finally:
        if own_conn:
            conn.close()