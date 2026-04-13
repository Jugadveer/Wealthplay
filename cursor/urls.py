from django .urls import path 
from .import views 

urlpatterns =[
path ('explain',views .explain ,name ='cursor_explain'),
path ('health',views .health ,name ='cursor_health'),
]

