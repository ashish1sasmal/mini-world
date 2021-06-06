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
    path('search/', views.autocomplete, name='autocomplete'),
    path('checkgroup/<str:room_code>/',views.checkgroup,name="checkgroup"),
    path('requestaction/',views.requestaction,name="requestaction"),
    path('leavegroup/',views.leavegroup,name="leavegroup"),

    path('login/',views.userlogin , name='login'),
    path('checkLogin/',views.checkLogin, name='checkLogin'),
    path('getMessages/',views.getMessages, name="getMessages"),
    path('getgroupdetails/',views.getgroupdetails, name="getgroupdetails"),
    path('invite/', views.invite, name="invite"),
    path('acceptInvite/<str:code>',views.acceptInvite,name="acceptInvite"),
]
