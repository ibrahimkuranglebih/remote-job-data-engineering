# Remote Job Analytics (Data Engineering Project) 
![Version][Version-Shield]

## Project Overview
Struggling to find a job will be the most problem for the job seeker, even it's intern or profesional job. From students to experienced worker, they faced the same problem. This project will provide job seeker to analyze the job market and find perfect job for them. 

## Project Architechture
This project was builded using data engineering concepts, including
* data pipeline to extract, transform, and load data into targeted form datasets
* data warehouse with three schemas, including stagging, mart, and analytics schema for analytics purpose
* dashboard analytics. In this project, i use Power BI to visualize the aggregate data

All of the process was builded by some tech stacks, including
* [![Docker][Docker-Logo]][Docker-Url]
* [![Apache Airflow][Apache-Airflow-Logo]][Apache-Airflow-Url]
* [![Python][Python-Logo]][Python-Url]
* [![Postgres][Postgres-Logo]][Postgres-Url]

<img alt='elt' src='assets/Remote Job Data Engineering Project.png' />

## 📂 Project Structure

```text
project/
│
├── dags/
│   └── Apache Airflow DAGs for orchestrating the ETL workflow.
│
├── etl/
│   ├── extract/
│   │   └── Scripts for extracting data from external APIs.
│   │
│   ├── transform/
│   │   └── Data cleaning, preprocessing, and business transformations.
│   │
│   └── load/
│       └── Load processed data into the Data Warehouse schemas.
│
├── sql/
│   └── SQL scripts for schema creation, views, stored procedures, and queries.
│
│
└── dashboard/
    └── Power BI dashboard files and supporting assets.
```

---

## Directory Overview

| Directory | Description |
|-----------|-------------|
| **dags/** | Contains Apache Airflow DAG definitions used to orchestrate the entire data pipeline. |
| **etl/extract/** | Retrieves raw data from external APIs and prepares it for ingestion. |
| **etl/transform/** | Cleans, standardizes, and transforms raw data into targeted form datasets. |
| **etl/load/** | Loads transformed datasets into the appropriate Data Warehouse schema. |
| **sql/** | Contains SQL scripts for database creation, schema definitions, views, and ETL queries. |
| **docker/** | Contains Dockerfiles and Docker Compose configuration for deploying the project environment. |
| **dashboard/** | Includes Power BI reports (`.pbix`) and any supporting dashboard assets. |

[Version-Shield]:https://img.shields.io/badge/Version-1.0-blue

<!--Markdown Links & Images-->
<!--Url-->
[Docker-Url]:https://www.docker.com/
[Apache-Airflow-Url]:https://airflow.apache.org/
[Python-Url]:https://www.python.org/
[Postgres-Url]:https://www.postgresql.org/
[Version-Url]:https://github.com/ibrahimkuranglebih/Football-Data-Pipeline-12-Leagues?tab=readme-ov-file
<!--Logo-->
[Docker-Logo]:https://img.shields.io/badge/Docker-blue?logo=docker&logoColor=ffffff
[Apache-Airflow-Logo]:https://img.shields.io/badge/Apache_Airflow-017CEE?logo=apacheairflow&logoColor=ffffff
[Python-Logo]:https://img.shields.io/badge/Python-FBEF76?logo=python&logoColor=ffffff
[Postgres-Logo]:https://img.shields.io/badge/Postgres-4169E1?logo=postgresql&logoColor=ffffff
[Version-Shield]:https://img.shields.io/badge/Version-1.2-blue
