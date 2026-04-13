from django .contrib import admin 
from .models import (
Course ,Topic ,Lesson ,MentorPersona ,
UserCourseCustomization ,UserCourseProgress 
)


@admin .register (Course )
class CourseAdmin (admin .ModelAdmin ):
    list_display =['title','created_at']
    search_fields =['title']
    list_filter =['created_at']


@admin .register (Topic )
class TopicAdmin (admin .ModelAdmin ):
    list_display =['title','course','order']
    search_fields =['title']
    list_filter =['course']


@admin .register (Lesson )
class LessonAdmin (admin .ModelAdmin ):
    list_display =['title','topic','order']
    search_fields =['title']
    list_filter =['topic']


@admin .register (MentorPersona )
class MentorPersonaAdmin (admin .ModelAdmin ):
    list_display =['name']
    search_fields =['name']


@admin .register (UserCourseCustomization )
class UserCourseCustomizationAdmin (admin .ModelAdmin ):
    list_display =['user','course_id','is_active','created_at']
    search_fields =['user__username','course_id']
    list_filter =['is_active','created_at']


@admin .register (UserCourseProgress )
class UserCourseProgressAdmin (admin .ModelAdmin ):
    list_display =['user','course_id','module_id','status','progress_percent','last_accessed']
    search_fields =['user__username','course_id']
    list_filter =['status','created_at']
