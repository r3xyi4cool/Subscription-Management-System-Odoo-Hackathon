import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timezone
from flask import current_app


class MailService:
    @staticmethod
    def send_email(to_email: str, subject: str, body_text: str, body_html: str = None, attachments: list = None):
        """Harmless console logger complying with NO EMAIL rule."""
        print(f"[MAIL DISABLED] Console Notification | To: {to_email} | Subject: {subject}")
        return True

    @staticmethod
    def send_password_reset_email(to_email: str, reset_token: str):
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        subject = "Password Reset Request"
        print(
            f"\n=======================================================\n"
            f"[LOCAL DEV] Password reset link for {to_email}:\n"
            f"{reset_link}\n"
            f"Token: {reset_token}\n"
            f"=======================================================\n"
        )
        return True

    @staticmethod
    def send_invoice_email(to_email: str, invoice, pdf_bytes: bytes = None):
        subject = f"Invoice #{invoice.invoice_number} from Subscription System"
        body_text = (
            f"Dear Customer,\n\n"
            f"Please find attached Invoice #{invoice.invoice_number} for the amount of ${float(invoice.total):.2f}.\n"
            f"Due Date: {invoice.due_date}\n\n"
            f"Thank you for your business!"
        )
        attachments = []
        if pdf_bytes:
            attachments.append((f"invoice_{invoice.invoice_number}.pdf", pdf_bytes))
        return MailService.send_email(to_email, subject, body_text, attachments=attachments)

