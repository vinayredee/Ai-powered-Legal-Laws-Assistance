import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def send_email(to_email: str, subject: str, body: str, attachment_path: str | None = None) -> bool:
    msg = MIMEMultipart()
    msg['From'] = "your_email@example.com"
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        with open(attachment_path, "rb") as file:
            attach_part = MIMEApplication(file.read())
            import os as _os
            attach_part.add_header('Content-Disposition', 'attachment', filename=_os.path.basename(attachment_path))
            msg.attach(attach_part)

    try:
        smtp_username = os.environ.get("SMTP_USERNAME")
        smtp_password = os.environ.get("SMTP_PASSWORD")
        if not smtp_username or not smtp_password:
            raise RuntimeError("Missing SMTP_USERNAME/SMTP_PASSWORD environment variables")

        msg['From'] = smtp_username

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg['From'], to_email, msg.as_string())
        server.close()
        return True
    except Exception:
        return False


