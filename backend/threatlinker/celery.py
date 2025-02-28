# threatlinker/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Imposta il modulo di impostazioni di Django per Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'threatlinker.settings')

# Crea l'applicazione Celery
app = Celery('threatlinker')

# Carica le impostazioni di Celery dal file settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Aggiungi questa riga se non c'è già
app.conf.worker_enable_remote_control = True

# Cerca task definiti nelle app registrate in Django
app.autodiscover_tasks()

# Evita che Django esegua i task sincroni nello stesso processo
app.conf.task_always_eager = False  # Assicurati che sia disattivato

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')