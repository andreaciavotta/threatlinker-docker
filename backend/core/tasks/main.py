import os
import random
import math
import time
from celery import shared_task, chord, group
from core.models import Task
from core.tasks.task_config import NUM_WORKERS
from core.tasks.worker_task import process_cve_subgroup
from core.tasks.end_task import final_task
import ast


@shared_task(queue="heavy_tasks")
def process_task_with_chord(task_id):
    """
    Recupera la task dal database, ottiene le CVE associate e le elabora con un Celery chord.

    Args:
        task_id (int): ID della task da processare.
    """
    print(f"Starting Celery Chord per Task ID: {task_id}")

    try:
        # Ottieni la task dal database
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        error_msg = f"Task con ID {task_id} non trovata."
        print(error_msg)
        return error_msg

    cve_list = []

    if isinstance(task.cve_hosts, list):
        cve_list = task.cve_hosts
    elif isinstance(task.cve_hosts, str):
        try:
            import ast
            cve_list = ast.literal_eval(task.cve_hosts)
        except Exception as e:
            print(f"[WARN] Errore parsing stringa cve_hosts: {e}")
            cve_list = []

    if not cve_list:
        error_msg = f"Nessuna CVE trovata per la task {task_id}"
        print(error_msg)
        return error_msg

    print(f"Numero totale di CVE trovate: {len(cve_list)}")

    # Dividi la lista di CVE in gruppi basati sulla costante NUM_PROCESSES
    total_cves = len(cve_list)
    subgroups = []
    start = 0
    for i in range(NUM_WORKERS):
        # Le prime (total_cves % NUM_PROCESSES) liste avranno un elemento in più
        group_size = total_cves // NUM_WORKERS + (1 if i < (total_cves % NUM_WORKERS) else 0)
        subgroup = cve_list[start: start + group_size]
        subgroups.append(subgroup)
        print(f"Gruppo {i+1}: {subgroup}")
        start += group_size

    # Crea il Chord: ogni worker elabora un sottogruppo e poi esegue il task finale
    chord_tasks = group(process_cve_subgroup.s(subgroup, task_id) for subgroup in subgroups if subgroup)
    workflow = chord(chord_tasks)(final_task.s(task_id))

    print(f"Chord avviato con {len(subgroups)} gruppi di CVE (Task ID: {task_id})")
    return workflow.id  # Restituisce l'ID della task Chord Celery
