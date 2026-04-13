from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.files.uploadedfile import UploadedFile as DjangoUploadedFile
from .models import UploadedFile
from .serializers import UploadedFileSerializer
import os


class UploadedFileViewSet(viewsets.ModelViewSet):
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        uploaded_file = UploadedFile.objects.create(
            user=request.user,
            file=file,
            original_filename=file.name,
            mime_type=file.content_type,
            size_bytes=file.size
        )

        serializer = self.get_serializer(uploaded_file)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
