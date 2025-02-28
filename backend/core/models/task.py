from django.db import models
import ast  # Importa per convertire la stringa in lista

class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ('correlation', 'Correlation'),
    ]
    
    TASK_STATUS_CHOICES = [
        ('complete', 'Complete'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('in_progress', 'In Progress'),
    ]
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES, default='correlation')
    status = models.CharField(max_length=50, choices=TASK_STATUS_CHOICES, default='pending')
    cve_hosts = models.JSONField(null=True)
    ai_models = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.id} - {self.name} ({self.get_type_display()})"

    def get_full_details(self):
        return (
            f"ID: {self.id}\n"
            f"Name: {self.name}\n"
            f"Type: {self.get_type_display()}\n"
            f"Status: {self.get_status_display()}\n"
            f"Notes: {self.notes}\n"
            f"Created at: {self.created_at}\n"
            f"Updated at: {self.updated_at}\n"
        )


    def check_task_completion(self):
        """
        Controlla se tutte le SingleCorrelation sono complete per questa Task.
        La Task è completa solo se:
        - Il numero di SingleCorrelation complete è uguale al numero di CVE nel campo cve_hosts.
        - Ogni cve_id nelle SingleCorrelation corrisponde a una CVE nella lista cve_hosts.
        """
        try:
            # Decodifica la stringa in una vera lista Python
            cve_list = ast.literal_eval(self.cve_hosts) if isinstance(self.cve_hosts, str) else self.cve_hosts
            if not isinstance(cve_list, list):
                print("[ERROR] cve_hosts non è una lista valida")
                return False

            total_cves = len(cve_list)  # Numero totale di CVE nella task
            completed_correlations = self.single_correlations.filter(status='complete')  # SingleCorrelation completate
            completed_cve_ids = {sc.cve_id for sc in completed_correlations}  # Ottieni gli ID delle CVE completate

            # Controlla se tutte le CVE della task sono state processate correttamente
            if len(completed_cve_ids) == total_cves and set(cve_list) == completed_cve_ids:
                self.status = 'complete'
                self.save()
                return True
            else:
                self.status = 'in_progress'
                self.save()
                return False
        except Exception as e:
            print(f"[ERROR] Errore in check_task_completion: {e}")
            return False

class SingleCorrelation(models.Model):
    SINGLECORRELATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=50, choices=SINGLECORRELATION_STATUS_CHOICES, default='pending')
    cve_id = models.CharField(max_length=20)  # ID della CVE
    task = models.ForeignKey(Task, related_name='single_correlations', on_delete=models.CASCADE, null=True)  # ForeignKey con Task
    similarity_scores = models.JSONField()  # Punteggi di similarità per ogni metodo (es. 'method1': score, 'method2': score)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Single Correlation: {self.cve_id}"
