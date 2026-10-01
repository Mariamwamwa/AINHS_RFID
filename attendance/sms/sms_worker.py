import os
import time
import django


# =========================================================
# DJANGO SETUP
# =========================================================

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "AINHS.settings"
)

django.setup()


# =========================================================
# IMPORTS AFTER DJANGO SETUP
# =========================================================

from django.utils import timezone

from attendance.models import (
    SMSQueue,
    SystemNotification,
)

from attendance.sms.sms_service import (
    open_gsm_connection,
    send_sms_with_connection,
    close_gsm_connection,
    check_gsm,
    get_smart_sim_status,
)


# =========================================================
# WORKER CONFIGURATION
# =========================================================

# How often the worker loops while GSM is connected.
WORKER_CHECK_DELAY = 3

# How long to wait before trying to reconnect a missing
# or disconnected SIM800C.
GSM_RETRY_DELAY = 10

# Delay between individual SMS messages.
BETWEEN_SMS_DELAY = 1


# =========================================================
# CLEAN OLD SMS RECORDS
# =========================================================

def clean_old_sms_records():

    today = timezone.localdate()

    deleted_count, _ = (
        SMSQueue.objects.filter(
            attendance__date__lt=today
        ).delete()
    )

    if deleted_count:

        print(
            f"Removed {deleted_count} "
            f"old SMS queue record(s)."
        )


# =========================================================
# RESET INTERRUPTED SMS
# =========================================================

def reset_sending_messages():

    updated = (
        SMSQueue.objects.filter(
            status="SENDING"
        ).update(
            status="PENDING"
        )
    )

    if updated:

        print(
            f"Reset {updated} interrupted "
            f"SMS message(s) to PENDING."
        )


# =========================================================
# GET PENDING SMS
# =========================================================

def get_pending_messages():

    today = timezone.localdate()

    return list(
        SMSQueue.objects.filter(
            status="PENDING",
            attendance__date=today
        )
        .select_related(
            "student",
            "attendance"
        )
        .order_by(
            "created_at"
        )
    )


# =========================================================
# CREATE SMS FAILED NOTIFICATION
# =========================================================

def create_sms_failed_notification(
    sms,
    error
):

    error_message = (
        error
        or
        "Unknown SMS error."
    )

    notification, created = (
        SystemNotification.objects.get_or_create(
            sms_queue=sms,
            notification_type="SMS_FAILED",
            defaults={
                "student": sms.student,
                "title": "SMS Failed",
                "message": (
                    "Parent notification could not "
                    "be sent.\n"
                    f"Reason: {error_message}"
                ),
                "superadmin_only": False,
            }
        )
    )

    if created:

        print(
            f"Created SMS failure notification "
            f"for SMS #{sms.id}."
        )

    else:

        print(
            f"SMS failure notification for "
            f"SMS #{sms.id} already exists."
        )


# =========================================================
# CREATE GSM DISCONNECTED NOTIFICATION
# =========================================================

def create_gsm_disconnected_notification(
    error=None,
    startup=False
):

    if startup:

        message = (
            "SIM800C was not available when the "
            "AINHS SMS worker started."
        )

    else:

        message = (
            "The SIM800C connection was lost."
        )

    if error:

        message += (
            f"\nReason: {error}"
        )

    SystemNotification.objects.create(
        notification_type="GSM_DISCONNECTED",
        title="GSM Disconnected",
        message=message,
        superadmin_only=True,
    )

    print(
        "Created Super Admin GSM disconnected "
        "notification."
    )


# =========================================================
# CREATE GSM CONNECTED NOTIFICATION
# =========================================================

def create_gsm_connected_notification(
    smart_status=None
):

    message_lines = [
        "SIM800C has been connected again.",
        "Network: Registered",
    ]

    if (
        smart_status
        and smart_status.get("success")
    ):

        daily_texts = smart_status.get(
            "daily_texts"
        )

        text_expiration = smart_status.get(
            "daily_texts_expiration"
        )

        balance = smart_status.get(
            "balance"
        )

        load_expiration = smart_status.get(
            "regular_load_expiration"
        )

        if daily_texts is not None:

            message_lines.append(
                f"Daily Texts Remaining: "
                f"{daily_texts}"
            )

        if text_expiration:

            message_lines.append(
                f"Text Expiration: "
                f"{text_expiration}"
            )

        if balance is not None:

            message_lines.append(
                f"Regular Load: "
                f"P{balance:.2f}"
            )

        if load_expiration:

            message_lines.append(
                f"Load Expiration: "
                f"{load_expiration}"
            )

    elif smart_status:

        error = smart_status.get(
            "error"
        )

        if error:

            message_lines.append(
                f"Smart status check: {error}"
            )

    SystemNotification.objects.create(
        notification_type="GSM_CONNECTED",
        title="GSM Connected",
        message="\n".join(
            message_lines
        ),
        superadmin_only=True,
    )

    print(
        "Created Super Admin GSM connected "
        "notification."
    )


# =========================================================
# CREATE STARTUP SMART SIM STATUS NOTIFICATION
# =========================================================

def create_sim_status_notification(
    smart_status
):

    # =====================================================
    # SMART STATUS FAILED
    # =====================================================

    if not smart_status.get(
        "success"
    ):

        error = (
            smart_status.get(
                "error"
            )
            or
            "Smart account status could not be checked."
        )

        balance = smart_status.get(
            "balance"
        )

        message_lines = [
            "SIM800C: Connected",
            "Network: Registered",
            "",
            "Smart account status could not be "
            "fully retrieved.",
            f"Reason: {error}",
        ]

        if balance is not None:

            message_lines.extend(
                [
                    "",
                    f"Regular Load: "
                    f"P{balance:.2f}",
                ]
            )

        SystemNotification.objects.create(
            notification_type="SIM_STATUS",
            title="Smart SIM Status",
            message="\n".join(
                message_lines
            ),
            superadmin_only=True,
        )

        print(
            "Created Super Admin SIM status "
            "notification."
        )

        return

    # =====================================================
    # VALUES
    # =====================================================

    daily_texts = smart_status.get(
        "daily_texts"
    )

    text_expiration = smart_status.get(
        "daily_texts_expiration"
    )

    balance = smart_status.get(
        "balance"
    )

    load_expiration = smart_status.get(
        "regular_load_expiration"
    )

    call_promo = smart_status.get(
        "call_promo"
    )

    call_expiration = smart_status.get(
        "call_expiration"
    )

    # =====================================================
    # BUILD MESSAGE
    # =====================================================

    message_lines = [
        "SIM800C: Connected",
        "Network: Registered",
    ]

    # -----------------------------------------------------
    # TEXT ALLOCATION
    # -----------------------------------------------------

    if daily_texts is not None:

        message_lines.extend(
            [
                "",
                f"Daily Texts Remaining: "
                f"{daily_texts}",
            ]
        )

        if daily_texts <= 0:

            message_lines.append(
                "SMS Status: No texts remaining"
            )

        else:

            message_lines.append(
                "SMS Status: Available"
            )

    if text_expiration:

        message_lines.append(
            f"Text Expiration: "
            f"{text_expiration}"
        )

    # -----------------------------------------------------
    # REGULAR LOAD
    # -----------------------------------------------------

    if balance is not None:

        message_lines.extend(
            [
                "",
                f"Regular Load: "
                f"P{balance:.2f}",
            ]
        )

    if load_expiration:

        message_lines.append(
            f"Load Expiration: "
            f"{load_expiration}"
        )

    # -----------------------------------------------------
    # CALL PROMO
    # -----------------------------------------------------

    if call_promo:

        message_lines.extend(
            [
                "",
                f"Call Promo: "
                f"{call_promo}",
            ]
        )

    if call_expiration:

        message_lines.append(
            f"Call Expiration: "
            f"{call_expiration}"
        )

    # =====================================================
    # CREATE NOTIFICATION
    # =====================================================

    SystemNotification.objects.create(
        notification_type="SIM_STATUS",
        title="Smart SIM Status",
        message="\n".join(
            message_lines
        ),
        superadmin_only=True,
    )

    print(
        "Created Super Admin Smart SIM status "
        "notification."
    )


# =========================================================
# CHECK SMART SIM STATUS
# =========================================================

def check_smart_status(
    gsm
):

    print()

    print(
        "Checking Smart SIM status..."
    )

    try:

        smart_status = (
            get_smart_sim_status(
                gsm
            )
        )

    except Exception as error:

        smart_status = {
            "success": False,
            "error": str(error),
        }

    if smart_status.get(
        "success"
    ):

        print(
            "Smart SIM status retrieved."
        )

        daily_texts = smart_status.get(
            "daily_texts"
        )

        balance = smart_status.get(
            "balance"
        )

        if daily_texts is not None:

            print(
                f"Daily texts remaining: "
                f"{daily_texts}"
            )

        if balance is not None:

            print(
                f"Regular load: "
                f"P{balance:.2f}"
            )

    else:

        print(
            "Smart SIM status check failed."
        )

        print(
            f"Reason: "
            f"{smart_status.get('error')}"
        )

    return smart_status


# =========================================================
# PROCESS ONE SMS
# =========================================================

def process_sms(
    gsm,
    sms
):

    # Get latest status from database.
    sms.refresh_from_db()

    # =====================================================
    # SKIP IF NO LONGER PENDING
    # =====================================================

    if sms.status != "PENDING":

        return {
            "success": True,
            "error": None,
        }

    print()

    print(
        "--------------------------------"
    )

    print(
        f"SMS ID: {sms.id}"
    )

    print(
        f"Student: "
        f"{sms.student.full_name}"
    )

    print(
        f"Number: "
        f"{sms.phone_number}"
    )

    print(
        f"Attendance: "
        f"{sms.get_attendance_type_display()}"
    )

    print(
        f"Original Time: "
        f"{sms.attendance_time.strftime('%I:%M %p')}"
    )

    # =====================================================
    # MARK AS SENDING
    # =====================================================

    sms.status = "SENDING"

    sms.save(
        update_fields=[
            "status"
        ]
    )

    # =====================================================
    # SEND SMS
    # =====================================================

    try:

        success, error = (
            send_sms_with_connection(
                gsm=gsm,
                phone_number=sms.phone_number,
                message=sms.message
            )
        )

    except Exception as exception:

        success = False
        error = str(exception)

    sms.attempts += 1

    # =====================================================
    # SUCCESS
    # =====================================================

    if success:

        sms.status = "SENT"

        sms.sent_at = (
            timezone.now()
        )

        sms.last_error = None

        sms.save(
            update_fields=[
                "status",
                "attempts",
                "sent_at",
                "last_error",
            ]
        )

        print(
            f"SMS #{sms.id} SENT."
        )

        return {
            "success": True,
            "error": None,
        }

    # =====================================================
    # FAILED
    #
    # IMPORTANT:
    #
    # We do NOT create SMS_FAILED here yet.
    #
    # The worker must first determine whether this was:
    #
    # 1. A GSM/hardware/network failure
    #
    # OR
    #
    # 2. An SMS-specific failure.
    # =====================================================

    sms.status = "PENDING"

    sms.last_error = (
        error
        or
        "Unknown SMS error."
    )

    sms.save(
        update_fields=[
            "status",
            "attempts",
            "last_error",
        ]
    )

    print(
        f"SMS #{sms.id} FAILED."
    )

    print(
        f"Reason: "
        f"{sms.last_error}"
    )

    return {
        "success": False,
        "error": sms.last_error,
    }


# =========================================================
# MAIN WORKER
# =========================================================

def run_worker():

    print()

    print(
        "================================"
    )

    print(
        "AINHS SMS WORKER"
    )

    print(
        "================================"
    )

    print(
        "Worker started."
    )

    print(
        "Continuous SIM800C monitoring enabled."
    )

    print(
        "Smart SIM startup status enabled."
    )

    print(
        "Persistent GSM connection enabled."
    )

    print(
        "Press CTRL+C to stop."
    )

    print(
        "================================"
    )

    # =====================================================
    # INITIAL DATABASE CLEANUP
    # =====================================================

    reset_sending_messages()

    clean_old_sms_records()

    # =====================================================
    # WORKER STATE
    # =====================================================

    gsm = None

    # None:
    #     Worker has not determined hardware state yet.
    #
    # True:
    #     SIM800C is currently connected.
    #
    # False:
    #     SIM800C is currently disconnected.
    gsm_connected_state = None

    # We only perform the special startup SIM status
    # notification once per worker run.
    startup_check_complete = False

    try:

        while True:

            # =================================================
            # NO ACTIVE GSM CONNECTION
            # =================================================

            if gsm is None:

                print()

                print(
                    "Checking for SIM800C..."
                )

                gsm, error = (
                    open_gsm_connection()
                )

                # =============================================
                # STILL DISCONNECTED
                # =============================================

                if gsm is None:

                    print(
                        f"SIM800C unavailable: "
                        f"{error}"
                    )

                    # -----------------------------------------
                    # FIRST CHECK AFTER WORKER START
                    # -----------------------------------------

                    if (
                        gsm_connected_state
                        is None
                    ):

                        create_gsm_disconnected_notification(
                            error=error,
                            startup=True
                        )

                        gsm_connected_state = False
                        startup_check_complete = True

                    # -----------------------------------------
                    # CONNECTED -> DISCONNECTED TRANSITION
                    # -----------------------------------------

                    elif (
                        gsm_connected_state
                        is True
                    ):

                        create_gsm_disconnected_notification(
                            error=error,
                            startup=False
                        )

                        gsm_connected_state = False

                    # -----------------------------------------
                    # ALREADY DISCONNECTED
                    #
                    # Do NOT create another notification.
                    # -----------------------------------------

                    else:

                        print(
                            "SIM800C is still disconnected. "
                            "No duplicate notification created."
                        )

                    time.sleep(
                        GSM_RETRY_DELAY
                    )

                    continue

                # =============================================
                # CONNECTION SUCCESSFUL
                # =============================================

                print(
                    "SIM800C connected."
                )

                # ---------------------------------------------
                # STARTUP CONNECTION
                # ---------------------------------------------

                if (
                    gsm_connected_state
                    is None
                ):

                    gsm_connected_state = True

                    # We intentionally create ONLY the
                    # Smart SIM Status notification here.
                    #
                    # We do NOT also create GSM_CONNECTED,
                    # otherwise startup would produce two
                    # notifications.

                    smart_status = (
                        check_smart_status(
                            gsm
                        )
                    )

                    create_sim_status_notification(
                        smart_status
                    )

                    startup_check_complete = True

                # ---------------------------------------------
                # DISCONNECTED -> CONNECTED TRANSITION
                # ---------------------------------------------

                elif (
                    gsm_connected_state
                    is False
                ):

                    gsm_connected_state = True

                    # Recheck Smart balance/text allocation
                    # whenever the hardware comes back.

                    smart_status = (
                        check_smart_status(
                            gsm
                        )
                    )

                    create_gsm_connected_notification(
                        smart_status
                    )

                # ---------------------------------------------
                # ALREADY CONNECTED
                # ---------------------------------------------

                else:

                    gsm_connected_state = True

            # =================================================
            # VERIFY CURRENT GSM CONNECTION
            #
            # This happens EVEN WHEN THERE ARE NO PENDING SMS.
            # =================================================

            ready, gsm_error = (
                check_gsm(
                    gsm
                )
            )

            # =================================================
            # CONNECTION LOST
            # =================================================

            if not ready:

                print()

                print(
                    "SIM800C connection lost."
                )

                print(
                    f"Reason: "
                    f"{gsm_error}"
                )

                # ---------------------------------------------
                # CREATE NOTIFICATION ONLY ON STATE CHANGE
                # ---------------------------------------------

                if (
                    gsm_connected_state
                    is not False
                ):

                    create_gsm_disconnected_notification(
                        error=gsm_error,
                        startup=False
                    )

                gsm_connected_state = False

                # ---------------------------------------------
                # RELEASE BROKEN SERIAL CONNECTION
                # ---------------------------------------------

                close_gsm_connection(
                    gsm
                )

                gsm = None

                time.sleep(
                    GSM_RETRY_DELAY
                )

                continue

            # =================================================
            # GSM HEALTHY
            # =================================================

            gsm_connected_state = True

            # =================================================
            # CHECK SMS QUEUE
            # =================================================

            pending_messages = (
                get_pending_messages()
            )

            # =================================================
            # NOTHING PENDING
            #
            # IMPORTANT:
            #
            # We still reached check_gsm() above.
            # Therefore the hardware continues being monitored.
            # =================================================

            if not pending_messages:

                time.sleep(
                    WORKER_CHECK_DELAY
                )

                continue

            print()

            print(
                "================================"
            )

            print(
                f"PENDING SMS: "
                f"{len(pending_messages)}"
            )

            print(
                "================================"
            )

            # =================================================
            # PROCESS QUEUE SEQUENTIALLY
            # =================================================

            connection_lost = False

            for sms in pending_messages:

                result = (
                    process_sms(
                        gsm,
                        sms
                    )
                )

                # =============================================
                # SMS SUCCESS
                # =============================================

                if result["success"]:

                    time.sleep(
                        BETWEEN_SMS_DELAY
                    )

                    continue

                # =============================================
                # SMS SEND FAILED
                #
                # Determine whether GSM itself failed.
                # =============================================

                ready, gsm_error = (
                    check_gsm(
                        gsm
                    )
                )

                # =============================================
                # GSM / HARDWARE / NETWORK FAILURE
                # =============================================

                if not ready:

                    print()

                    print(
                        "SMS failure was caused by "
                        "SIM800C/network connection loss."
                    )

                    print(
                        f"Reason: "
                        f"{gsm_error}"
                    )

                    # -----------------------------------------
                    # IMPORTANT:
                    #
                    # Do NOT create SMS_FAILED.
                    #
                    # The SMS remains PENDING and will be
                    # retried after the SIM800C reconnects.
                    # -----------------------------------------

                    if (
                        gsm_connected_state
                        is not False
                    ):

                        create_gsm_disconnected_notification(
                            error=gsm_error,
                            startup=False
                        )

                    gsm_connected_state = False

                    close_gsm_connection(
                        gsm
                    )

                    gsm = None

                    connection_lost = True

                    break

                # =============================================
                # GSM IS HEALTHY
                #
                # Therefore this is an SMS-specific failure.
                # =============================================

                print(
                    "SIM800C is still healthy."
                )

                print(
                    "Creating SMS-specific failure "
                    "notification."
                )

                create_sms_failed_notification(
                    sms=sms,
                    error=result["error"]
                )

                # Stop this batch so we do not repeatedly
                # attempt the same failing message immediately.
                break

            # =================================================
            # CONNECTION WAS LOST DURING SMS
            # =================================================

            if connection_lost:

                time.sleep(
                    GSM_RETRY_DELAY
                )

                continue

            # =================================================
            # WAIT BEFORE NEXT WORKER LOOP
            # =================================================

            time.sleep(
                WORKER_CHECK_DELAY
            )

    # =====================================================
    # CTRL+C
    # =====================================================

    except KeyboardInterrupt:

        print()

        print(
            "Stopping SMS worker..."
        )

    # =====================================================
    # UNEXPECTED WORKER ERROR
    # =====================================================

    except Exception as error:

        print()

        print(
            "SMS WORKER ERROR"
        )

        print(
            str(error)
        )

        raise

    # =====================================================
    # ALWAYS CLEAN UP
    # =====================================================

    finally:

        if gsm is not None:

            close_gsm_connection(
                gsm
            )

            print(
                "SIM800C connection closed."
            )

        print()

        print(
            "================================"
        )

        print(
            "AINHS SMS WORKER STOPPED"
        )

        print(
            "================================"
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    run_worker()