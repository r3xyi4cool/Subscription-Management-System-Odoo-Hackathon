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
        backend = current_app.config.get("MAIL_BACKEND", "dev").lower()
        if backend == "smtp":
            return MailService._send_smtp(to_email, subject, body_text, body_html, attachments)
        else:
            return MailService._send_dev(to_email, subject, body_text, body_html, attachments)

    @staticmethod
    def _send_dev(to_email: str, subject: str, body_text: str, body_html: str = None, attachments: list = None):
        outbox_dir = current_app.config.get("MAIL_OUTBOX_DIR", "backend/outbox")
        os.makedirs(outbox_dir, exist_ok=True)

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        safe_to = to_email.replace("@", "_at_").replace(".", "_")
        filename = f"{timestamp_str}_{safe_to}.json"
        filepath = os.path.join(outbox_dir, filename)

        mail_record = {
            "to": to_email,
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
            "attachments_count": len(attachments) if attachments else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(mail_record, f, indent=2)

        print(f"[MAIL DEV OUTBOX] Sent email to {to_email}: {subject} (Saved to {filepath})")
        return True

    @staticmethod
    def _send_smtp(to_email: str, subject: str, body_text: str, body_html: str = None, attachments: list = None):
        host = current_app.config.get("SMTP_HOST")
        port = current_app.config.get("SMTP_PORT", 587)
        user = current_app.config.get("SMTP_USER")
        password = current_app.config.get("SMTP_PASSWORD")
        use_tls = current_app.config.get("SMTP_USE_TLS", True)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_email

        msg.attach(MIMEText(body_text, "plain"))
        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        if attachments:
            for filename, data in attachments:
                part = MIMEApplication(data, Name=filename)
                part["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(part)

        try:
            with smtplib.SMTP(host, port) as server:
                if use_tls:
                    server.starttls()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[MAIL SMTP ERROR] Failed sending to {to_email}: {e}")
            return False

    @staticmethod
    def send_password_reset_email(to_email: str, reset_token: str):
        reset_link = f"http://localhost:5000/api/v1/auth/reset-password?token={reset_token}"
        subject = "Password Reset Request"
        body_text = (
            f"Hello,\n\n"
            f"You requested a password reset. Please use the following token or link:\n\n"
            f"Token: {reset_token}\n"
            f"Link: {reset_link}\n\n"
            f"This link expires in 30 minutes and can only be used once.\n\n"
            f"If you did not request this, please ignore this email."
        )
        body_html = (
            f"<p>Hello,</p>"
            f"<p>You requested a password reset. Your reset token is: <strong>{reset_token}</strong></p>"
            f"<p><a href='{reset_link}'>Click here to reset your password</a></p>"
            f"<p>This link expires in 30 minutes and can only be used once.</p>"
        )
        return MailService.send_email(to_email, subject, body_text, body_html)

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

