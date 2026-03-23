from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='last_activity',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RemoveField(
            model_name='lesson',
            name='content',
        ),
        migrations.RemoveField(
            model_name='lesson',
            name='video_url',
        ),
        migrations.AddField(
            model_name='lesson',
            name='video',
            field=models.FileField(blank=True, upload_to='tutor/lesson_videos/', validators=[django.core.validators.FileExtensionValidator(['mp4', 'mov', 'mkv', 'webm'])]),
        ),
    ]
