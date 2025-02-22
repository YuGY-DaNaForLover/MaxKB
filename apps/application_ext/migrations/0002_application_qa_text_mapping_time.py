from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application_ext', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ApplicationQaTextMapping',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, verbose_name='创建时间'),
        ),
        migrations.AddField(
            model_name='ApplicationQaTextMapping',
            name='update_time',
            field=models.DateTimeField(auto_now=True, verbose_name='修改时间'),
        ),
    ]
