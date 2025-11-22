from rest_framework import serializers
from .models import Course, Topic, Lesson, MentorPersona


class MentorPersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorPersona
        fields = ['mentor_id', 'name', 'role', 'system_prompt', 'tone_profile', 'expertise_tags']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'lesson_id', 'title', 'order', 'content_type', 'metadata']


class TopicSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ['id', 'topic_id', 'title', 'order', 'summary', 'lessons']


class CourseSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'course_id', 'title', 'description', 'cover_image', 'language', 'currency', 'version', 'created_at', 'topics']





