# Generated by Django 4.2.19 on 2025-02-24 03:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ip_lookup_app', '0007_awssecuritygroup_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='awssecuritygroup',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='awssecuritygroup',
            name='group_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='awssecuritygroup',
            name='inbound_rules_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='awssecuritygroup',
            name='outbound_rules_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='awssecuritygroup',
            name='owner',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='awssecuritygroup',
            name='vpc_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
