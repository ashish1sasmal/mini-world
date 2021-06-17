import json
from channels.generic.websocket import AsyncWebsocketConsumer,WebsocketConsumer

from .models import *
from django.contrib.auth.models import User

from channels.db import database_sync_to_async
import time
#

class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        time.sleep(1)
        user = self.scope['user']
        if user.is_authenticated:
            await self.updateUser(user,True)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'online_status',
                    'action': True,
                    'username': user.username,
                }
            )
            print("After add")


    @database_sync_to_async
    def updateUser(self,user,status):
        group = ChatGroup.objects.get(code=self.room_name)
        if status:
            group.online.add(user)
            print(f"[ {user} added ]")
        else:
            group.online.remove(user)
            print(f"[ {user} removed ]")

    async def disconnect(self, close_code):
        # await self.delGroup()
        user = self.scope['user']
        await self.updateUser(user,False)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'online_status',
                'action': False,
                'username': user.username,
            }
        )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def delGroup(self):
        ChatGroup.objects.get(code=self.room_group_name).delete()
        print("[ Group Deleted. ]")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message',None)
        username = text_data_json.get('username',None)
        file_ids = text_data_json.get("file_ids",None)
        del_msg_id = text_data_json.get("del_msg_id",None)
        if file_ids:
            file_sizes = text_data_json.get("file_sizes",None)
            file_names = text_data_json.get("file_names",None)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chatroom_files',
                    'file_ids' : file_ids,
                    'file_sizes' : file_sizes,
                    "file_names":file_names,
                    'username': username
                }
            )
        elif del_msg_id:
            await self.updateDB(del_msg_id=del_msg_id)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delete_message',
                    'del_msg_id' : del_msg_id
                }
            )
        elif message:
            print(username,"HI")
            await self.updateDB(message=message,username=username)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chatroom_message',
                    'message': message,
                    'username': username,
                }
            )

        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'request_status',
                    'username': username,
                }
            )

    async def delete_message(self, event):
        await self.send(text_data=json.dumps({
            'del_msg_id' : event.get("del_msg_id",None)
        }))

    async def chatroom_files(self, event):
        await self.send(text_data=json.dumps({
            'file_ids' : event.get('file_ids',[]),
            'file_sizes' : event.get('file_sizes',[]),
            'username': event.get('username',None),
            "file_names":event.get('file_names',[])
        }))

    async def chatroom_message(self, event):
        message = event['message']
        username = event['username']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))

    async def online_status(self,event):
        action = event["action"]
        username = event['username']
        await self.send(text_data=json.dumps({
            'action': action,
            'username': username,
        }))

    async def request_status(self,event):
        username = event['username']
        request = "true"
        await self.send(text_data=json.dumps({
            'username': username,
            "request":request
        }))

    @database_sync_to_async
    def updateDB(self,**kwargs):
        del_msg_id = kwargs.get("del_msg_id",None)
        message = kwargs.get("message",None)
        user = self.scope["user"]
        group = ChatGroup.objects.get(code = self.room_group_name)
        if del_msg_id!=None:
            # Delete all chat messages
            if del_msg_id == -1:
                msgs = ChatMessage.objects.filter(group__code = self.room_group_name).exclude(type="INFO")
                msgs.delete()
                print(f"Messages of {self.room_group_name} deleted successfully")

            # Delete particular message with id
            else:
                ChatMessage.objects.filter(id=del_msg_id).delete()
                print(f"Message with id {del_msg_id} deleted successfully")
        else:
            username = kwargs.get("username",None)
            user = User.objects.get(username=username)
            newM = ChatMessage(content=message,user=user,group=group)
            newM.save()
            print("Message Saved!")
        return True
    pass

class AcceptRequest(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        self.room_name = user.username
        self.room_group_name = user.username

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def receive(self, text_data):
        tjson = json.loads(text_data)
        result = tjson.get("result")
        code = tjson.get("code")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'request_status',
                'result': result,
                'code': code
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def request_status(self,event):
        result = event["result"]
        code = event['code']
        await self.send(text_data=json.dumps({
            'result': result,
            'code': code,
        }))
