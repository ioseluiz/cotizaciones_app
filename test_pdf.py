import sys
from PyQt6.QtWidgets import QApplication
from utils.pdf_generator import PDFGenerator

app = QApplication(sys.argv)
gen = PDFGenerator()
quote_data = (1, "Cliente de Prueba con un nombre largo", "DESARROLLADOR DE SOFTWARE", "2023-10-10", "Un Proyecto Muy Largo Para Que La Tabla Se Llene XYZ", "<p>Estas son observaciones detalladas.<br/>Otra linea de observaciones.</p>", "test@test.com", "12345678")
items_data = [
    (1, "Desarrollo Web Frontend", "Desarrollo de interfaz de usuario con React y Tailwind CSS, incluyendo diseño responsivo", 1500.0), 
    (2, "Backend API", "Desarrollo de servicios RESTful y conexión a base de datos PostgreSQL", 2000.0),
    (3, "Despliegue", "Configuración de entorno de producción en AWS", 500.0)
]
gen.generate(quote_data, items_data, "test.pdf")
print("Done")
