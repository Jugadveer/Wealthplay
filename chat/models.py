from django .db import models 
from django .contrib .auth .models import User 
from courses .models import Lesson 


class ChatMessage (models .Model ):
    SENDER_CHOICES =[
    ('wise','Wise'),
    ('nex','Nex'),
    ('user','User'),
    ]

    lesson =models .ForeignKey (Lesson ,on_delete =models .CASCADE ,related_name ='messages',null =True ,blank =True )
    sender =models .CharField (max_length =20 ,choices =SENDER_CHOICES )
    text =models .TextField ()
    reply_to =models .ForeignKey ('self',on_delete =models .SET_NULL ,null =True ,blank =True ,related_name ='replies')
    created_at =models .DateTimeField (auto_now_add =True )
    time_display =models .CharField (max_length =10 ,blank =True )

    class Meta :
        ordering =['created_at']

    def __str__ (self ):
        return f"{self .sender }: {self .text [:50 ]}"


class TopicChatMessage (models .Model ):
    """Topic-specific chat messages - saves chat per user, per course, per module"""
    SENDER_CHOICES =[
    ('nex','Nex'),
    ('user','User'),
    ]

    user =models .ForeignKey (User ,on_delete =models .CASCADE ,related_name ='topic_chats')
    course_id =models .CharField (max_length =100 )
    module_id =models .CharField (max_length =100 ,blank =True )
    sender =models .CharField (max_length =20 ,choices =SENDER_CHOICES )
    text =models .TextField ()
    created_at =models .DateTimeField (auto_now_add =True )
    time_display =models .CharField (max_length =10 ,blank =True )

    class Meta :
        ordering =['created_at']
        indexes =[
        models .Index (fields =['user','course_id','module_id']),
        ]

    def __str__ (self ):
        return f"{self .user .username } - {self .course_id } - {self .sender }: {self .text [:50 ]}"


class Attachment (models .Model ):
    attachment_id =models .CharField (max_length =50 ,unique =True )
    file =models .FileField (upload_to ='attachments/')
    title =models .CharField (max_length =200 )
    filename =models .CharField (max_length =255 )
    size_bytes =models .BigIntegerField ()
    mime_type =models .CharField (max_length =100 )
    short_summary =models .TextField (blank =True )
    tags =models .JSONField (default =list ,blank =True )
    metadata =models .JSONField (default =dict ,blank =True )
    created_at =models .DateTimeField (auto_now_add =True )

    class Meta :
        ordering =['-created_at']

    def __str__ (self ):
        return self .title 

    def size_mb (self ):
        return round (self .size_bytes /(1024 *1024 ),2 )


class MessageAttachment (models .Model ):
    message =models .ForeignKey (ChatMessage ,on_delete =models .CASCADE ,related_name ='message_attachments')
    attachment =models .ForeignKey (Attachment ,on_delete =models .CASCADE )

    class Meta :
        unique_together =['message','attachment']
