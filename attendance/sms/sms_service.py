import serial
import time
import re

from .gsm_connection import detect_gsm


# =====================================================
# GSM CONFIGURATION
# =====================================================

BAUD_RATE = 9600

SERIAL_TIMEOUT = 2
WRITE_TIMEOUT = 5

COMMAND_TIMEOUT = 10
SMS_TIMEOUT = 60


# =====================================================
# NORMALIZE PHILIPPINE PHONE NUMBER
# =====================================================

def normalize_phone_number(phone_number):

    if not phone_number:

        return None

    phone_number = str(
        phone_number
    ).strip()

    # -------------------------------------------------
    # REMOVE SPACES, DASHES AND PARENTHESES
    #
    # Examples:
    #
    # 0917 123 4567
    # 0917-123-4567
    # (0917) 123 4567
    #
    # becomes:
    #
    # 09171234567
    # -------------------------------------------------

    phone_number = re.sub(
        r"[\s\-\(\)]",
        "",
        phone_number
    )

    # -------------------------------------------------
    # 09171234567
    # becomes
    # +639171234567
    # -------------------------------------------------

    if phone_number.startswith(
        "09"
    ):

        phone_number = (
            "+63"
            +
            phone_number[1:]
        )

    # -------------------------------------------------
    # 639171234567
    # becomes
    # +639171234567
    # -------------------------------------------------

    elif phone_number.startswith(
        "639"
    ):

        phone_number = (
            "+"
            +
            phone_number
        )

    # -------------------------------------------------
    # VALIDATE PHILIPPINE MOBILE NUMBER
    #
    # Required format:
    #
    # +639XXXXXXXXX
    # -------------------------------------------------

    if not re.fullmatch(
        r"\+639\d{9}",
        phone_number
    ):

        return None

    return phone_number


# =====================================================
# READ GSM RESPONSE
# =====================================================

def read_response(
    gsm,
    timeout=COMMAND_TIMEOUT
):

    response = ""

    start_time = time.monotonic()

    while (
        time.monotonic()
        -
        start_time
        <
        timeout
    ):

        try:

            if gsm.in_waiting:

                response += gsm.read(
                    gsm.in_waiting
                ).decode(
                    "utf-8",
                    errors="replace"
                )

                # -------------------------------------
                # STOP WHEN GSM RETURNS FINAL RESPONSE
                # -------------------------------------

                if (
                    "\r\nOK\r\n"
                    in response

                    or

                    "\r\nERROR\r\n"
                    in response

                    or

                    "+CMS ERROR:"
                    in response

                    or

                    "+CME ERROR:"
                    in response
                ):

                    break

        except (
            serial.SerialException,
            OSError
        ):

            break

        time.sleep(
            0.1
        )

    return response


# =====================================================
# SEND AT COMMAND
# =====================================================

def send_command(
    gsm,
    command,
    timeout=COMMAND_TIMEOUT
):

    try:

        # -------------------------------------------------
        # CLEAR PREVIOUS RESPONSE
        # -------------------------------------------------

        gsm.reset_input_buffer()

        # -------------------------------------------------
        # SEND COMMAND
        # -------------------------------------------------

        gsm.write(
            (
                command
                +
                "\r"
            ).encode(
                "ascii"
            )
        )

        gsm.flush()

        # -------------------------------------------------
        # READ RESPONSE
        # -------------------------------------------------

        response = read_response(
            gsm,
            timeout
        )

        return response

    except (
        serial.SerialException,
        OSError
    ):

        return ""


# =====================================================
# CHECK GSM MODULE
# =====================================================

def check_gsm(gsm):

    # =================================================
    # CHECK MODULE RESPONSE
    # =================================================

    response = send_command(
        gsm,
        "AT"
    )

    if "OK" not in response:

        return (
            False,
            "GSM module is not responding."
        )

    # =================================================
    # CHECK SIM CARD
    # =================================================

    response = send_command(
        gsm,
        "AT+CPIN?"
    )

    if "+CPIN: READY" not in response:

        return (
            False,
            "SIM card is not ready."
        )

    # =================================================
    # CHECK NETWORK REGISTRATION
    #
    # 1 = registered home network
    # 5 = registered roaming
    # =================================================

    response = send_command(
        gsm,
        "AT+CREG?"
    )

    if not re.search(
        r"\+CREG:\s*\d+,\s*[15]\b",
        response
    ):

        return (
            False,
            "GSM network is not registered."
        )

    return (
        True,
        None
    )


# =====================================================
# OPEN GSM CONNECTION
# =====================================================

def open_gsm_connection():

    # =================================================
    # FIND SIM800C
    # =================================================

    detected_port = detect_gsm()

    if not detected_port:

        return (
            None,
            "SIM800C module not detected."
        )

    try:

        # =================================================
        # OPEN SERIAL CONNECTION
        # =================================================

        gsm = serial.Serial(
            port=detected_port,
            baudrate=BAUD_RATE,
            timeout=SERIAL_TIMEOUT,
            write_timeout=WRITE_TIMEOUT
        )

        # Give SIM800C time to settle
        time.sleep(
            1
        )

        # =================================================
        # CHECK MODULE / SIM / NETWORK
        # =================================================

        ready, error = check_gsm(
            gsm
        )

        if not ready:

            gsm.close()

            return (
                None,
                error
            )

        # =================================================
        # CONNECTION READY
        # =================================================

        return (
            gsm,
            None
        )

    except (
        serial.SerialException,
        OSError
    ) as error:

        return (
            None,
            str(error)
        )


# =====================================================
# SEND ONE SMS
#
# IMPORTANT:
# This function expects an ALREADY OPEN GSM connection.
#
# This allows the SMS worker to:
#
# Open GSM once
#     ↓
# Send Student A
#     ↓
# Send Student B
#     ↓
# Send Student C
#     ↓
# Close GSM
#
# instead of reopening the COM port for every SMS.
# =====================================================
# =====================================================
# READ USSD RESPONSE
# =====================================================

def read_ussd_response(
    gsm,
    timeout=45
):

    response = ""

    start_time = time.monotonic()

    while (
        time.monotonic() - start_time
        < timeout
    ):

        try:

            if gsm.in_waiting:

                data = gsm.read(
                    gsm.in_waiting
                )

                response += data.decode(
                    "utf-8",
                    errors="replace"
                )

                # -------------------------------------
                # USSD RESPONSE RECEIVED
                # -------------------------------------

                if "+CUSD:" in response:

                    # Give the module a little time
                    # to finish sending the response.

                    time.sleep(0.5)

                    if gsm.in_waiting:

                        response += gsm.read(
                            gsm.in_waiting
                        ).decode(
                            "utf-8",
                            errors="replace"
                        )

                    break

                # -------------------------------------
                # GSM ERROR
                # -------------------------------------

                if (
                    "+CME ERROR:" in response
                    or
                    "+CMS ERROR:" in response
                    or
                    "\r\nERROR\r\n" in response
                ):

                    break

        except (
            serial.SerialException,
            OSError
        ):

            break

        time.sleep(
            0.1
        )

    return response


# =====================================================
# SEND USSD REQUEST
# =====================================================

def send_ussd(
    gsm,
    value,
    timeout=45
):

    try:

        # ---------------------------------------------
        # CLEAR PREVIOUS DATA
        # ---------------------------------------------

        gsm.reset_input_buffer()

        # ---------------------------------------------
        # SEND USSD
        # ---------------------------------------------

        command = (
            f'AT+CUSD=1,"{value}",15\r'
        )

        gsm.write(
            command.encode(
                "ascii"
            )
        )

        gsm.flush()

        # ---------------------------------------------
        # WAIT FOR +CUSD RESPONSE
        # ---------------------------------------------

        response = read_ussd_response(
            gsm,
            timeout=timeout
        )

        if "+CUSD:" not in response:

            return (
                False,
                response.strip()
                or
                "No USSD response received."
            )

        return (
            True,
            response
        )

    except (
        serial.SerialException,
        OSError
    ) as error:

        return (
            False,
            str(error)
        )


# =====================================================
# CANCEL USSD SESSION
# =====================================================

def cancel_ussd(
    gsm
):

    try:

        gsm.write(
            b"AT+CUSD=2\r"
        )

        gsm.flush()

        time.sleep(
            0.5
        )

        if gsm.in_waiting:

            gsm.read(
                gsm.in_waiting
            )

    except (
        serial.SerialException,
        OSError
    ):

        pass


# =====================================================
# EXTRACT TEXT FROM +CUSD RESPONSE
# =====================================================

def extract_ussd_text(
    response
):

    if not response:

        return ""

    match = re.search(
        r'\+CUSD:\s*\d+,"(.*?)"\s*,\s*\d+',
        response,
        re.DOTALL
    )

    if not match:

        return ""

    return match.group(
        1
    ).strip()


# =====================================================
# PARSE SMART MAIN BALANCE
#
# Example:
#
# BAL: P7.50
# =====================================================

def parse_smart_main_balance(
    response
):

    text = extract_ussd_text(
        response
    )

    match = re.search(
        r"BAL:\s*P\s*([0-9]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE
    )

    if not match:

        return None

    try:

        return float(
            match.group(1)
        )

    except ValueError:

        return None


# =====================================================
# PARSE SMART ACCOUNT STATUS
#
# Actual Smart response:
#
# Daily Texts: 94 Exp: 02Oct2026 12:00AM
# Unli Trinet Calls Exp: 03Oct2026 09:50AM
# Regular Load: P7.50 Exp: 19Sep2027 07:49AM
# =====================================================

def parse_smart_account_status(
    response
):

    text = extract_ussd_text(
        response
    )

    result = {

        "daily_texts": None,
        "daily_texts_expiration": None,

        "call_promo": None,
        "call_expiration": None,

        "regular_load": None,
        "regular_load_expiration": None,

        "raw_status": text,

    }

    # =================================================
    # DAILY TEXTS
    # =================================================

    texts_match = re.search(
        r"Daily\s+Texts:\s*(\d+)"
        r"\s+Exp:\s*"
        r"([0-9]{1,2}[A-Za-z]{3}[0-9]{4}"
        r"\s+[0-9]{1,2}:[0-9]{2}(?:AM|PM))",
        text,
        re.IGNORECASE
    )

    if texts_match:

        try:

            result[
                "daily_texts"
            ] = int(
                texts_match.group(1)
            )

        except ValueError:

            pass

        result[
            "daily_texts_expiration"
        ] = texts_match.group(
            2
        ).strip()

    # =================================================
    # REGULAR LOAD
    # =================================================

    load_match = re.search(
        r"Regular\s+Load:\s*P\s*"
        r"([0-9]+(?:\.[0-9]+)?)"
        r"\s+Exp:\s*"
        r"([0-9]{1,2}[A-Za-z]{3}[0-9]{4}"
        r"\s+[0-9]{1,2}:[0-9]{2}(?:AM|PM))",
        text,
        re.IGNORECASE
    )

    if load_match:

        try:

            result[
                "regular_load"
            ] = float(
                load_match.group(1)
            )

        except ValueError:

            pass

        result[
            "regular_load_expiration"
        ] = load_match.group(
            2
        ).strip()

    # =================================================
    # CALL PROMO
    #
    # Keep this flexible because Smart may rename
    # the active call allocation/promo.
    # =================================================

    call_match = re.search(
        r"([^\r\n]*Calls[^\r\n]*?)"
        r"\s+Exp:\s*"
        r"([0-9]{1,2}[A-Za-z]{3}[0-9]{4}"
        r"\s+[0-9]{1,2}:[0-9]{2}(?:AM|PM))",
        text,
        re.IGNORECASE
    )

    if call_match:

        result[
            "call_promo"
        ] = call_match.group(
            1
        ).strip()

        result[
            "call_expiration"
        ] = call_match.group(
            2
        ).strip()

    return result


# =====================================================
# GET SMART SIM STATUS
#
# Smart menu path discovered from the actual SIM:
#
# *123#
#   ↓
# 10
#   ↓
# 1
#
# Returns:
#
# {
#     "success": True,
#     "balance": 7.50,
#     "daily_texts": 94,
#     "daily_texts_expiration": "...",
#     "call_promo": "...",
#     "call_expiration": "...",
#     "regular_load": 7.50,
#     "regular_load_expiration": "...",
# }
# =====================================================

def get_smart_sim_status(
    gsm
):

    result = {

        "success": False,

        "balance": None,

        "daily_texts": None,
        "daily_texts_expiration": None,

        "call_promo": None,
        "call_expiration": None,

        "regular_load": None,
        "regular_load_expiration": None,

        "error": None,

    }

    try:

        # =================================================
        # MAKE SURE GSM IS READY
        # =================================================

        ready, error = check_gsm(
            gsm
        )

        if not ready:

            result[
                "error"
            ] = error

            return result

        # =================================================
        # CANCEL ANY OLD USSD SESSION
        # =================================================

        cancel_ussd(
            gsm
        )

        time.sleep(
            0.5
        )

        # =================================================
        # STEP 1
        #
        # *123#
        #
        # This gives us the immediate BAL value.
        # =================================================

        success, response = send_ussd(
            gsm,
            "*123#"
        )

        if not success:

            result[
                "error"
            ] = (
                "Unable to open Smart "
                f"*123#: {response}"
            )

            return result

        result[
            "balance"
        ] = parse_smart_main_balance(
            response
        )

        # =================================================
        # STEP 2
        #
        # 10 = WAISHACKS
        # =================================================

        success, response = send_ussd(
            gsm,
            "10"
        )

        if not success:

            result[
                "error"
            ] = (
                "Unable to open Smart "
                f"balance services: {response}"
            )

            return result

        menu_text = extract_ussd_text(
            response
        )

        # Safety check.
        #
        # We expect the read-only menu discovered
        # during testing:
        #
        # 1) Balance
        # 2) Manage Auto-Renew
        # ...

        if (
            "Balance"
            not in menu_text
        ):

            result[
                "error"
            ] = (
                "Smart USSD menu changed. "
                "Balance option was not found."
            )

            return result

        # =================================================
        # STEP 3
        #
        # 1 = Balance
        # =================================================

        success, response = send_ussd(
            gsm,
            "1"
        )

        if not success:

            result[
                "error"
            ] = (
                "Unable to retrieve Smart "
                f"account status: {response}"
            )

            return result

        account_status = (
            parse_smart_account_status(
                response
            )
        )

        # =================================================
        # COPY PARSED VALUES
        # =================================================

        result[
            "daily_texts"
        ] = account_status.get(
            "daily_texts"
        )

        result[
            "daily_texts_expiration"
        ] = account_status.get(
            "daily_texts_expiration"
        )

        result[
            "call_promo"
        ] = account_status.get(
            "call_promo"
        )

        result[
            "call_expiration"
        ] = account_status.get(
            "call_expiration"
        )

        result[
            "regular_load"
        ] = account_status.get(
            "regular_load"
        )

        result[
            "regular_load_expiration"
        ] = account_status.get(
            "regular_load_expiration"
        )

        # Prefer the detailed Regular Load value
        # if Smart returned it.

        if (
            result[
                "regular_load"
            ]
            is not None
        ):

            result[
                "balance"
            ] = result[
                "regular_load"
            ]

        # =================================================
        # SUCCESS
        # =================================================

        result[
            "success"
        ] = True

        return result

    except Exception as error:

        result[
            "error"
        ] = str(
            error
        )

        return result

    finally:

        # Always close the Smart USSD session.
        #
        # IMPORTANT:
        # This does NOT close the serial connection.
        # The SMS worker can continue using the
        # same SIM800C connection afterward.

        cancel_ussd(
            gsm
        )
def send_sms_with_connection(
    gsm,
    phone_number,
    message
):

    # =================================================
    # VALIDATE / NORMALIZE PHONE NUMBER
    # =================================================

    phone_number = normalize_phone_number(
        phone_number
    )

    if not phone_number:

        return (
            False,
            "Invalid Philippine mobile number."
        )

    # =================================================
    # ENABLE SMS TEXT MODE
    # =================================================

    response = send_command(
        gsm,
        "AT+CMGF=1"
    )

    if "OK" not in response:

        return (
            False,
            "Unable to enable SMS text mode."
        )

    try:

        # =================================================
        # CLEAR OLD GSM RESPONSE
        # =================================================

        gsm.reset_input_buffer()

        # =================================================
        # SET SMS RECIPIENT
        # =================================================

        command = (
            f'AT+CMGS="{phone_number}"'
        )

        gsm.write(
            (
                command
                +
                "\r"
            ).encode(
                "ascii"
            )
        )

        gsm.flush()

        # =================================================
        # WAIT FOR GSM MESSAGE PROMPT
        #
        # SIM800C should respond with:
        #
        # >
        # =================================================

        prompt = ""

        start_time = time.monotonic()

        while (
            time.monotonic()
            -
            start_time
            <
            10
        ):

            try:

                if gsm.in_waiting:

                    prompt += gsm.read(
                        gsm.in_waiting
                    ).decode(
                        "utf-8",
                        errors="replace"
                    )

                    # -------------------------------------
                    # READY FOR MESSAGE
                    # -------------------------------------

                    if ">" in prompt:

                        break

                    # -------------------------------------
                    # GSM ERROR
                    # -------------------------------------

                    if (
                        "ERROR"
                        in prompt

                        or

                        "+CMS ERROR:"
                        in prompt

                        or

                        "+CME ERROR:"
                        in prompt
                    ):

                        return (
                            False,
                            prompt.strip()
                        )

            except (
                serial.SerialException,
                OSError
            ) as error:

                return (
                    False,
                    str(error)
                )

            time.sleep(
                0.1
            )

        # =================================================
        # GSM NEVER GAVE MESSAGE PROMPT
        # =================================================

        if ">" not in prompt:

            return (
                False,
                "No SMS prompt received."
            )

        # =================================================
        # SEND MESSAGE
        # =================================================

        gsm.write(
            message.encode(
                "ascii",
                errors="replace"
            )
        )

        # =================================================
        # CTRL + Z
        #
        # Tells SIM800C to submit/send the SMS.
        # =================================================

        gsm.write(
            b"\x1A"
        )

        gsm.flush()

        # =================================================
        # WAIT FOR MOBILE NETWORK RESPONSE
        # =================================================

        response = read_response(
            gsm,
            timeout=SMS_TIMEOUT
        )

        # =================================================
        # SUCCESS RESPONSE
        #
        # Usually:
        #
        # +CMGS: 123
        # OK
        # =================================================

        if (
            re.search(
                r"\+CMGS:\s*\d+",
                response
            )

            and

            re.search(
                r"\bOK\b",
                response
            )
        ):

            return (
                True,
                None
            )

        # =================================================
        # GSM RETURNED SOMETHING BUT SMS FAILED
        # =================================================

        if response.strip():

            return (
                False,
                response.strip()
            )

        # =================================================
        # NO RESPONSE / TIMEOUT
        # =================================================

        return (
            False,
            "SMS sending timed out."
        )

    except (
        serial.SerialException,
        OSError
    ) as error:

        return (
            False,
            str(error)
        )


# =====================================================
# CLOSE GSM CONNECTION
# =====================================================

def close_gsm_connection(gsm):

    if not gsm:

        return

    try:

        if gsm.is_open:

            gsm.close()

    except (
        serial.SerialException,
        OSError
    ):

        pass    