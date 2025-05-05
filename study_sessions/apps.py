from django.apps import AppConfig


class StudySessionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'study_sessions'

    def ready(self):
        import study_sessions.signals  # This loads our signals