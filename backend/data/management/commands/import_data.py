from django.core.management.base import BaseCommand
from data.functions.handle_capecs import import_capec_data
from data.functions.handle_cve import download_cve_data, import_cve_data
from data.models import CAPEC, CVE

EXPECTED_CVE_COUNT = 250000  # Numero atteso di CVE
EXPECTED_CAPEC_COUNT = 500  # Numero atteso di CAPEC
THRESHOLD_PERCENTAGE = 0.95  # Almeno il 95% delle voci devono essere presenti

class Command(BaseCommand):
    help = "Importa le CAPEC e CVE nel database (solo se necessario)"

    def handle(self, *args, **kwargs):
        # ✅ Controllo se le CAPEC sono già presenti in numero sufficiente
        existing_capec_count = CAPEC.objects.count()
        min_required_capec = int(EXPECTED_CAPEC_COUNT * THRESHOLD_PERCENTAGE)

        if existing_capec_count >= min_required_capec:
            print(f"✅ Le CAPEC sono già presenti nel database ({existing_capec_count}/{EXPECTED_CAPEC_COUNT}, {existing_capec_count / EXPECTED_CAPEC_COUNT:.1%}). Nessuna operazione necessaria.")
        else:
            print(f"⚠️ Numero attuale di CAPEC nel database: {existing_capec_count}, attese: {EXPECTED_CAPEC_COUNT} (minimo richiesto: {min_required_capec}).")
            print("📥 Importazione delle CAPEC in corso...")
            import_capec_data()
            print("✅ Operazione CAPEC completata.")

        # ✅ Controllo se le CVE sono già presenti in numero sufficiente
        existing_cve_count = CVE.objects.count()
        min_required_cve = int(EXPECTED_CVE_COUNT * THRESHOLD_PERCENTAGE)

        if existing_cve_count >= min_required_cve:
            print(f"✅ Le CVE sono già presenti nel database ({existing_cve_count}/{EXPECTED_CVE_COUNT}, {existing_cve_count / EXPECTED_CVE_COUNT:.1%}). Nessuna operazione necessaria.")
            return

        print(f"⚠️ Numero attuale di CVE nel database: {existing_cve_count}, attese: {EXPECTED_CVE_COUNT} (minimo richiesto: {min_required_cve}).")
        print("📥 Scaricamento e importazione delle CVE in corso...")

        # Scarica e importa le CVE
        download_cve_data()
        import_cve_data()

        print("✅ Operazione CVE completata.")
