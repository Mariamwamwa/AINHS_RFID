import serial
import time

from serial.tools import list_ports


# =====================================================
# AINHS GSM AUTO-DETECTION CONFIGURATION
# =====================================================

BAUD_RATE = 9600

GSM_TIMEOUT = 2


# =====================================================
# READ GSM RESPONSE
# =====================================================

def read_response(gsm, timeout=3):

    response = ""

    start_time = time.monotonic()

    while time.monotonic() - start_time < timeout:

        if gsm.in_waiting:

            response += gsm.read(
                gsm.in_waiting
            ).decode(
                "utf-8",
                errors="replace"
            )

            if (
                "\r\nOK\r\n" in response
                or "\r\nERROR\r\n" in response
            ):
                break

        time.sleep(0.05)

    return response


# =====================================================
# DETECT GSM MODULE AUTOMATICALLY
# =====================================================

def detect_gsm():

    print("\n================================")
    print("AINHS GSM AUTO-DETECTION")
    print("================================")

    ports = list(
        list_ports.comports()
    )

    if not ports:

        print(
            "\nNo COM ports detected."
        )

        return None

    print(
        "\nScanning available COM ports..."
    )

    for port in ports:

        print(
            f"\nChecking {port.device} "
            f"({port.description})..."
        )

        try:

            with serial.Serial(
                port=port.device,
                baudrate=BAUD_RATE,
                timeout=GSM_TIMEOUT,
                write_timeout=GSM_TIMEOUT
            ) as gsm:

                time.sleep(0.5)

                # ---------------------------------
                # CLEAR PREVIOUS RESPONSE
                # ---------------------------------

                gsm.reset_input_buffer()

                # ---------------------------------
                # TEST BASIC COMMUNICATION
                # ---------------------------------

                gsm.write(
                    b"AT\r"
                )

                gsm.flush()

                response = read_response(
                    gsm,
                    timeout=2
                )

                if "OK" not in response:

                    print(
                        "No valid GSM response."
                    )

                    continue

                # ---------------------------------
                # IDENTIFY MODULE
                # ---------------------------------

                gsm.reset_input_buffer()

                gsm.write(
                    b"ATI\r"
                )

                gsm.flush()

                info = read_response(
                    gsm,
                    timeout=3
                )

                print(
                    f"Module response:\n{info}"
                )

                if "SIM800" in info.upper():

                    print(
                        "\n================================"
                    )

                    print(
                        "SIM800 GSM MODULE DETECTED!"
                    )

                    print(
                        f"COM PORT: {port.device}"
                    )

                    print(
                        "================================"
                    )

                    return port.device

                print(
                    "Device responded, but it "
                    "was not identified as SIM800."
                )

        except (
            serial.SerialException,
            OSError
        ) as error:

            print(
                f"Cannot access "
                f"{port.device}: "
                f"{error}"
            )

            continue

    print(
        "\nNo compatible SIM800 "
        "module detected."
    )

    return None


# =====================================================
# RUN AUTO-DETECTION TEST
# =====================================================

if __name__ == "__main__":

    detected_port = detect_gsm()

    if detected_port:

        print(
            f"\nGSM ready on "
            f"{detected_port}"
        )

    else:

        print(
            "\nConnect your SIM800C "
            "and try again."
        )