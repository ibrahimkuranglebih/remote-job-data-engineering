import requests
import json
import time

# selecting all country / region that available in the API response
geo = [
    "apac", "emea", "latam", "argentina", "australia",
    "austria", "belgium", "brazil", "bulgaria", "canada",
    "china", "hong-kong", "costa-rica", "croatia", "cyprus",
    "czechia", "denmark", "estonia", "europe", "finland",
    "france", "germany", "greece", "hungary", "ireland",
    "israel", "italy", "japan", "latvia", "lithuania",
    "mexico", "netherlands", "new-zealand", "norway",
    "philippines", "poland", "portugal", "romania",
    "serbia", "singapore", "slovakia", "slovenia",
    "south-korea", "spain", "sweden", "switzerland",
    "thailand", "turkiye", "united-arab-emirates",
    "uk", "ukraine", "usa", "vietnam"
]
# total jobs per country / region with spesific industry selected
count = 1
# industry field that available in the API response
industry = [
    'admin-support', 'copywriting', 'translation-localization','supporting',
    'technical-support', 'cybersecurity','data-science','design-multimedia',
    'web-app-design', 'video-audio-production', 'admin', 'e-commerce',
    'education', 'accounting-finance' ,'healthcare', 'hr', 'legal',
    'marketing', 'business', 'seller', 'seo', 'smm', 'management',
    'project-management', 'engineering', 'dev', 'qa-testing'
]

# base url for the API endpoint

BASE_URL = 'https://jobicy.com/api/v2/remote-jobs'

all_jobs = []

def extract_jobs() :
    for g in geo:
        for ind in industry:

            params = {
                "count": count,
                "geo": g,
                "industry": ind
            }

            print(f"Fetching {g} - {ind}")

            try:
                response = requests.get(BASE_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                #print(json.dumps(data, indent=4, ensure_ascii=False))
                
                jobs = data.get("jobs", [])

                for job in jobs:

                    job["filter_geo"] = g
                    job["filter_industry"] = ind

                    all_jobs.append(job)

            except Exception as e:
                print(f"Failed {g} - {ind}: {e}")

            # supaya tidak terlalu cepat request ke API
            time.sleep(0.5)

#extract_jobs()