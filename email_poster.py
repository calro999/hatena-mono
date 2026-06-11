import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

class HatenaEmailPoster:
    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str, target_email: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.target_email = target_email

    def send_post(self, title: str, html_content: str, image_path: str = None) -> bool:
        if not self.smtp_host or not self.smtp_user or not self.smtp_pass or not self.target_email:
            print("Email configuration is incomplete. Skip sending and printing post locally.")
            print(f"--- DUMMY EMAIL POST ---")
            print(f"To: {self.target_email}")
            print(f"Subject: {title}")
            print(f"Content:\n{html_content[:500]}...")
            if image_path:
                print(f"Attachment: {image_path}")
            print(f"------------------------")
            return True

        try:
            # Create a multipart message
            msg = MIMEMultipart("mixed")
            msg["Subject"] = title
            msg["From"] = self.smtp_user
            msg["To"] = self.target_email

            # Hatena Blog accepts HTML mail. We attach it as alternative or simple body.
            # Add HTML content
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # Attach eyecatch image if provided
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as img_file:
                    img_data = img_file.read()
                    image_part = MIMEImage(img_data, name=os.path.basename(image_path))
                    image_part.add_header("Content-ID", f"<{os.path.basename(image_path)}>")
                    image_part.add_header("Content-Disposition", "attachment", filename=os.path.basename(image_path))
                    msg.attach(image_part)
                print(f"Attached image: {image_path}")

            # SMTP Connection
            print(f"Connecting to SMTP server {self.smtp_host}:{self.smtp_port}...")
            # Use SSL/TLS based on port
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, [self.target_email], msg.as_string())
            server.quit()
            print("Post email sent successfully.")
            return True
        except Exception as e:
            print(f"Failed to send email to Hatena Blog: {e}")
            return False
