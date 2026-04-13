from django .contrib import admin 
from .models import ChatMessage ,Attachment ,MessageAttachment 


@admin .register (ChatMessage )
class ChatMessageAdmin (admin .ModelAdmin ):
    list_display =['id','sender','lesson','text_preview','created_at']
    list_filter =['sender','lesson','created_at']
    search_fields =['text']
    readonly_fields =['created_at']

    def text_preview (self ,obj ):
        return obj .text [:50 ]+'...'if len (obj .text )>50 else obj .text 
    text_preview .short_description ='Text'


@admin .register (Attachment )
class AttachmentAdmin (admin .ModelAdmin ):
    list_display =['attachment_id','title','mime_type','size_bytes','created_at']
    search_fields =['title','attachment_id']
    list_filter =['mime_type','created_at']


@admin .register (MessageAttachment )
class MessageAttachmentAdmin (admin .ModelAdmin ):
    list_display =['message','attachment']
