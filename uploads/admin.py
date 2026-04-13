from django.contrib import admin
from .models import UploadedFile


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'original_filename', 'mime_type', 'size_bytes', 'uploaded_at']
    list_filter = ['mime_type', 'uploaded_at']
    search_fields = ['original_filename', 'user__username']
