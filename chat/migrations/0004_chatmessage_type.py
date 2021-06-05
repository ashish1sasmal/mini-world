# Generated by Django 3.1.1 on 2021-06-05 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_chatgroup_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='type',
            field=models.CharField(choices=[('MSG', 'MSG'), ('INFO', 'INFO')], default='MSG', max_length=20),
        ),
    ]