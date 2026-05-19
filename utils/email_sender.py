import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import keyring

KEYRING_SERVICE = "CotizacionesApp"
KEYRING_ACCOUNT = "gmail_app_password"

class EmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "joseluism1412@gmail.com"
        self.sender_password = self._get_app_password()

    def _get_app_password(self):
        try:
            return keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT) or ""
        except Exception:
            return ""
        return ""

    def send_email_with_attachment(self, to_email, attachment_path):
        if not self.sender_password:
            raise Exception(
                "No hay una Contraseña de Aplicación configurada. Por favor, configúrala en la pestaña de Configuración."
            )

        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = to_email
        msg["Subject"] = "Cotización de Servicios - Ing. Jose Luis Munoz"

        body = """
        Estimado cliente,
        
        Adjunto a este correo encontrará la cotización solicitada.
        Quedo a su entera disposición para cualquier consulta.
        
        Saludos cordiales,
        
        Ing. Jose Luis Muñoz
        Tel: 64998718
        Email: joseluism1412@gmail.com
        """
        msg.attach(MIMEText(body, "plain"))

        with open(attachment_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part["Content-Disposition"] = (
                f'attachment; filename="{os.path.basename(attachment_path)}"'
            )
            msg.attach(part)

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
        except smtplib.SMTPAuthenticationError:
            raise Exception(
                "Error de autenticación: Verifica que la Contraseña de Aplicación de Gmail sea correcta."
            )
        except Exception as e:
            raise Exception(f"Error al enviar el correo: {str(e)}")
