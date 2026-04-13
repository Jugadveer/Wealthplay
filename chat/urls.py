from django .urls import path ,include 
from rest_framework .routers import DefaultRouter 
from .views import (
ChatMessageViewSet ,AttachmentViewSet ,
mentor_respond ,mentor_respond_rag ,general_inquiry ,
get_topic_chat ,save_topic_message 
)

router =DefaultRouter ()
router .register (r'messages',ChatMessageViewSet ,basename ='message')
router .register (r'attachments',AttachmentViewSet ,basename ='attachment')

urlpatterns =[
path ('mentor/respond/',mentor_respond ,name ='mentor_respond'),
path ('mentor/rag/',mentor_respond_rag ,name ='mentor_respond_rag'),
path ('mentor/inquiry/',general_inquiry ,name ='general_inquiry'),
path ('topic/<str:course_id>/',get_topic_chat ,name ='get_topic_chat'),
path ('topic/<str:course_id>/<str:module_id>/',get_topic_chat ,name ='get_topic_chat_with_module'),
path ('topic/save/',save_topic_message ,name ='save_topic_message'),
path ('',include (router .urls )),
]


