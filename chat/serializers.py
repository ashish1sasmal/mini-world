from rest_framework import serializers
from .models import ChatMessage, ChatGroup
from rest_framework.response import Response
from rest_framework import status
import json
from django.contrib.auth import get_user_model
User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    class Meta:
        model = ChatMessage
        fields = '__all__'

    def get_username(self,obj):
        return obj.user.username

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatGroup
        fields = '__all__'
