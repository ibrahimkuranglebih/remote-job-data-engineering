import uuid
from datetime import datetime, timezone
import psycopg2
import os

def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
 
def transform_raw_responses(raw_responses):
    extracted_at = datetime.now(timezone.utc)

    api_metadata_records = []
    job_records = []
    job_industry_records = []
    job_type_records = []

    seen_job_ids = set()

    for resp in raw_responses:
        ingestion_id = str(uuid.uuid4())

        jobs = resp.get("jobs", [])
        applied = resp.get("appliedFilters", {})

        api_metadata_records.append({
            "ingestion_id": ingestion_id,
            "api_version": resp.get("apiVersion"),
            "documentation_url": resp.get("documentationUrl"),
            "friendly_notice": resp.get("friendlyNotice"),
            "job_count": resp.get("jobCount"),
            "last_update": _parse_dt(resp.get("lastUpdate")),
            "filter_count": applied.get("count"),
            "filter_geo": applied.get("geo", resp.get("filter_geo")),
            "filter_industry": applied.get("industry", resp.get("filter_industry")),
            "filter_tag": applied.get("tag"),
            "success": resp.get("success", bool(jobs)),
            "extracted_at": extracted_at,
        })

        for job in jobs:

            job_id = job.get("id")
            if job_id is None:
                continue

            if job_id in seen_job_ids:
                continue

            seen_job_ids.add(job_id)

            job_records.append({
                "ingestion_id": ingestion_id,
                "job_id": job_id,
                "job_slug": job.get("jobSlug"),
                "job_url": job.get("url"),
                "job_title": job.get("jobTitle"),
                "company_name": job.get("companyName"),
                "company_logo": job.get("companyLogo"),
                "job_geo": job.get("jobGeo"),
                "job_level": job.get("jobLevel"),
                "job_excerpt": job.get("jobExcerpt"),
                "job_description": job.get("jobDescription"),
                "pub_date": _parse_dt(job.get("pubDate")),
                "salary_min": job.get("salaryMin"),
                "salary_max": job.get("salaryMax"),
                "salary_currency": job.get("salaryCurrency"),
                "salary_period": job.get("salaryPeriod"),
                "extracted_at": extracted_at,
            })

            for ind in job.get("jobIndustry", []):
                job_industry_records.append({
                    "job_id": job_id,
                    "industry": ind,
                    "extracted_at": extracted_at,
                })

            for jt in job.get("jobType", []):
                job_type_records.append({
                    "job_id": job_id,
                    "job_type": jt,
                    "extracted_at": extracted_at,
                })

    return {
        "api_metadata": api_metadata_records,
        "jobs": job_records,
        "job_industries": job_industry_records,
        "job_types": job_type_records,
    }
 
def run_stagging_transform(ti, **kwargs):
    raw_responses = ti.xcom_pull(
        task_ids="extract_data_remote_jobs"
    )
    staged_data = transform_raw_responses(raw_responses)
    return staged_data