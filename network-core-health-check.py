"""
Network Health Audit Script
---------------------------
Connects to Cisco IOS-XE Core/Distribution switches (e.g., Catalyst 9600 VSL),
executes health check commands, and sends a summarized report via Email and Webex.

Author: Network Engineering Team
License: MIT
"""

import os
import smtplib
import requests
from email.message import EmailMessage
from dotenv import load_dotenv
from netmiko import ConnectHandler

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION FROM ENVIRONMENT VARIABLES ---
USERNAME = os.getenv('NET_USER')
PASSWORD = os.getenv('NET_PASS')
WEBEX_URL = os.getenv('WEBEX_WEBHOOK_URL')

SMTP_SERVER = os.getenv('MAIL_SERVER')
SMTP_PORT = int(os.getenv('MAIL_PORT', 25))
EMAIL_FROM = os.getenv('MAIL_FROM')
EMAIL_TO = os.getenv('MAIL_TO')

# Switch inventory loaded dynamically or defaulted to target IPs
TARGET_SWITCH_1 = os.getenv('SWITCH_1_IP', '10.251.255.250')
TARGET_SWITCH_2 = os.getenv('SWITCH_2_IP', '10.251.255.251')

SWITCHES = [
    {"device_type": "cisco_xe", "host": TARGET_SWITCH_1},
    {"device_type": "cisco_xe", "host": TARGET_SWITCH_2},
]

# Health Audit Commands for Cisco IOS-XE / Cat9k VSL
COMMANDS = [
    "show etherchannel summary",                            # Port-Channel status
    "show stackwise-virtual",                                # VSL status
    "show stackwise-virtual dual-active-detection",          # Dual-Active Detection status
    "show ip bgp summary",                                   # BGP neighbor states
    "show ip interface brief | exclude administratively",      # Up/Up & Down/Down active ports
    "show processes cpu sorted | ex 0.00",                   # Active CPU load
    "show environment all",                                  # PSU, Fans, and Temps
]


def get_switch_data() -> str:
    """Connects to switches sequentially via Netmiko and runs audit commands."""
    full_output = "Cat 9606R VSL Health & Audit Report\n" + "=" * 45 + "\n"

    for sw in SWITCHES:
        device = {
            "device_type": sw["device_type"],
            "host": sw["host"],
            "username": USERNAME,
            "password": PASSWORD,
            "fast_cli": True,  # Speeds up multiple command execution in Netmiko
        }

        try:
            print(f"Connecting to {sw['host']}...")
            with ConnectHandler(**device) as net_connect:
                # Capture switch hostname from CLI prompt
                hostname = net_connect.find_prompt()[:-1]

                full_output += f"\n{'=' * 15} DEVICE: {hostname} ({sw['host']}) {'=' * 15}\n\n"

                for cmd in COMMANDS:
                    full_output += f"--- [ COMMAND: {cmd} ] ---\n"
                    output = net_connect.send_command(cmd)
                    full_output += f"{output}\n\n"

                full_output += "-" * 50 + "\n"

        except Exception as e:
            full_output += f"\n[!] Error connecting to {sw['host']}: {e}\n"
            full_output += "-" * 50 + "\n"

    return full_output


def send_email(text_content: str) -> None:
    """Dispatches the report via standard SMTP email relay."""
    if not SMTP_SERVER or not EMAIL_TO:
        print("SMTP server or recipient not configured. Skipping email...")
        return

    msg = EmailMessage()
    msg.set_content(text_content)
    msg['Subject'] = "Network Audit: Core Switch Health Check"
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_webex_message(text_content: str) -> None:
    """Posts the health audit report into a Webex Space via Incoming Webhook."""
    if not WEBEX_URL:
        print("Webex Webhook URL not found. Skipping Webex alert...")
        return

    # Webex message limit safety: truncate body if exceeding ~3500 chars
    if len(text_content) > 3500:
        formatted_content = (
            text_content[:3500] 
            + "\n\n... [Report Truncated for Webex. See Email for full output] ..."
        )
    else:
        formatted_content = text_content

    payload = {
        "markdown": f"### 📊 Daily Core Health Audit\n```\n{formatted_content}\n```"
    }

    try:
        response = requests.post(WEBEX_URL, json=payload, timeout=10)
        if response.status_code == 204:
            print("Webex message sent successfully!")
        else:
            print(f"Webex notification failed: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Failed to send Webex message: {e}")


if __name__ == "__main__":
    print("Starting network audit...")

    # 1. Collect diagnostic data from switches
    report = get_switch_data()

    # 2. Dispatch notifications
    send_email(report)
    send_webex_message(report)

    # 3. Output to local terminal/stdout log
    print("\n--- LOCAL REPORT COPY ---\n")
    print(report)
