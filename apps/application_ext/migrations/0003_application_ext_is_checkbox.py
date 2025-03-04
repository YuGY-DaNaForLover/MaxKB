from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application_ext', '0002_application_qa_text_mapping_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='ApplicationExt',
            name='is_checkbox',
            field=models.BooleanField(default=False, verbose_name='回答是否可以被引入'),
        )
    ]
