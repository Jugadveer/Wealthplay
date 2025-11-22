from rest_framework import serializers
from .models import UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'original_filename', 'mime_type', 'size_bytes', 'uploaded_at']
        read_only_fields = ['original_filename', 'mime_type', 'size_bytes', 'uploaded_at']





