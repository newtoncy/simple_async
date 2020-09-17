# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2020-09-15 16:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ResultBackend',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.BinaryField(max_length=4096, null=True, verbose_name='\u5e8f\u5217\u5316\u7684\u8fd4\u56de\u503c')),
                ('task_id', models.CharField(max_length=100, unique=True, verbose_name='\u4efb\u52a1id')),
                ('status', models.CharField(default='Pending', max_length=40, verbose_name='\u72b6\u6001')),
            ],
        ),
    ]