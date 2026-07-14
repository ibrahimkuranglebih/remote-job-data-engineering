import requests
import time

# selecting all country / region that available in the API response
geo = [
    "australia", "uk", "usa", "china", "france", "germany", "italy", "japan", "netherlands", "singapore", "south-korea", "switzerland","united-arab-emirates",
]
# total jobs per country / region with spesific industry selected
count = 3
# industry field that available in the API response
industry = [
    'admin-support', 'copywriting', 'supporting',
    'technical-support', 'cybersecurity', 'data-science', 'design-multimedia',
    'web-app-design', 'video-audio-production', 'admin', 'e-commerce',
    'education', 'accounting-finance', 'healthcare', 
    'marketing', 'business', 'seller', 'seo', 'management',
    'project-management', 'engineering', 'dev', 'qa-testing'
]

BASE_URL = 'https://jobicy.com/api/v2/remote-jobs'

def extract_jobs():
    raw_responses = []

    for g in geo:
        for ind in industry:
            params = {"count": count, "geo": g, "industry": ind}
            print(f"Fetching {g} - {ind}")

            try:
                response = requests.get(BASE_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                data["filter_geo"] = g
                data["filter_industry"] = ind

                raw_responses.append(data)

            except Exception as e:
                print(f"Failed {g} - {ind}: {e}")

            # supaya tidak terlalu cepat request ke API
            time.sleep(1)

    return raw_responses