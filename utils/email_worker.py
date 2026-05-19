from PyQt6.QtCore import QThread, pyqtSignal
from utils.email_sender import EmailSender

class EmailWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, to_email, attachment_path):
        super().__init__()
        self.to_email = to_email
        self.attachment_path = attachment_path

    def run(self):
        try:
            sender = EmailSender()
            sender.send_email_with_attachment(self.to_email, self.attachment_path)
            self.finished_signal.emit(True, "Correo enviado exitosamente.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
