import json
import os
from datetime import datetime
from data.models import CVE

def get_cve_statistics():
    # Determina la cartella del file corrente
    current_dir = os.path.dirname(os.path.abspath(__file__))
    stats_file = os.path.join(current_dir, "cve_stats.json")
    
    # Controlla il numero attuale di CVE nel database
    total_cve_count = CVE.objects.count()
    
    # Se il file esiste, prova a caricare i dati salvati
    if os.path.exists(stats_file):
        with open(stats_file, "r") as f:
            cached_stats = json.load(f)
        
        # Confronta il numero di CVE con quello salvato
        if cached_stats.get("total_cve_count") == total_cve_count:
            return cached_stats  # Restituisce i dati salvati se il numero di CVE è invariato
    
    # Calcola le statistiche poiché il file è assente o il numero di CVE è cambiato
    valid_cves = CVE.objects.exclude(description__startswith="Rejected reason")
    valid_cve_count = valid_cves.count()

    # 1. Distribuzione per rating
    rating_counts = {'Low': 0, 'Medium': 0, 'High': 0, 'Critical': 0}
    rated_cves = valid_cves.exclude(impact_v2__isnull=True, impact_v3__isnull=True)
    for cve in rated_cves:
        rating = cve.get_overall_rating()
        if rating:
            rating_counts[rating] += 1

    total_rated_cves = sum(rating_counts.values())
    rating_percentages = {
        rating: (count / total_rated_cves) * 100 if total_rated_cves > 0 else 0
        for rating, count in rating_counts.items()
    }

    # 2. Numero di CVE per anno e percentuali
    current_year = datetime.now().year
    cve_per_year_counts = {}
    for cve in valid_cves:
        year = int(cve.id.split('-')[1])
        if year <= current_year:
            cve_per_year_counts[year] = cve_per_year_counts.get(year, 0) + 1

    total_valid_cves = sum(cve_per_year_counts.values())
    cve_per_year_percentages = {
        year: (count / total_valid_cves) * 100 if total_valid_cves > 0 else 0
        for year, count in cve_per_year_counts.items()
    }

    # Aggiunta del timestamp e preparazione dei dati
    stats = {
        'total_cve_count': total_cve_count,
        'valid_cve_count': valid_cve_count,
        'cve_rating_percentages': rating_percentages,
        'cve_per_year_counts': cve_per_year_counts,
        'cve_per_year_percentages': cve_per_year_percentages,
        'last_updated': datetime.now().isoformat()
    }
    
    # Salva i dati nel file JSON per utilizzi futuri
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=4)
    
    return stats
