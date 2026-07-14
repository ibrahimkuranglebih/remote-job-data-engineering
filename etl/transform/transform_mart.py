from datetime import date
import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", 5432)
    )

def _fetch_all(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def extract_stagging_jobs(conn=None):
    own_conn = conn is None
    conn = conn 
    try:
        jobs = _fetch_all(conn, """
            SELECT job_id, job_slug, job_url, job_title, company_name,
                   company_logo, job_geo, job_level, job_excerpt,
                   pub_date, salary_min, salary_max, salary_currency,
                   salary_period, extracted_at
            FROM stagging.stg_jobs
        """)
        industries = _fetch_all(conn, "SELECT job_id, industry FROM stagging.stg_job_industries")
        types = _fetch_all(conn, "SELECT job_id, job_type FROM stagging.stg_job_types")
        return jobs, industries, types
    finally:
        if own_conn:
            conn.close()


def _split_geo(job_geo):
    if not job_geo:
        return None, None
    return job_geo, None


def build_mart_payload(jobs, industries, types):
    companies = {}
    locations = {}
    salaries = {}
    levels = {}

    fact_rows = []

    for j in jobs:
        if j["company_name"]:
            companies[j["company_name"]] = j.get("company_logo")

        country, region = _split_geo(j["job_geo"])
        if country:
            locations[(country, region)] = True

        salary_key_tuple = (
            j["salary_currency"], j["salary_period"], j["salary_min"], j["salary_max"]
        )
        if any(v is not None for v in salary_key_tuple):
            salaries[salary_key_tuple] = True

        if j["job_level"]:
            levels[j["job_level"]] = True

        pub_date = j["pub_date"].date() if j["pub_date"] else date.today()
        salary_min = j["salary_min"]
        salary_max = j["salary_max"]
        salary_avg = None
        if salary_min is not None and salary_max is not None:
            salary_avg = (salary_min + salary_max) / 2

        fact_rows.append({
            "job_id": j["job_id"],
            "job_title": j["job_title"],
            "job_url": j["job_url"],
            "excerpt": j["job_excerpt"],
            "company_name": j["company_name"],
            "country": country,
            "region": region,
            "job_level": j["job_level"],
            "salary_key_tuple": salary_key_tuple,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_avg": salary_avg,
            "full_date": pub_date,
            "load_date": j["extracted_at"],
        })

    industry_names = sorted({i["industry"] for i in industries if i["industry"]})
    job_type_names = sorted({t["job_type"] for t in types if t["job_type"]})

    job_industry_map = {}
    for i in industries:
        job_industry_map.setdefault(i["job_id"], set()).add(i["industry"])

    job_type_map = {}
    for t in types:
        job_type_map.setdefault(t["job_id"], set()).add(t["job_type"])

    return {
        "companies": [{"company_name": k, "company_logo": v} for k, v in companies.items()],
        "locations": [{"country": c, "region": r} for (c, r) in locations.keys()],
        "salaries": [
            {"salary_currency": c, "salary_period": p, "salary_min": mn, "salary_max": mx}
            for (c, p, mn, mx) in salaries.keys()
        ],
        "levels": [{"job_level": lv} for lv in levels.keys()],
        "industries": industry_names,
        "job_types": job_type_names,
        "facts": fact_rows,
        "job_industry_map": job_industry_map,
        "job_type_map": job_type_map,
    }
    
def run_transform_mart(conn):
    conn = get_connection()  

    try:
        jobs, industries, job_types = extract_stagging_jobs(conn)

        payload = build_mart_payload(
            jobs=jobs,
            industries=industries,
            types=job_types,
        )

        return payload

    finally:
        if conn:
            conn.close()