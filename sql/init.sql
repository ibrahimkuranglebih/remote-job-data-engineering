-- =====================================================================
-- SCHEMA: stagging  (raw / lightly typed data hasil extract API)
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS stagging;

CREATE TABLE IF NOT EXISTS stagging.stg_api_metadata (
    ingestion_id      UUID PRIMARY KEY NOT NULL,
    api_version       VARCHAR(255),
    documentation_url TEXT,
    friendly_notice   TEXT,
    job_count         INTEGER,
    last_update       TIMESTAMP,
    filter_count      INTEGER,
    filter_geo        VARCHAR(255),
    filter_industry   VARCHAR(255),
    filter_tag        VARCHAR(255),
    success           BOOLEAN,
    extracted_at      TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS stagging.stg_jobs (
    ingestion_id     UUID REFERENCES stagging.stg_api_metadata(ingestion_id),
    job_id           BIGINT PRIMARY KEY NOT NULL,
    job_slug         VARCHAR(255),
    job_url          TEXT,
    job_title        VARCHAR(255),
    company_name     VARCHAR(255),
    company_logo     TEXT,
    job_geo          VARCHAR(255),
    job_level        VARCHAR(255),
    job_excerpt      TEXT,
    job_description  TEXT,
    pub_date         TIMESTAMP,
    salary_min       NUMERIC(12,2),
    salary_max       NUMERIC(12,2),
    salary_currency  VARCHAR(100),
    salary_period    VARCHAR(100),
    extracted_at     TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS stagging.stg_job_industries (
    job_id       BIGINT REFERENCES stagging.stg_jobs(job_id),
    industry     VARCHAR(255),
    extracted_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS stagging.stg_job_types (
    job_id       BIGINT REFERENCES stagging.stg_jobs(job_id),
    job_type     VARCHAR(255),
    extracted_at TIMESTAMP NOT NULL
);

-- =====================================================================
-- SCHEMA: mart  (star schema)
-- NOTE urutan create sengaja: dim dulu -> fact -> bridge, supaya FK valid.
-- Surrogate key pakai GENERATED ALWAYS AS IDENTITY supaya gampang di-upsert
-- dari kode Python (insert ... ON CONFLICT ... RETURNING key).
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS mart.dim_company (
    company_key  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    company_logo TEXT,
    UNIQUE (company_name)
);

CREATE TABLE IF NOT EXISTS mart.dim_location (
    location_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country      VARCHAR(255),
    region       VARCHAR(255),
    UNIQUE (country, region)
);

CREATE TABLE IF NOT EXISTS mart.dim_salary (
    salary_key      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    salary_currency VARCHAR(100),
    salary_period   VARCHAR(100),
    salary_min      NUMERIC(12,2),
    salary_max      NUMERIC(12,2),
    UNIQUE (salary_currency, salary_period, salary_min, salary_max)
);

CREATE TABLE IF NOT EXISTS mart.dim_job_level (
    level_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_level VARCHAR(255) NOT NULL,
    UNIQUE (job_level)
);

CREATE TABLE IF NOT EXISTS mart.dim_industry (
    industry_key  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    industry_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS mart.dim_job_type (
    job_type_key  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_type_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS mart.dim_date (
    date_key   INTEGER PRIMARY KEY,
    full_date  DATE UNIQUE NOT NULL,
    year       SMALLINT,
    quarter    SMALLINT,
    month      SMALLINT,
    month_name VARCHAR(20),
    week       SMALLINT,
    day        SMALLINT,
    weekday    VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS mart.fact_remote_jobs (
    job_key     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id      BIGINT NOT NULL UNIQUE,
    company_key BIGINT,
    location_key BIGINT,
    date_key    INTEGER,
    salary_key  BIGINT,
    level_key   BIGINT,
    job_title   VARCHAR(255),
    job_url     TEXT,
    excerpt     TEXT,
    salary_min  NUMERIC(12,2),
    salary_max  NUMERIC(12,2),
    salary_avg  NUMERIC(12,2),
    load_date   TIMESTAMP,

    CONSTRAINT fk_company  FOREIGN KEY (company_key)  REFERENCES mart.dim_company(company_key),
    CONSTRAINT fk_location FOREIGN KEY (location_key) REFERENCES mart.dim_location(location_key),
    CONSTRAINT fk_level    FOREIGN KEY (level_key)    REFERENCES mart.dim_job_level(level_key),
    CONSTRAINT fk_salary   FOREIGN KEY (salary_key)   REFERENCES mart.dim_salary(salary_key),
    CONSTRAINT fk_date     FOREIGN KEY (date_key)     REFERENCES mart.dim_date(date_key)
);

CREATE TABLE IF NOT EXISTS mart.bridge_job_industry (
    job_key      BIGINT NOT NULL,
    industry_key BIGINT NOT NULL,
    PRIMARY KEY (job_key, industry_key),
    FOREIGN KEY (job_key)      REFERENCES mart.fact_remote_jobs(job_key) ON DELETE CASCADE,
    FOREIGN KEY (industry_key) REFERENCES mart.dim_industry(industry_key)
);

CREATE TABLE IF NOT EXISTS mart.bridge_job_type (
    job_key      BIGINT NOT NULL,
    job_type_key BIGINT NOT NULL,
    PRIMARY KEY (job_key, job_type_key),
    FOREIGN KEY (job_key)      REFERENCES mart.fact_remote_jobs(job_key) ON DELETE CASCADE,
    FOREIGN KEY (job_type_key) REFERENCES mart.dim_job_type(job_type_key)
);

-- =====================================================================
-- SCHEMA: analytics  (USULAN - belum ada di spesifikasi awal Anda)
-- Berisi tabel ringkasan/agregat siap pakai untuk dashboard/reporting,
-- dibangun dari mart.fact_remote_jobs. Sesuaikan lagi sesuai kebutuhan
-- laporan Anda.
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.agg_jobs_by_industry_geo (
    industry_name VARCHAR(100),
    country        VARCHAR(255),
    job_count      INTEGER,
    avg_salary_min NUMERIC(12,2),
    avg_salary_max NUMERIC(12,2),
    snapshot_date  DATE NOT NULL,
    PRIMARY KEY (industry_name, country, snapshot_date)
);

CREATE TABLE IF NOT EXISTS analytics.agg_jobs_by_company (
    company_name   VARCHAR(255),
    total_jobs     INTEGER,
    avg_salary_avg NUMERIC(12,2),
    snapshot_date  DATE NOT NULL,
    PRIMARY KEY (company_name, snapshot_date)
);

CREATE TABLE IF NOT EXISTS analytics.agg_jobs_daily (
    full_date    DATE PRIMARY KEY,
    job_count    INTEGER,
    avg_salary   NUMERIC(12,2)
);