from django.apps import AppConfig


class AttendanceConfig(AppConfig):

    default_auto_field = (
        "django.db.models.BigAutoField"
    )

    name = "attendance"

    def ready(self):

        from attendance.sms.sms_runner import (
            start_sms_worker
        )
    
        start_sms_worker()