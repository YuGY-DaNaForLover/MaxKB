from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application_ext', '0003_application_ext_is_checkbox'),
    ]

    operations = [
        migrations.AddField(
            model_name='ApplicationExt',
            name='is_public',
            field=models.BooleanField(default=False, verbose_name='是否公共应用'),
        )
    ]
