from celery import shared_task
from core.tasks.utils import _get_task


@shared_task(bind=True, queue="heavy_tasks", max_retries=3, default_retry_delay=60)
def final_task(self, status, task_id):
    print(f"Start complete_task_progress for Task ID: {task_id}, status: {status}")
    
    task = _get_task(task_id)

    try:
        if task.check_task_completion():
            task.status = "complete"
            task.save()
            print(f"Task {task_id} marked as complete.")

            # 🔁 Invia callback SOLO se richiesto
            if task.callback_url:
                print(f"Invio callback a {task.callback_url}")
                try:
                    from django.utils import timezone
                    from django.conf import settings
                    import requests

                    def format_result(sc):
                        results = []

                        # Prendiamo la lista CAPEC associata al modello SBERT Hyb
                        all_scores = sc.similarity_scores.get("SBERT", [])

                        # Ordina per "rank" e prendi le prime 10
                        top_capecs = sorted(all_scores, key=lambda x: x[1].get("rank", 9999))[:10]

                        for capec_id, score_data in top_capecs:
                            results.append({
                                "capec_id": capec_id,
                                "rank": score_data.get("rank"),
                                "final_score": score_data.get("final_score")
                            })

                        return {
                            "cve_id": sc.cve_id,
                            "top_capecs": results
                        }


                    payload = {
                        "task_id": task.id,
                        "generated_at": timezone.now().isoformat(),
                        "cve_results": [
                            format_result(sc) for sc in task.single_correlations.all()
                        ]
                    }

                    headers = {"Content-Type": "application/json"}
                    if hasattr(settings, "IP2_TOKEN"):
                        headers["X-API-KEY"] = settings.IP2_TOKEN

                    r = requests.post(task.callback_url, json=payload, headers=headers, timeout=10)
                    r.raise_for_status()
                    print("Callback inviato correttamente.")

                except Exception as exc:
                    print(f"[ERROR] Invio callback fallito: {exc}")
                    raise self.retry(exc=exc)

            return {"status": "completed", "task_id": task_id}
        else:
            task.status = "in_progress"
            task.save()
            print(f"Task {task_id} still in progress.")
            return {"status": "in_progress", "task_id": task_id}

    except Exception as e:
        print(f"Error while updating Task ID {task_id}: {e}")
        return {"status": "failed", "error": str(e), "task_id": task_id}




