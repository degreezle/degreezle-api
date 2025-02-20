# Generated by Django 3.2.14 on 2022-07-13 08:30

import api.models
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Puzzle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_movie_id', models.IntegerField()),
                ('end_movie_id', models.IntegerField()),
                ('object_created', models.DateTimeField(auto_now_add=True)),
                ('object_modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Solution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(default=api.models.generate_token, max_length=100, unique=True)),
                ('solution', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), size=None, unique=True)),
                ('object_created', models.DateTimeField(auto_now_add=True)),
                ('object_modified', models.DateTimeField(auto_now=True)),
                ('puzzle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solutions', related_query_name='solution', to='api.puzzle')),
            ],
        ),
    ]
