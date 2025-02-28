import re
from datetime import datetime
import requests
import time

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

def validate_cve_list(cve_list):
    """
    Valida una lista di CVE_IDs assicurandosi che ciascuno rispetti il formato CVE-AAAA-NNNN,
    dove AAAA è un anno compreso tra il 1999 e l'anno corrente, e NNNN è composto da almeno quattro cifre.

    Args:
        cve_list (str): Stringa contenente CVE_IDs separati da virgola.

    Returns:
        list: Lista di CVE_IDs validi.
    """
    current_year = datetime.now().year
    cve_pattern = re.compile(r'^CVE-(1999|2\d{3})-\d{4,19}$')
    cve_ids = [cve.strip() for cve in cve_list.split(',') if cve_pattern.match(cve.strip())]
    return [cve for cve in cve_ids if 1999 <= int(cve.split('-')[1]) <= current_year]

def fetch_cve_details(cve_id):
    """Recupera i dettagli di una CVE dal database NVD con log dettagliati."""
    try:
        print(f"Requesting details for {cve_id}...")
        params = {"cveId": cve_id}
        response = requests.get(NVD_API_URL, params=params)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 429:
            print(f"Rate limit exceeded! Waiting before retrying...")
            time.sleep(5)  # Aspetta 5 secondi prima di riprovare
            return fetch_cve_details(cve_id)  # Riprova la richiesta
        
        response.raise_for_status()
        data = response.json()
        print(f"Fetched data for {cve_id}: {data}")

        if "vulnerabilities" in data and data["vulnerabilities"]:
            cve_data = data["vulnerabilities"][0]["cve"]

            descriptions = cve_data.get("descriptions", [])
            description = next((d["value"] for d in descriptions if d["lang"] == "en"), "N/A")
            publish_date = cve_data.get("published", "N/A")
            metrics = cve_data.get("metrics", {})
            impact_v2 = metrics.get("cvssMetricV2", [{}])[0].get("cvssData", {})
            impact_v3 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})

            result = {
                "id": cve_id,
                "description": description,
                "publish_date": publish_date,
                "impact_v2": impact_v2,
                "impact_v3": impact_v3,
            }
            print(f"Extracted details for {cve_id}: {result}")
            return result
        else:
            print(f"CVE {cve_id} not found in NVD database")
            return {"id": cve_id, "error": "CVE not found in NVD database"}

    except requests.RequestException as e:
        print(f"Error fetching {cve_id}: {e}")
        return {"id": cve_id, "error": str(e)}


def fetch_multiple_cve_details(cve_list):
    """Recupera i dettagli per una lista di CVE."""
    cve_details = []
    for cve_id in cve_list:
        details = fetch_cve_details(cve_id)
        if details:
            cve_details.append(details)
    print(f"Final CVE details list: {cve_details}")
    return cve_details
