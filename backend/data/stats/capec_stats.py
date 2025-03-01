import json
import os
from django.db.models import Count, Avg
from datetime import datetime
from data.models import CAPEC, AttackStep, ExecutionFlow

def get_capec_statistics():
    # Determina la cartella del file corrente
    current_dir = os.path.dirname(os.path.abspath(__file__))
    stats_file = os.path.join(current_dir, "capec_stats.json")
    
    # Controlla il numero attuale di CAPEC nel database
    total_capec_count = CAPEC.objects.count()
    
    # Se il file esiste, prova a caricare i dati salvati
    if os.path.exists(stats_file):
        with open(stats_file, "r") as f:
            cached_stats = json.load(f)
        
        # Confronta il numero di CAPEC con quello salvato
        if cached_stats.get("total_capec_count") == total_capec_count:
            return cached_stats  # Restituisce i dati salvati se il numero di CAPEC è invariato
    
    # Calcola le statistiche poiché il file è assente o il numero di CAPEC è cambiato
    deprecated_capec_count = CAPEC.objects.filter(status='Deprecated').count()
    valid_capec_count = total_capec_count - deprecated_capec_count

    # Numero di CAPEC con Execution Flow
    capecs_with_execution_flow_count = CAPEC.objects.filter(execution_flow_instance__isnull=False).count()
    capecs_without_execution_flow_count = valid_capec_count - capecs_with_execution_flow_count

    # Numero di Attack Steps totali
    total_attack_steps_count = AttackStep.objects.count()

    # Distribuzione del numero di Attack Steps per Execution Flow per ogni CAPEC
    attack_step_distribution = {}
    capecs_with_execution_flow = CAPEC.objects.filter(execution_flow_instance__isnull=False)
    
    for capec in capecs_with_execution_flow:
        num_steps = capec.execution_flow_instance.attack_steps.count()
        if num_steps not in attack_step_distribution:
            attack_step_distribution[num_steps] = {'count': 0, 'percentage': 0.0}
        attack_step_distribution[num_steps]['count'] += 1

    # Calcola la percentuale per ogni numero di Attack Steps
    for num_steps, data in attack_step_distribution.items():
        data['percentage'] = (data['count'] / capecs_with_execution_flow_count) * 100

    # Calcolo della media del numero di Attack Steps per CAPEC con Execution Flow
    avg_attack_steps_per_capec = (
        ExecutionFlow.objects
        .annotate(num_steps=Count('attack_steps'))
        .aggregate(Avg('num_steps'))['num_steps__avg']
    ) or 0

    # Distribuzione delle varie "phase" degli Attack Steps
    phase_distribution = (
        AttackStep.objects
        .values('phase')
        .annotate(count=Count('id'))
    )

    phase_distribution_dict = {
        entry['phase']: {
            'count': entry['count'],
            'percentage': (entry['count'] / total_attack_steps_count) * 100
        }
        for entry in phase_distribution
    }

    stats = {
        'total_capec_count': total_capec_count,
        'deprecated_capec_count': deprecated_capec_count,
        'valid_capec_count': valid_capec_count,
        'capecs_with_execution_flow_count': capecs_with_execution_flow_count,
        'capecs_without_execution_flow_count': capecs_without_execution_flow_count,
        'total_attack_steps_count': total_attack_steps_count,
        'attack_step_distribution': attack_step_distribution,
        'avg_attack_steps_per_capec': avg_attack_steps_per_capec,
        'phase_distribution': phase_distribution_dict,
        'last_updated': datetime.now().isoformat()
    }
    
    # Salva i dati nel file JSON per utilizzi futuri
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=4)
    
    return stats
