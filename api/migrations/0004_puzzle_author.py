# Generated by Django 3.2.14 on 2023-07-22 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_solution_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='puzzle',
            name='author',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
