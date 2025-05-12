from data.models import CVE
from core.functions.cve_handling import fetch_cve_details
from django.utils.dateparse import parse_datetime
import os
import requests
import zipfile
from datetime import datetime
import json
from data.models import CVE

CVE_DOWNLOAD_DIR = "download/cve"
CVE_BASE_URL = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{}.json.zip"  # Formato URL

def download_cve_data():
    """Scarica i file ZIP delle CVE per ogni anno dal 2002 ad oggi e li salva nella directory /download/cve/"""

    return True

def extract_zip_file(zip_path, extract_to):
    """Estrai un file ZIP nella directory specificata."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"File {zip_path} estratto con successo in {extract_to}")
    except zipfile.BadZipFile:
        print(f"Errore: il file {zip_path} non è un archivio ZIP valido.")


def import_cve_data():
    """Importa i dati CVE nel database solo se non sono già presenti."""
    # Estrai lo ZIP se necessario
    zip_path = os.path.join(CVE_DOWNLOAD_DIR, "nvdcve.zip")
    extracted_flag = os.path.join(CVE_DOWNLOAD_DIR, ".extracted_flag")

    if os.path.exists(zip_path) and not os.path.exists(extracted_flag):
        print("📦 Estrazione CVE 2002-2025 file ZIP...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(CVE_DOWNLOAD_DIR)
        with open(extracted_flag, "w") as f:
            f.write("done")
        print("✅ Estrazione completata.")

    json_files = sorted(
        [f for f in os.listdir(CVE_DOWNLOAD_DIR) if f.endswith(".json")],
        key=lambda x: int(x.split('-')[-1].split('.')[0])  # Ordina per anno
    )

    total_cve_count = 0
    processed_cve_count = 0

    # Conta il numero totale di CVE nei file JSON
    for file_name in json_files:
        file_path = os.path.join(CVE_DOWNLOAD_DIR, file_name)
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            total_cve_count += len(data.get("CVE_Items", []))

    # Importazione delle CVE
    for file_name in json_files:
        file_path = os.path.join(CVE_DOWNLOAD_DIR, file_name)
        print(f"Processing file: {file_name}")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                for item in data.get("CVE_Items", []):
                    processed_cve_count += 1  # Contatore di avanzamento

                    cve_meta = item["cve"]["CVE_data_meta"]
                    cve_id = cve_meta["ID"]

                    # Descrizione in inglese
                    description_data = item["cve"]["description"]["description_data"]
                    description = next((d["value"] for d in description_data if d["lang"] == "en"), None)

                    # Date
                    published_date = item.get("publishedDate", None)

                    # Impatti CVSS
                    impact_v2 = item.get("impact", {}).get("baseMetricV2", None)
                    impact_v3 = item.get("impact", {}).get("baseMetricV3", None)

                    # Inserisci nel database
                    cve_data = {
                        "description": description,
                        "published_date": published_date,
                        "impact_v2": impact_v2,
                        "impact_v3": impact_v3,
                    }

                    cve_instance, created = CVE.objects.update_or_create(id=cve_id, defaults=cve_data)


            print(f"File {file_name} importato con successo.")

        except Exception as e:
            print(f"Errore durante l'importazione delle CVE dal file {file_name}: {e}")

    print("Importazione CVE completata con successo.")

def get_or_create_cves(cve_list):
    # Recupera le CVE esistenti dal database
    existing_cves = {cve.id: cve for cve in CVE.objects.filter(id__in=cve_list)}
    new_cves = []

    for cve_id in cve_list:
        if cve_id not in existing_cves:
            details = fetch_cve_details(cve_id)
            if "error" not in details:
                new_cves.append(CVE(
                    id=details["id"],
                    description=details["description"],
                    published_date=parse_datetime(details["publish_date"]),
                    impact_v2=details["impact_v2"],
                    impact_v3=details["impact_v3"]
                ))
    if new_cves:
        CVE.objects.bulk_create(new_cves)

    # Combina le CVE esistenti e quelle nuove, poi estrae gli ID
    combined_cves = list(existing_cves.values()) + new_cves
    return [cve.id for cve in combined_cves]
