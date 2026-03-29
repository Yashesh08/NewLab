from .models import PlatformSettings


def platform_settings(request):
    settings_obj, _ = PlatformSettings.objects.get_or_create(
        pk=1,
        defaults={
            'platform_name': 'LearnSphere',
            'courses_visible': True,
        },
    )
    return {
        'platform_name': settings_obj.platform_name,
        'courses_visible': settings_obj.courses_visible,
    }
