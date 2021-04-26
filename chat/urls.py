from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path('',views.home,name="home"),
    path('chat/<str:room_code>/',views.chat,name="room"),
    path('newmeet/',views.startChat,name="newchat"),
    path('upload/',views.messageFileUpload , name='uploadmsg'),
    path('downloadfile/<int:msg_id>/',views.download_file,name="download_file"),
    path('logout/',views.user_logout,name='logout'),
]
