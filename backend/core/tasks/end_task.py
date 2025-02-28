from celery import shared_task
from core.tasks.utils import _get_task


@shared_task(queue="heavy_tasks")
def final_task(status, task_id):
    """
    Aggiorna lo stato di completamento di una task specificata e modifica il campo 'ai_models'
    aggiungendo il suffisso '_keyword' ai modelli già presenti.

    :param status: Stato corrente del processo (es. 'complete', 'in_progress').
    :param task_id: ID della task da aggiornare.
    :return: Dizionario con lo stato finale e l'ID della task.
    """
    print(f"Start complete_task_progress for Task ID: {task_id}, status: {status}")
    
    task = _get_task(task_id)

    try:
        # Verifica se la task è completata
        if task.check_task_completion():
            task.status = "complete"
            task.save()
            print(f"Task {task_id} marked as complete.")
            return {"status": "completed", "task_id": task_id}
        else:
            # Se non completata, aggiorna lo stato come ancora in progresso
            task.status = "in_progress"
            task.save()
            print(f"Task {task_id} still in progress.")
            return {"status": "in_progress", "task_id": task_id}
    except Exception as e:
        # Log e gestione degli errori generici
        print(f"Error while updating Task ID {task_id}: {e}")
        return {"status": "failed", "error": str(e), "task_id": task_id}



