import os
import re
import smtplib

from dotenv import load_dotenv
from tavily import TavilyClient
from email.message import EmailMessage


def get_user_info(name: str) -> str:
    return f"The user's name is {name}."


def search_web(query: str):
    load_dotenv()

    client = TavilyClient(
        api_key=os.getenv("TAVILY_API_KEY")
    )

    response = client.search(
        query=query,
        max_results=5,
    )

    return response

def send_slack_message(message: str):
    return f"Slack message sent: {message}"


def _email_status(success: bool, message: str, recipient: str | None = None, subject: str | None = None):
    status = {
        "success": success,
        "tool": "send_email",
        "message": message,
    }
    if recipient:
        status["recipient"] = recipient
    if subject:
        status["subject"] = subject
    return status


def send_email(to: str, subject: str, body: str):
    load_dotenv()

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port_value = os.getenv("SMTP_PORT", "587")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    configured_recipient = os.getenv("CHAT_EMAIL_TO") or smtp_username

    if not smtp_username or not smtp_password:
        return _email_status(
            False,
            "Email was not sent: SMTP_USERNAME and SMTP_PASSWORD must be configured.",
            to,
            subject,
        )

    to = to.strip()
    if to in {"YOUR_GMAIL_ADDRESS", "farhanshoukatali37"} and configured_recipient:
        to = configured_recipient
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", to):
        return _email_status(
            False,
            "Email was not sent: recipient must be a valid email address.",
            to,
            subject,
        )

    smtp_password = "".join(smtp_password.split())

    try:
        smtp_port = int(smtp_port_value)
    except ValueError:
        return _email_status(
            False,
            "Email was not sent: SMTP_PORT must be a valid port number.",
            to,
            subject,
        )

    message = EmailMessage()
    message["From"] = smtp_username
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            refused_recipients = server.send_message(message)
    except smtplib.SMTPAuthenticationError:
        return _email_status(
            False,
            "Email was not sent: Gmail rejected SMTP authentication. Verify "
            "SMTP_USERNAME and use a valid Google App Password in SMTP_PASSWORD.",
            to,
            subject,
        )
    except smtplib.SMTPRecipientsRefused as exc:
        refused = "; ".join(
            f"{recipient}: {code} {response.decode(errors='replace')}"
            for recipient, (code, response) in exc.recipients.items()
        )
        return _email_status(
            False,
            f"Email was not sent: SMTP rejected recipient(s): {refused}",
            to,
            subject,
        )
    except smtplib.SMTPResponseException as exc:
        response = exc.smtp_error.decode(errors="replace")
        return _email_status(
            False,
            f"Email was not sent: SMTP rejected the message ({exc.smtp_code}): {response}",
            to,
            subject,
        )
    except (smtplib.SMTPException, OSError) as exc:
        return _email_status(
            False,
            f"Email was not sent: {type(exc).__name__}: {exc}",
            to,
            subject,
        )

    if refused_recipients:
        return _email_status(
            False,
            f"Email was not accepted by the SMTP server for: {', '.join(refused_recipients)}",
            to,
            subject,
        )

    return _email_status(True, "Email sent successfully.", to, subject)