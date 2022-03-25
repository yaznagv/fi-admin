# Generated by Django 2.2.24 on 2022-03-25 11:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0004_auto_20170504_1544'),
    ]

    operations = [
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_time', models.DateTimeField(auto_now=True, null=True, verbose_name='updated')),
                ('acronym', models.CharField(blank=True, max_length=25, verbose_name='Acronym')),
                ('language', models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese'), ('es', 'Spanish'), ('fr', 'French')], max_length=10, verbose_name='Language')),
                ('name', models.CharField(max_length=75, verbose_name='Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('order', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Order')),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'License',
                'verbose_name_plural': 'Licenses',
            },
        ),
        migrations.AlterField(
            model_name='sourcelanguage',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese'), ('es', 'Spanish'), ('fr', 'French')], max_length=10, verbose_name='Language'),
        ),
        migrations.AlterField(
            model_name='sourcelanguagelocal',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese'), ('es', 'Spanish'), ('fr', 'French')], max_length=10, verbose_name='Language'),
        ),
        migrations.AlterField(
            model_name='sourcetype',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese'), ('es', 'Spanish'), ('fr', 'French')], max_length=10, verbose_name='Language'),
        ),
        migrations.AlterField(
            model_name='sourcetypelocal',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese'), ('es', 'Spanish'), ('fr', 'French')], max_length=10, verbose_name='language'),
        ),
        migrations.AlterField(
            model_name='thematicarea',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese'), ('es', 'Spanish'), ('fr', 'French')], max_length=10, verbose_name='Language'),
        ),
        migrations.AlterField(
            model_name='thematicarealocal',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese'), ('es', 'Spanish'), ('fr', 'French')], max_length=10, verbose_name='Language'),
        ),
        migrations.CreateModel(
            name='LicenseLocal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(choices=[('en', 'English'), ('pt-br', 'Portuguese'), ('es', 'Spanish'), ('fr', 'French')], max_length=10, verbose_name='Language')),
                ('name', models.CharField(max_length=75, verbose_name='Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('license', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.License', verbose_name='License')),
            ],
            options={
                'verbose_name': 'Translation',
                'verbose_name_plural': 'Translations',
            },
        ),
    ]
