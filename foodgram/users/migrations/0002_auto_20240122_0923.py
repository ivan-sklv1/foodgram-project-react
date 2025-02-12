# Generated by Django 3.2.3 on 2024-01-22 06:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscribe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author', models.ForeignKey(help_text='Укажите блогера', on_delete=django.db.models.deletion.CASCADE, related_name='bloger', to=settings.AUTH_USER_MODEL, verbose_name='Блогер')),
                ('follower', models.ForeignKey(help_text='Укажите подписчика', on_delete=django.db.models.deletion.CASCADE, related_name='following', to=settings.AUTH_USER_MODEL, verbose_name='Подписчик')),
            ],
            options={
                'verbose_name': 'Подписка на автора',
                'verbose_name_plural': 'Подписка на авторов',
            },
        ),
        migrations.AddConstraint(
            model_name='subscribe',
            constraint=models.CheckConstraint(check=models.Q(('follower', django.db.models.expressions.F('author'))), name='no_self_subscribe'),
        ),
        migrations.AddConstraint(
            model_name='subscribe',
            constraint=models.UniqueConstraint(fields=('follower', 'author'), name='unique_subscription'),
        ),
    ]
