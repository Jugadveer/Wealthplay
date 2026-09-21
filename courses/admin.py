from django.contrib import admin

from .models import UserCourseProgress


@admin.register(UserCourseProgress)
class UserCourseProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course_id', 'module_id', 'status', 'last_accessed')
    list_filter = ('status', 'course_id')
    search_fields = ('user__username', 'course_id')
