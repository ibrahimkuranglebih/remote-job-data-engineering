from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import os

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432)
    )

def _date_key(d):
    return int(d.strftime("%Y%m%d"))


def _upsert_dim_company(conn, companies):
    lookup = {}
    if not companies:
        return lookup
    sql = """
        INSERT INTO mart.dim_company (company_name, company_logo)
        VALUES %s
        ON CONFLICT (company_name) DO UPDATE SET company_logo = EXCLUDED.company_logo
        RETURNING company_key, company_name
    """
    values = [(c["company_name"], c["company_logo"]) for c in companies]
    with conn.cursor() as cur:
        rows = execute_values(cur, sql, values, fetch=True)  # <-- ambil return value
        for row in rows:
            lookup[row[1]] = row[0]
    return lookup


def _upsert_dim_location(conn, locations):
    lookup = {}
    if not locations:
        return lookup
    sql = """
        INSERT INTO mart.dim_location (country, region)
        VALUES %s
        ON CONFLICT (country, region) DO UPDATE SET country = EXCLUDED.country
        RETURNING location_key, country, region
    """
    values = [(l["country"], l["region"]) for l in locations]
    with conn.cursor() as cur:
        rows = execute_values(cur, sql, values, fetch=True)
        for row in rows:
            lookup[(row[1], row[2])] = row[0]
    return lookup


def _upsert_dim_salary(conn, salaries):
    lookup = {}
    if not salaries:
        return lookup
    sql = """
        INSERT INTO mart.dim_salary (salary_currency, salary_period, salary_min, salary_max)
        VALUES %s
        ON CONFLICT (salary_currency, salary_period, salary_min, salary_max)
        DO UPDATE SET salary_currency = EXCLUDED.salary_currency
        RETURNING salary_key, salary_currency, salary_period, salary_min, salary_max
    """
    values = [(s["salary_currency"], s["salary_period"], s["salary_min"], s["salary_max"]) for s in salaries]
    with conn.cursor() as cur:
        rows = execute_values(cur, sql, values, fetch=True)
        for row in rows:
            lookup[(row[1], row[2], row[3], row[4])] = row[0]
    return lookup


def _upsert_dim_level(conn, levels):
    lookup = {}
    if not levels:
        return lookup
    sql = """
        INSERT INTO mart.dim_job_level (job_level)
        VALUES %s
        ON CONFLICT (job_level) DO UPDATE SET job_level = EXCLUDED.job_level
        RETURNING level_key, job_level
    """
    values = [(l["job_level"],) for l in levels]
    with conn.cursor() as cur:
        rows = execute_values(cur, sql, values, fetch=True)
        for row in rows:
            lookup[row[1]] = row[0]
    return lookup


def _upsert_dim_industry(conn, industry_names):
    lookup = {}
    if not industry_names:
        return lookup
    sql = """
        INSERT INTO mart.dim_industry (industry_name)
        VALUES %s
        ON CONFLICT (industry_name) DO UPDATE SET industry_name = EXCLUDED.industry_name
        RETURNING industry_key, industry_name
    """
    values = [(name,) for name in industry_names]
    with conn.cursor() as cur:
        rows = execute_values(cur, sql, values, fetch=True)
        for row in rows:
            lookup[row[1]] = row[0]
    return lookup


def _upsert_dim_job_type(conn, job_type_names):
    lookup = {}
    if not job_type_names:
        return lookup
    sql = """
        INSERT INTO mart.dim_job_type (job_type_name)
        VALUES %s
        ON CONFLICT (job_type_name) DO UPDATE SET job_type_name = EXCLUDED.job_type_name
        RETURNING job_type_key, job_type_name
    """
    values = [(name,) for name in job_type_names]
    with conn.cursor() as cur:
        rows = execute_values(cur, sql, values, fetch=True)
        for row in rows:
            lookup[row[1]] = row[0]
    return lookup


def _upsert_dim_date(conn, dates):
    lookup = {}
    if not dates:
        return lookup
    sql = """
        INSERT INTO mart.dim_date (date_key, full_date, year, quarter, month, month_name, week, day, weekday)
        VALUES %s
        ON CONFLICT (date_key) DO NOTHING
    """
    values = []
    for d in dates:
        key = _date_key(d)
        values.append((
            key, d, d.year, (d.month - 1) // 3 + 1, d.month, d.strftime("%B"),
            int(d.strftime("%W")), d.day, d.strftime("%A"),
        ))
        lookup[d] = key
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
    return lookup


def _upsert_facts(conn, facts, company_lu, location_lu, salary_lu, level_lu, date_lu):
    if not facts:
        return {}

    sql = """
        INSERT INTO mart.fact_remote_jobs (
            job_id, company_key, location_key, date_key, salary_key, level_key,
            job_title, job_url, excerpt, salary_min, salary_max, salary_avg, load_date
        ) VALUES %s
        ON CONFLICT (job_id) DO UPDATE SET
            company_key  = EXCLUDED.company_key,
            location_key = EXCLUDED.location_key,
            date_key     = EXCLUDED.date_key,
            salary_key   = EXCLUDED.salary_key,
            level_key    = EXCLUDED.level_key,
            job_title    = EXCLUDED.job_title,
            job_url      = EXCLUDED.job_url,
            excerpt      = EXCLUDED.excerpt,
            salary_min   = EXCLUDED.salary_min,
            salary_max   = EXCLUDED.salary_max,
            salary_avg   = EXCLUDED.salary_avg,
            load_date    = EXCLUDED.load_date
        RETURNING job_key, job_id
    """
    values = []
    for f in facts:
        salary_key = salary_lu.get(f["salary_key_tuple"])
        location_key = location_lu.get((f["country"], f["region"])) if f["country"] else None
        values.append((
            f["job_id"],
            company_lu.get(f["company_name"]),
            location_key,
            date_lu.get(f["full_date"]),
            salary_key,
            level_lu.get(f["job_level"]),
            f["job_title"], f["job_url"], f["excerpt"],
            f["salary_min"], f["salary_max"], f["salary_avg"],
            f["load_date"],
        ))

    job_key_lookup = {}
    with conn.cursor() as cur:
        rows = execute_values(cur, sql, values, fetch=True)   # <-- FIX: ambil return value
        for row in rows:
            job_key_lookup[row[1]] = row[0]
    return job_key_lookup


def _load_bridge(conn, table, fk_col, job_key_lookup, job_map, dim_lookup):
    # normalisasi key job_key_lookup jadi string agar sama dengan job_map (hasil deserialize XCom JSON)
    job_key_lookup_str = {str(k): v for k, v in job_key_lookup.items()}

    rows = []
    for job_id, names in job_map.items():
        job_key = job_key_lookup_str.get(str(job_id))
        if job_key is None:
            continue
        for name in names:
            key = dim_lookup.get(name)
            if key is not None:
                rows.append((job_key, key))

    if not rows:
        return

    with conn.cursor() as cur:
        job_keys = list({r[0] for r in rows})
        cur.execute(f"DELETE FROM mart.{table} WHERE job_key = ANY(%s)", (job_keys,))
        sql = f"INSERT INTO mart.{table} (job_key, {fk_col}) VALUES %s"
        execute_values(cur, sql, rows)


def run_mart_load(ti, conn=None, **kwargs):
    conn = get_connection()
    
    payload = ti.xcom_pull(
        task_ids="transform_data_remote_jobs_mart"
    )
    
    try:
        company_lu = _upsert_dim_company(conn, payload["companies"])
        location_lu = _upsert_dim_location(conn, payload["locations"])
        salary_lu = _upsert_dim_salary(conn, payload["salaries"])
        level_lu = _upsert_dim_level(conn, payload["levels"])
        industry_lu = _upsert_dim_industry(conn, payload["industries"])
        job_type_lu = _upsert_dim_job_type(conn, payload["job_types"])

        unique_dates = {f["full_date"] for f in payload["facts"]}
        date_lu = _upsert_dim_date(conn, unique_dates)

        job_key_lookup = _upsert_facts(
            conn, payload["facts"], company_lu, location_lu, salary_lu, level_lu, date_lu
        )

        _load_bridge(conn, "bridge_job_industry", "industry_key", job_key_lookup,
                     payload["job_industry_map"], industry_lu)
        _load_bridge(conn, "bridge_job_type", "job_type_key", job_key_lookup,
                     payload["job_type_map"], job_type_lu)

        conn.commit()
        print(f"Total Transformed Data Payload Successfully Loaded: {len(payload['facts'])}")
    except Exception:
        conn.rollback()
        raise
    finally:
        if conn:
            conn.close()