from django.shortcuts import render,redirect

# Create your views here.
from django.contrib.auth import get_user_model
User = get_user_model()

from django.contrib.auth import authenticate
from django.contrib.auth import login,logout
from .models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from django.db.models import Count

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def gen(n):
    import string
    import random
    var2 = ""
    for i in range(n):
        var2 += random.choice(string.ascii_letters)
    return var2


@login_required
def leavegroup(request):
    room_code = request.GET.get("roomcode")
    print(room_code)
    group = ChatGroup.objects.get(code=room_code)
    group.members.remove(request.user)
    msg = ChatMessage(type='INFO',group=group,user=request.user,content=f'{request.user.username} left')
    msg.save()
    if request.user == group.user:
        if group.members.all().count()!=0:
            group.user = group.members.first()
            group.save()
        else:
            group.delete()
            print("Group deleted")
    print(f"{request.user} left {room_code}")
    return JsonResponse({"status":"200","room_code":room_code})

@login_required
def autocomplete(request):
    if request.is_ajax():
        query = request.GET.get("term", "")
        # profiles = User.objects.filter(username__icontains=query)
        results = []
        # ext = ChatGroup.objects.annotate(c=Count('members')).filter(c=2,members__in=[request.user])
        # for profile in profiles:
        #     group = ext.filter(members__in=[profile]).last()
        #     results.append({
        #         "label":profile.first_name+" "+profile.last_name,
        #         "value":group.code
        #         })
        groups = ChatGroup.objects.annotate(c=Count('members')).filter(name__icontains=query)
        for g in groups:
            results.append({
                "label":g.name,
                "value":g.code
            })
        if results==[]:
            results.append({"label":"No Match Found","value":""})
        return JsonResponse(results,safe=False)

    elif request.method=="GET":
        code = request.GET.get("mysearchid")
        group = ChatGroup.objects.get(code = code)
        return redirect("chat:room" ,room_code=code)


@login_required
def user_logout(request):
    try:
        logout(request)
        return JsonResponse({"msg":"Logged out"},status=200)
    except Exception as e:
        return JsonResponse({"msg":e} , status=500)

def checkLogin(request):
    if request.user.is_authenticated:
        return JsonResponse(status=200)
    else:
        return JsonResponse(status=400)

from .serializers import MessageSerializer, GroupSerializer
def getMessages(request):
    grpcode = request.GET.get("grpcode")
    msgs = ChatMessage.objects.filter(group__code=grpcode)
    files = msgs.exclude(file__isnull=True)
    seri = MessageSerializer(msgs,many=True)
    seri2 = MessageSerializer(files,many=True)
    seri3 = list(ChatGroup.objects.get(code=grpcode).members.all().values("username"))
    seri4 = list(ChatGroup.objects.get(code=grpcode).online.all().values("username"))
    print(seri4)
    d = {
        "msgs":seri.data,
        "files":seri2.data,
        "members":seri3,
        "online":seri4
    }
    return JsonResponse(d,safe=False,status=200)

def getgroupdetails(request):
    grpcode = request.GET.get("grpcode")
    grp = ChatGroup.objects.get(code=grpcode)
    details = {"name":grp.name,"code":grp.code,"user":grp.user.username,"members":grp.members.all().count(),"online":grp.online.all().count()}
    return JsonResponse(details,status=200)

def home(request):
    if request.method == "GET":
        chlist = set()
        login = False
        if request.user.is_authenticated:
            login = True
            for i in ChatGroup.objects.filter(user=request.user):
                chlist.add(i)
            for i in ChatGroup.objects.filter(members__in=[request.user]):
                chlist.add(i)
        context = {}
        context["chlist"] = list(chlist)
        context["login"] = login
        print(context)
        return render(request,"chat/main.html",context)
    else:
        room_code = request.POST.get("code")
        email = request.POST.get("email")
        user = None
        if email:
            try:
                user = User.objects.get(username=email.split("@")[0])
            except:
                user = User(username=email.split("@")[0],email=email,password="ashishMe")
                user.save()
            login(request,user)
            print(user,"Logged in")
            return redirect("chat:home")
        else:
            return redirect("chat:room",room_code=room_code)

def userlogin(request):
    print(request.POST)
    if request.method == "POST":
        email = request.POST.get("emaillogin")
        user = None
        if email:
            print(email)
            try:
                user = User.objects.get(username=email.split("@")[0])
            except:
                user = User(username=email.split("@")[0],email=email,password="ashishMe")
                user.save()
            login(request,user)
            return JsonResponse({"msg":"Successfully Logged In"}, status=200)
        return JsonResponse({"msg":"Invalid Email"}, status=400)

@login_required
def download_file(request,msg_id):
    print("New")
    msg = ChatMessage.objects.get(id=msg_id)
    if msg.file == None:
        return HttpResponse("Sorry file doesn't exists")
    return redirect(msg.download_temp_url())

@login_required
def messageFileUpload(request):
    if request.method == "POST" and request.FILES:
        files = request.FILES.getlist('myfile[]')
        file_ids = []
        file_names = []
        file_sizes = []
        for i in files:
            grp = ChatGroup.objects.get(code=request.POST.get("room_code"))
            msg = None
            msg = ChatMessage(user=request.user,file=i.name,group=grp)
            msg.save(i)
            file_names.append(i.name)
            file_ids.append(msg.id)
            file_sizes.append(i.size)
        return JsonResponse({"msg":"Files Uploaded Successfully","file_ids":file_ids,"file_names":file_names,"file_sizes":file_sizes}, status=200)


@login_required
def startChat(request):
    room_code = gen(10)
    new = ChatGroup(code=room_code,name=request.POST.get("groupName"),user=request.user)
    new.save()
    new.members.add(request.user)
    new.save()
    msg = ChatMessage(type='INFO',group=new,user=request.user,content=f'{request.user.username} created this group')
    msg.save()
    print("[ Group created. ]")
    return JsonResponse({"room_code":room_code},status=200)

@login_required
def checkgroup(request,room_code):
    group = ChatGroup.objects.filter(code=room_code)
    print(group)
    if group.count()==0:
        print("[ No such meeting found! ]")
        return JsonResponse({"msg":"No such meeting found!","status":"400"})
    else:
        group = group.first()
        if request.user in group.members.all():
            return JsonResponse({"msg":"Accepted","status":"200"},status=200)
        else:
            print("Reject")
            msg = {}
            msg["type"] =  'request_status'
            msg["username"] = request.user.username
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(room_code,msg)
            print("Just After")
            return JsonResponse({"msg":"Rejected","status":"403"},status=403)

@login_required
def requestaction(request):
    if request.method == "POST":
        print("Inside request action")
        username = request.POST.get("username",None)
        code= request.POST.get("code",None)
        user = User.objects.get(username=username)
        group = ChatGroup.objects.get(code = code)
        action = request.POST.get("action",None)
        print(username,code,group,action)
        if action=="true":
            group.members.add(user)
            msg = ChatMessage(type='INFO',group=group,user=user,content=f'{user.username} joined this group')
            msg.save()
        print(f"[ Action taken {action} ]",username,code,action,type(action))
        msg = {}
        msg["type"] =  'request_status'
        msg["result"] = action
        msg["code"] = code
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(username,msg)
        return JsonResponse({"action":action,"username":username})

@login_required
def chat(request,room_code=None):
    group = ChatGroup.objects.filter(code=room_code)
    if group.count()==0:
        print("[ No such meeting found! ]")
        messages.warning(request,"No such meeting found!")
        return redirect("chat:home")
    else:
        group = group.first()
    username = None
    context = {}
    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = gen(5)

    group.members.add(request.user)
    messages = ChatMessage.objects.filter(group=group).order_by("created_on")
    context["username"] = username
    context["room_code"] = room_code
    context["group"] = group
    context["cmessages"] = messages
    print(context)
    return render(request,"chat/chatroom.html",context)
