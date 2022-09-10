# Generated by Django 2.2.16 on 2022-09-10 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0012_auto_20220908_1449'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='already_follower',
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_follower'),
        ),
    ]