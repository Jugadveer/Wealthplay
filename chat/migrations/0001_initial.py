

from django .conf import settings 
from django .db import migrations ,models 
import django .db .models .deletion 


class Migration (migrations .Migration ):

    initial =True 

    dependencies =[
    migrations .swappable_dependency (settings .AUTH_USER_MODEL ),
    ('courses','0001_initial'),
    ]

    operations =[
    migrations .CreateModel (
    name ='Attachment',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('attachment_id',models .CharField (max_length =50 ,unique =True )),
    ('file',models .FileField (upload_to ='attachments/')),
    ('title',models .CharField (max_length =200 )),
    ('filename',models .CharField (max_length =255 )),
    ('size_bytes',models .BigIntegerField ()),
    ('mime_type',models .CharField (max_length =100 )),
    ('short_summary',models .TextField (blank =True )),
    ('tags',models .JSONField (blank =True ,default =list )),
    ('metadata',models .JSONField (blank =True ,default =dict )),
    ('created_at',models .DateTimeField (auto_now_add =True )),
    ],
    options ={
    'ordering':['-created_at'],
    },
    ),
    migrations .CreateModel (
    name ='ChatMessage',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('sender',models .CharField (choices =[('wise','Wise'),('nex','Nex'),('user','User')],max_length =20 )),
    ('text',models .TextField ()),
    ('created_at',models .DateTimeField (auto_now_add =True )),
    ('time_display',models .CharField (blank =True ,max_length =10 )),
    ('lesson',models .ForeignKey (blank =True ,null =True ,on_delete =django .db .models .deletion .CASCADE ,related_name ='messages',to ='courses.lesson')),
    ('reply_to',models .ForeignKey (blank =True ,null =True ,on_delete =django .db .models .deletion .SET_NULL ,related_name ='replies',to ='chat.chatmessage')),
    ],
    options ={
    'ordering':['created_at'],
    },
    ),
    migrations .CreateModel (
    name ='TopicChatMessage',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('course_id',models .CharField (max_length =100 )),
    ('module_id',models .CharField (blank =True ,max_length =100 )),
    ('sender',models .CharField (choices =[('nex','Nex'),('user','User')],max_length =20 )),
    ('text',models .TextField ()),
    ('created_at',models .DateTimeField (auto_now_add =True )),
    ('time_display',models .CharField (blank =True ,max_length =10 )),
    ('user',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,related_name ='topic_chats',to =settings .AUTH_USER_MODEL )),
    ],
    options ={
    'ordering':['created_at'],
    'indexes':[models .Index (fields =['user','course_id','module_id'],name ='chat_topicc_user_id_e0d947_idx')],
    },
    ),
    migrations .CreateModel (
    name ='MessageAttachment',
    fields =[
    ('id',models .BigAutoField (auto_created =True ,primary_key =True ,serialize =False ,verbose_name ='ID')),
    ('attachment',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,to ='chat.attachment')),
    ('message',models .ForeignKey (on_delete =django .db .models .deletion .CASCADE ,related_name ='message_attachments',to ='chat.chatmessage')),
    ],
    options ={
    'unique_together':{('message','attachment')},
    },
    ),
    ]
