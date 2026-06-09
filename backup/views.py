from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions


class BackupDatabaseView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        return Response({"message": "Backup feature coming soon"}, status=200)


class BackupMediaView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        return Response({"message": "Media backup coming soon"}, status=200)
