import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def send_email_with_attachment(subject, body, attachment_path):
    sender_email = os.getenv("MY_EMAIL")
    app_password = os.getenv("APP_PASSWORD")
    receiver_email = os.getenv("EMAIL_TO", sender_email)

    if not sender_email or not app_password:
        raise ValueError("MY_EMAIL or APP_PASSWORD missing from .env")

    attachment_path = Path(attachment_path)

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.set_content(body)

    attachment_data = attachment_path.read_bytes()

    msg.add_attachment(
        attachment_data,
        maintype="application",
        subtype="pdf",
        filename=attachment_path.name,
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(sender_email, app_password)
        connection.send_message(msg)


if __name__ == "__main__":
    test_pdf = "reports/weekly/weekly_report_2026-05-01.pdf"

    send_email_with_attachment(
        subject="Weekly Portfolio Report",
        body="Attached is your weekly portfolio report.",
        attachment_path=test_pdf,
    )

    print("Email sent successfully.")
