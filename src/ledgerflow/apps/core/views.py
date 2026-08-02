from django.db import connection
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class ReadyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            connection.ensure_connection()
            cache.set("ready_probe", "1", timeout=5)
            cache.get("ready_probe")
        except Exception as exc:  # noqa: BLE001
            return Response({"status": "not_ready", "detail": str(exc)}, status=503)
        return Response({"status": "ready"})
