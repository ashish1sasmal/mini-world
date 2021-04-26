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

def gen(n):
    import string
    import random
    var2 = ""
    for i in range(n):
        var2 += random.choice(string.ascii_letters)
    return var2

@login_required
def user_logout(request):
    logout(request)
    return redirect('chat:home')

def home(request):
    if request.method == "GET":
        chlist = set()
        if request.user.is_authenticated:
            for i in ChatMessage.objects.filter(user=request.user).values("group").distinct():
                print(i)
                chlist.add(ChatGroup.objects.get(id=i["group"]))
            for i in ChatGroup.objects.filter(user=request.user):
                chlist.add(i)
        context = {}
        context["chlist"] = list(chlist)
        print(context)
        return render(request,"chat/home.html",context)
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

@login_required
def download_file(request,msg_id):
    # Download File ; check if already exists in user's filemanager; If not download from sender's filemanager (if exist there)
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
    new = ChatGroup(code=gen(10),user=request.user)
    new.save()
    print("[ Group created. ]")
    return redirect("chat:room",room_code=new.code)

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
