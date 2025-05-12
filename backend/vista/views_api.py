from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from uuid import uuid4

from core.models import Task
from core.tasks import process_task_with_chord

class ThreatAnalysisView(APIView):
    def post(self, request):
        data = request.data
        cve_list = data.get("cve_list")
        callback_url = data.get("callback_url")  # ✅ aggiunto

        if not cve_list or not isinstance(cve_list, list):
            return Response({"error": "Missing or invalid 'cve_list'"}, status=status.HTTP_400_BAD_REQUEST)

        task = Task.objects.create(
            name=f"API Task {uuid4().hex[:6]}",
            notes="Created via API",
            ai_models=["SBERT Hyb"],  # JSONField: dev'essere lista!
            cve_hosts=cve_list,       # JSONField
            callback_url=callback_url # ✅ aggiunto qui
        )

        process_task_with_chord.delay(task.id)

        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


