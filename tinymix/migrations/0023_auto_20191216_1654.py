# Generated by Django 3.0 on 2019-12-16 16:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tinymix', '0022_value_int_value'),
    ]

    operations = [
        migrations.RenameField(
            model_name='value',
            old_name='value_name',
            new_name='enum_value_name',
        ),
    ]
