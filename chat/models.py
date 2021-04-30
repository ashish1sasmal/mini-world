from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model
# Create your models here.
from .s3 import s3_service
import uuid
from django.db.models.signals import post_delete
from django.dispatch import receiver

User = get_user_model()

class ChatGroup(models.Model):
    code = models.CharField(max_length=20)
    members = models.ManyToManyField(User,related_name="group_members",blank=True)
    online = models.ManyToManyField(User,related_name="group_online",blank=True)
    user = models.ForeignKey(User,related_name="group_user",on_delete=models.CASCADE,blank=True,null=True)

    def __str__(self):
        return self.code


class ChatMessage(models.Model):
    content = models.TextField(blank=True,null=True)
    unique_file = models.CharField(max_length=100, blank=True,null=True)
    file = models.CharField(max_length=500,blank=True,null=True)
    group = models.ForeignKey(ChatGroup,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now=True)

    def save(self,file=None ,**kwargs):
        if file:
            self.unique_file = f"{uuid.uuid1()}.{self.file.split('.')[-1]}"
            s3_service.upload_file_obj(file,self.unique_file)
        super(ChatMessage, self).save(**kwargs)

    def download_temp_url(self):
        return s3_service.download_file(self.unique_file)


@receiver(post_delete, sender=ChatMessage)
def delete_file_s3(sender, instance, **kwargs):
    if instance.unique_file:
        s3_service.delete_file(instance.unique_file)
        print("Doc deleted @")
