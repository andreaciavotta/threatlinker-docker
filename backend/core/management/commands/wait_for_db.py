import time
from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Attende che il database sia pronto prima di eseguire Django"

    def handle(self, *args, **kwargs):
        self.stdout.write("Attendo il database...")
        db_conn = None
        while not db_conn:
            try:
                db_conn = connections["default"]
                db_conn.cursor()
            except OperationalError:
                self.stdout.write("Database non disponibile, riprovo tra 1 secondo...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database pronto!"))
