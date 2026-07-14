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

def _load_api_metadata(conn, records):
    if not records:
        print("No API metadata records found. Skipping load.")
        return
    sql = """
        INSERT INTO stagging.stg_api_metadata (
            ingestion_id, api_version, documentation_url, friendly_notice,
            job_count, last_update, filter_count, filter_geo,
            filter_industry, filter_tag, success, extracted_at
        ) VALUES %s
        ON CONFLICT (ingestion_id) DO NOTHING
    """
    values = [(
        r["ingestion_id"], r["api_version"], r["documentation_url"], r["friendly_notice"],
        r["job_count"], r["last_update"], r["filter_count"], r["filter_geo"],
        r["filter_industry"], r["filter_tag"], r["success"], r["extracted_at"],
    ) for r in records]
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
 
def _load_jobs(conn, records):
    if not records:
        return
    sql = """
        INSERT INTO stagging.stg_jobs (
            ingestion_id, job_id, job_slug, job_url, job_title, company_name,
            company_logo, job_geo, job_level, job_excerpt, job_description,
            pub_date, salary_min, salary_max, salary_currency, salary_period,
            extracted_at
        ) VALUES %s
        ON CONFLICT (job_id) DO UPDATE SET
            ingestion_id     = EXCLUDED.ingestion_id,
            job_title        = EXCLUDED.job_title,
            company_name     = EXCLUDED.company_name,
            company_logo     = EXCLUDED.company_logo,
            job_geo          = EXCLUDED.job_geo,
            job_level        = EXCLUDED.job_level,
            job_excerpt      = EXCLUDED.job_excerpt,
            job_description  = EXCLUDED.job_description,
            pub_date         = EXCLUDED.pub_date,
            salary_min       = EXCLUDED.salary_min,
            salary_max       = EXCLUDED.salary_max,
            salary_currency  = EXCLUDED.salary_currency,
            salary_period    = EXCLUDED.salary_period,
            extracted_at     = EXCLUDED.extracted_at
    """
    values = [(
        r["ingestion_id"], r["job_id"], r["job_slug"], r["job_url"], r["job_title"],
        r["company_name"], r["company_logo"], r["job_geo"], r["job_level"],
        r["job_excerpt"], r["job_description"], r["pub_date"], r["salary_min"],
        r["salary_max"], r["salary_currency"], r["salary_period"], r["extracted_at"],
    ) for r in records]
    with conn.cursor() as cur:
        execute_values(cur, sql, values)
 
 
def _load_job_industries(conn, records):
    if not records:
        return
    with conn.cursor() as cur:
        job_ids = list({r["job_id"] for r in records})
        cur.execute(
            "DELETE FROM stagging.stg_job_industries WHERE job_id = ANY(%s)",
            (job_ids,),
        )
        sql = "INSERT INTO stagging.stg_job_industries (job_id, industry, extracted_at) VALUES %s"
        values = [(r["job_id"], r["industry"], r["extracted_at"]) for r in records]
        execute_values(cur, sql, values)
 
 
def _load_job_types(conn, records):
    if not records:
        return
    with conn.cursor() as cur:
        job_ids = list({r["job_id"] for r in records})
        cur.execute(
            "DELETE FROM stagging.stg_job_types WHERE job_id = ANY(%s)",
            (job_ids,),
        )
        sql = "INSERT INTO stagging.stg_job_types (job_id, job_type, extracted_at) VALUES %s"
        values = [(r["job_id"], r["job_type"], r["extracted_at"]) for r in records]
        execute_values(cur, sql, values)
 
 
def run_stagging_load(ti, conn=None, **kwargs):

    staged_data = ti.xcom_pull(
        task_ids="transform_data_remote_jobs"
    )

    conn = get_connection() 

    try:
        _load_api_metadata(conn, staged_data["api_metadata"])
        _load_jobs(conn, staged_data["jobs"])
        _load_job_industries(conn, staged_data["job_industries"])
        _load_job_types(conn, staged_data["job_types"])

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        if conn:
            conn.close()