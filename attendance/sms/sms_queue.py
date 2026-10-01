from django.utils import timezone

from attendance.models import SMSQueue


# =====================================================
# CLEAN OLD SMS QUEUE
# =====================================================

def clean_old_sms_queue():

    today = timezone.localdate()

    # Delete anything that does not belong to today.
    SMSQueue.objects.exclude(
        attendance__date=today
    ).delete()


# =====================================================
# FORMAT STUDENT NAME
# =====================================================

def get_student_name(student):

    middle_name = (
        student.middle_name or ""
    ).strip()

    if middle_name:

        return (
            f"{student.first_name} "
            f"{middle_name} "
            f"{student.last_name}"
        )

    return (
        f"{student.first_name} "
        f"{student.last_name}"
    )


# =====================================================
# CREATE ATTENDANCE SMS MESSAGE
# =====================================================

def create_attendance_message(
    student,
    attendance,
    attendance_label,
    attendance_time
):

    student_name = get_student_name(
        student
    )

    formatted_date = (
        attendance.date.strftime(
            "%B %d, %Y"
        )
    )

    formatted_time = (
        attendance_time.strftime(
            "%I:%M %p"
        )
    )

    message = (
        "AINHS Attendance System: "
        f"{student_name} recorded "
        f"{attendance_label} at "
        f"{formatted_time} on "
        f"{formatted_date}."
    )

    return message


# =====================================================
# QUEUE ATTENDANCE SMS
# =====================================================

def queue_attendance_sms(
    student,
    attendance,
    attendance_type,
    attendance_label,
    attendance_time
):

    # -------------------------------------------------
    # CLEAN YESTERDAY / OLD RECORDS
    # -------------------------------------------------

    clean_old_sms_queue()

    # -------------------------------------------------
    # GET PARENT / GUARDIAN NUMBER
    # -------------------------------------------------

    phone_number = (
        student.parent_contact or ""
    ).strip()

    if not phone_number:

        return {
            "queued": False,
            "reason": "Student has no parent contact."
        }

    # -------------------------------------------------
    # CREATE MESSAGE
    # -------------------------------------------------

    message = create_attendance_message(
        student=student,
        attendance=attendance,
        attendance_label=attendance_label,
        attendance_time=attendance_time
    )

    # -------------------------------------------------
    # CREATE ONLY IF IT DOES NOT ALREADY EXIST
    # -------------------------------------------------

    sms_record, created = (
        SMSQueue.objects.get_or_create(

            attendance=attendance,

            attendance_type=attendance_type,

            phone_number=phone_number,

            defaults={

                "student":
                    student,

                "attendance_time":
                    attendance_time,

                "message":
                    message,

                "status":
                    "PENDING",
            }
        )
    )

    if created:

        return {
            "queued": True,
            "created": True,
            "sms_id": sms_record.id
        }

    return {
        "queued": True,
        "created": False,
        "sms_id": sms_record.id,
        "reason": "SMS already queued."
    }