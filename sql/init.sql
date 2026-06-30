CREATE SCHEMA IF NOT EXISTS stagging;

CREATE TABLE IF NOT EXISTS stagging.stg_api_metadata(
    ingestion_id UUID PRIMARY KEY NOT NULL,
    api_version VARCHAR(255),
    documentation_url TEXT,
    friendly_notice TEXT,
    job_count INTEGER,
    last_update TIMESTAMP,
    filter_count INTEGER,
    filter_geo VARCHAR (255),
    filter_industry VARCHAR (255),
    filter_tag VARCHAR (255),
    success BOOLEAN,
    extracted_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS stagging.stg_jobs(
    ingestion_id UUID REFERENCES stagging.stg_api_metadata(ingestion_id),
    job_id BIGINT PRIMARY KEY NOT NULL,
    job_slug VARCHAR (255),
    job_url TEXT,
    job_title VARCHAR (255),
    company_name VARCHAR (255),
    company_logo TEXT,
    job_geo VARCHAR (255),
    job_level VARCHAR (255),
    job_excerpt TEXT,
    job_description TEXT,
    pub_date TIMESTAMP,
    salary_min NUMERIC (12,2),
    salary_max NUMERIC (12,2),
    salary_currency VARCHAR (100),
    salary_period VARCHAR (100),
    extracted_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS stagging.stg_job_industries(
    job_id BIGINT REFERENCES stagging.stg_jobs(job_id),
    industry VARCHAR (255),
    extracted_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS stagging.stg_job_types(
    job_id BIGINT REFERENCES stagging.stg_jobs(job_id),
    job_type VARCHAR (255),
    extracted_at TIMESTAMP NOT NULL
);

CREATE SCHEMA IF NOT EXISTS mart;