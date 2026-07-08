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

CREATE TABLE IF NOT EXISTS mart.fact_remote_jobs(
    job_key BIGINT PRIMARY KEY NOT NULL,
    job_id BIGINT ,
    company_key BIGINT,
    location_key BIGINT,
    date_key BIGINT,
    salary_key BIGINT,
    level_key BIGINT,
    job_title VARCHAR (255),
    job_url TEXT,
    excerpt TEXT,
    salary_min NUMERIC (12,2),
    salary_max NUMERIC (12,2),
    salary_avg NUMERIC (12,2),
    load_date TIMESTAMP,

    CONSTRAINT fk_company
        FOREIGN KEY(company_key)
        REFERENCES mart.dim_company(company_key),

    CONSTRAINT fk_location
        FOREIGN KEY(location_key)
        REFERENCES mart.dim_location(location_key),

    CONSTRAINT fk_level
        FOREIGN KEY(level_key)
        REFERENCES mart.dim_job_level(level_key),

    CONSTRAINT fk_salary
        FOREIGN KEY(salary_key)
        REFERENCES mart.dim_salary(salary_key),

    CONSTRAINT fk_date
        FOREIGN KEY(date_key)
        REFERENCES mart.dim_date(date_key)
);

CREATE TABLE mart.bridge_job_industry (

    job_key BIGINT NOT NULL,
    industry_key INTEGER NOT NULL,

    PRIMARY KEY(job_key, industry_key),

    FOREIGN KEY(job_key)
        REFERENCES mart.fact_job_posting(job_key)
        ON DELETE CASCADE,

    FOREIGN KEY(industry_key)
        REFERENCES mart.dim_industry(industry_key)
);

CREATE TABLE mart.bridge_job_type (

    job_key BIGINT NOT NULL,
    job_type_key INTEGER NOT NULL,

    PRIMARY KEY(job_key, job_type_key),

    FOREIGN KEY(job_key)
        REFERENCES mart.fact_job_posting(job_key)
        ON DELETE CASCADE,

    FOREIGN KEY(job_type_key)
        REFERENCES mart.dim_job_type(job_type_key)
);

CREATE TABLE IF NOT EXISTS mart.dim_company(
    company_key BIGINT PRIMARY KEY NOT NULL,
    company_name VARCHAR (255),
    company_logo TEXT
);

CREATE TABLE IF NOT EXISTS mart.dim_location(
    location_key BIGINT PRIMARY KEY NOT NULL,
    country VARCHAR (255),
    region VARCHAR (255)
);

CREATE TABLE IF NOT EXISTS mart.dim_salary(
    salary_key BIGINT PRIMARY KEY NOT NULL,
    salary_currency VARCHAR (100),
    salary_period VARCHAR (100),
    salary_min NUMERIC (12,2),
    salary_max NUMERIC (12,2)
);

CREATE TABLE IF NOT EXISTS mart.dim_level(
    level_key BIGINT PRIMARY KEY NOT NULL,
    job_level VARCHAR (255)
);

CREATE TABLE mart.dim_industry (
    industry_key BIGINT PRIMARY KEY,
    industry_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE mart.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    year SMALLINT,
    quarter SMALLINT,
    month SMALLINT,
    month_name VARCHAR(20),
    week SMALLINT,
    day SMALLINT,
    weekday VARCHAR(20)
);