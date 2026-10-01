import time

from attendance.sms.sms_service import (
    open_gsm_connection,
    close_gsm_connection,
    get_smart_sim_status,
)


# =====================================================
# DISPLAY VALUE
# =====================================================

def display_value(
    label,
    value
):

    if value is None:

        value = "Not available"

    print(
        f"{label}: {value}"
    )


# =====================================================
# TEST SMART SIM STATUS
# =====================================================

def test_smart_sim_status():

    print()
    print(
        "========================================"
    )

    print(
        "AINHS SMART SIM STATUS TEST"
    )

    print(
        "========================================"
    )

    print()
    print(
        "Detecting SIM800C..."
    )

    # =================================================
    # OPEN GSM CONNECTION
    # =================================================

    gsm, error = open_gsm_connection()

    if not gsm:

        print()
        print(
            "FAILED"
        )

        print(
            f"Reason: {error}"
        )

        print()
        print(
            "Make sure:"
        )

        print(
            "- SIM800C is connected"
        )

        print(
            "- SIM card is inserted"
        )

        print(
            "- GSM network is available"
        )

        print(
            "- SMS worker/runserver is stopped"
        )

        return

    print()
    print(
        "SIM800C connected successfully."
    )

    try:

        # =================================================
        # GET SMART ACCOUNT INFORMATION
        #
        # Automatic path:
        #
        # *123#
        #   ↓
        # 10
        #   ↓
        # 1
        # =================================================

        print()
        print(
            "Checking Smart account status..."
        )

        print(
            "Please wait..."
        )

        status = get_smart_sim_status(
            gsm
        )

        print()
        print(
            "========================================"
        )

        print(
            "SMART SIM STATUS"
        )

        print(
            "========================================"
        )

        # =================================================
        # FAILED
        # =================================================

        if not status.get(
            "success"
        ):

            print()
            print(
                "STATUS CHECK FAILED"
            )

            print()

            display_value(
                "Reason",
                status.get(
                    "error"
                )
            )

            # ---------------------------------------------
            # Balance may still have been retrieved
            # from the first *123# response.
            # ---------------------------------------------

            if (
                status.get(
                    "balance"
                )
                is not None
            ):

                print()

                print(
                    "Partial information:"
                )

                print(
                    f"Regular Load: "
                    f"P{status['balance']:.2f}"
                )

            return

        # =================================================
        # REGULAR LOAD
        # =================================================

        print()
        print(
            "REGULAR LOAD"
        )

        print(
            "----------------------------------------"
        )

        balance = status.get(
            "balance"
        )

        if balance is not None:

            print(
                f"Balance: P{balance:.2f}"
            )

            if balance <= 0:

                print(
                    "Balance Status: NO REGULAR LOAD"
                )

            else:

                print(
                    "Balance Status: AVAILABLE"
                )

        else:

            print(
                "Balance: Not available"
            )

        display_value(
            "Expiration",
            status.get(
                "regular_load_expiration"
            )
        )

        # =================================================
        # SMS / TEXT ALLOCATION
        # =================================================

        print()
        print(
            "SMS / TEXT ALLOCATION"
        )

        print(
            "----------------------------------------"
        )

        daily_texts = status.get(
            "daily_texts"
        )

        display_value(
            "Daily Texts Remaining",
            daily_texts
        )

        display_value(
            "Expiration",
            status.get(
                "daily_texts_expiration"
            )
        )

        if daily_texts is not None:

            if daily_texts <= 0:

                print(
                    "SMS Status: NO TEXTS REMAINING"
                )

            else:

                print(
                    "SMS Status: AVAILABLE"
                )

        # =================================================
        # CALL PROMO
        # =================================================

        print()
        print(
            "CALL ALLOCATION"
        )

        print(
            "----------------------------------------"
        )

        display_value(
            "Promo",
            status.get(
                "call_promo"
            )
        )

        display_value(
            "Expiration",
            status.get(
                "call_expiration"
            )
        )

        # =================================================
        # SUMMARY
        # =================================================

        print()
        print(
            "========================================"
        )

        print(
            "SUMMARY"
        )

        print(
            "========================================"
        )

        print(
            "SIM800C: CONNECTED"
        )

        print(
            "Network: REGISTERED"
        )

        if daily_texts is not None:

            if daily_texts > 0:

                print(
                    f"SMS Allocation: "
                    f"{daily_texts} text(s) available"
                )

            else:

                print(
                    "SMS Allocation: "
                    "NO TEXTS REMAINING"
                )

        else:

            print(
                "SMS Allocation: "
                "UNKNOWN"
            )

        if balance is not None:

            print(
                f"Regular Load: "
                f"P{balance:.2f}"
            )

        else:

            print(
                "Regular Load: UNKNOWN"
            )

        print(
            "========================================"
        )

    except KeyboardInterrupt:

        print()
        print(
            "Test cancelled."
        )

    except Exception as error:

        print()
        print(
            "========================================"
        )

        print(
            "TEST ERROR"
        )

        print(
            "========================================"
        )

        print(
            str(
                error
            )
        )

    finally:

        # =================================================
        # CLOSE GSM CONNECTION
        # =================================================

        print()
        print(
            "Closing SIM800C connection..."
        )

        close_gsm_connection(
            gsm
        )

        time.sleep(
            0.5
        )

        print(
            "Connection closed."
        )


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    test_smart_sim_status()