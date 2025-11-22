from rest_framework import serializers
from .models import ChatMessage, Attachment, MessageAttachment
from courses.serializers import LessonSerializer


class AttachmentSerializer(serializers.ModelSerializer):
    size_mb = serializers.ReadOnlyField()

    class Meta:
        model = Attachment
        fields = ['id', 'attachment_id', 'title', 'filename', 'size_bytes', 'size_mb', 'mime_type', 'short_summary', 'tags', 'file']


class ChatMessageSerializer(serializers.ModelSerializer):
    message_attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'text', 'reply_to', 'created_at', 'time_display', 'message_attachments']


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['sender', 'text', 'reply_to', 'time_display']





