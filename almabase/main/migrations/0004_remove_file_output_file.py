# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-11 04:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20160911_0404'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='output_file',
        ),
    ]
