import os
import sys
import subprocess
import atexit


_sms_process = None


def start_sms_worker():
    """
    Start the SMS worker automatically when
    Django's development server starts.

    RUN_MAIN prevents Django's auto-reloader
    from starting the worker twice.
    """

    global _sms_process

    # =====================================================
    # ONLY START WITH DJANGO RUNSERVER
    # =====================================================

    if "runserver" not in sys.argv:
        return

    # =====================================================
    # DJANGO AUTO-RELOADER PROTECTION
    # =====================================================

    if os.environ.get("RUN_MAIN") != "true":
        return

    # =====================================================
    # ALREADY RUNNING
    # =====================================================

    if (
        _sms_process is not None
        and
        _sms_process.poll() is None
    ):
        return

    print()
    print("================================")
    print("AINHS SMS WORKER")
    print("================================")
    print("Starting automatically...")
    print("================================")

    try:

        _sms_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "attendance.sms.sms_worker",
            ]
        )

        print(
            f"SMS worker started "
            f"(PID {_sms_process.pid})."
        )

    except Exception as error:

        print(
            f"Unable to start SMS worker: "
            f"{error}"
        )


def stop_sms_worker():
    """
    Stop the SMS worker when Django exits.
    """

    global _sms_process

    if _sms_process is None:
        return

    if _sms_process.poll() is not None:
        return

    print()
    print(
        "Stopping SMS worker..."
    )

    try:

        _sms_process.terminate()

        _sms_process.wait(
            timeout=5
        )

    except subprocess.TimeoutExpired:

        _sms_process.kill()

    except Exception as error:

        print(
            f"Error stopping SMS worker: "
            f"{error}"
        )

    finally:

        _sms_process = None


atexit.register(
    stop_sms_worker
)