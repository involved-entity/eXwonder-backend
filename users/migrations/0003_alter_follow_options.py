# Generated by Django 5.1.1 on 2024-10-02 11:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_follow'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='follow',
            options={'ordering': ('-pk',)},
        ),
    ]
