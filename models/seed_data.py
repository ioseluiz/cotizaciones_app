"""Datos iniciales para el estimador: roles con tarifa por hora y plantillas
base de actividades/entregables. Solo se insertan si las tablas están vacías,
después el usuario puede editarlos libremente desde la app."""

TIPO_SOFTWARE = "SOFTWARE"
TIPO_ESTRUCTURAL = "ESTRUCTURAL"
TIPO_AMBOS = "AMBOS"
TIPOS_ESTIMADO = [TIPO_SOFTWARE, TIPO_ESTRUCTURAL]

# Equivalencia con los tipos que ya usa la pestaña de Cotizaciones
TIPO_A_TIPO_COTIZACION = {
    TIPO_SOFTWARE: "DESARROLLADOR DE SOFTWARE",
    TIPO_ESTRUCTURAL: "INGENIERO CIVIL",
}

DEFAULT_ROLES = [
    # (nombre, tarifa_hora, tipo)
    ("Desarrollador Senior", 35.0, TIPO_SOFTWARE),
    ("Desarrollador Junior", 20.0, TIPO_SOFTWARE),
    ("Diseñador UI/UX", 25.0, TIPO_SOFTWARE),
    ("QA / Tester", 18.0, TIPO_SOFTWARE),
    ("Ingeniero Estructural Senior", 40.0, TIPO_ESTRUCTURAL),
    ("Ingeniero Estructural Junior", 25.0, TIPO_ESTRUCTURAL),
    ("Dibujante / Modelador BIM", 15.0, TIPO_ESTRUCTURAL),
    ("Gestión de Proyecto", 30.0, TIPO_AMBOS),
]

DEFAULT_TEMPLATES = [
    {
        "nombre": "Software estándar",
        "tipo": TIPO_SOFTWARE,
        "actividades": [
            # (fase, actividad, rol, horas)
            ("Requerimientos", "Reuniones de levantamiento con el cliente", "Gestión de Proyecto", 4),
            ("Requerimientos", "Documento de requerimientos y alcance", "Desarrollador Senior", 6),
            ("Diseño", "Wireframes y prototipo de interfaz", "Diseñador UI/UX", 12),
            ("Diseño", "Arquitectura y modelo de datos", "Desarrollador Senior", 6),
            ("Desarrollo Backend", "Base de datos, API y lógica de negocio", "Desarrollador Senior", 40),
            ("Desarrollo Frontend", "Pantallas e integración con API", "Desarrollador Junior", 40),
            ("Pruebas", "Pruebas funcionales y corrección de errores", "QA / Tester", 16),
            ("Despliegue", "Puesta en producción y configuración", "Desarrollador Senior", 4),
            ("Despliegue", "Capacitación al usuario", "Gestión de Proyecto", 3),
        ],
        "entregables": [
            "Documento de requerimientos y alcance",
            "Prototipo de interfaz aprobado",
            "Código fuente en repositorio",
            "Aplicación desplegada en producción",
            "Manual de usuario",
            "Sesión de capacitación",
        ],
    },
    {
        "nombre": "Estructural estándar",
        "tipo": TIPO_ESTRUCTURAL,
        "actividades": [
            ("Levantamiento", "Revisión de planos arquitectónicos y estudio de suelos", "Ingeniero Estructural Senior", 4),
            ("Levantamiento", "Definición de criterios de diseño y cargas", "Ingeniero Estructural Senior", 3),
            ("Modelado", "Modelo analítico de la estructura", "Ingeniero Estructural Junior", 12),
            ("Análisis", "Análisis por cargas gravitacionales, sismo y viento", "Ingeniero Estructural Senior", 10),
            ("Diseño", "Diseño de cimentaciones", "Ingeniero Estructural Junior", 8),
            ("Diseño", "Diseño de columnas, vigas y losas", "Ingeniero Estructural Junior", 12),
            ("Diseño", "Revisión de diseño", "Ingeniero Estructural Senior", 4),
            ("Planos", "Elaboración de planos estructurales", "Dibujante / Modelador BIM", 24),
            ("Memoria de cálculo", "Redacción de memoria de cálculo y especificaciones", "Ingeniero Estructural Junior", 8),
        ],
        "entregables": [
            "Planos estructurales firmados y sellados",
            "Memoria de cálculo estructural",
            "Especificaciones técnicas",
            "Modelo digital de la estructura",
        ],
    },
]

TIPO_NOMBRES = {
    TIPO_ESTRUCTURAL: "Ingeniería Estructural",
    TIPO_SOFTWARE: "Desarrollo de Software",
}

# Marcadores disponibles en los mensajes: {cliente}, {proyecto}, {numero}
_FIRMA_CONTACTO = "Ing. Jose Luis Muñoz\nTel: 64998718\nEmail: joseluism1412@gmail.com"

DEFAULT_BUSINESSES = [
    {
        "clave": TIPO_ESTRUCTURAL,
        "nombre": TIPO_NOMBRES[TIPO_ESTRUCTURAL],
        "prefijo": "EST",
        "encabezado_nombre": "ING. JOSE LUIS MUÑOZ",
        "encabezado_titulo": "INGENIERO CIVIL",
        "ruc": "RUC: 8-791-273 | D.V. 94",
        "email": "joseluism1412@gmail.com",
        "telefono": "64998718",
        "firma": "Ing. Jose Luis Munoz",
        "logo_path": "",
        "condiciones": (
            "<ul><li>Validez de la oferta: 30 días.</li>"
            "<li>Forma de pago: 50% al inicio y 50% contra entrega de planos.</li>"
            "<li>No incluye trámites ni pagos de permisos de construcción.</li></ul>"
        ),
        "email_asunto": "Cotización {numero} - Ingeniería Estructural - {proyecto}",
        "email_cuerpo": (
            "Estimado {cliente},\n\nAdjunto a este correo encontrará la cotización {numero} "
            "para el proyecto '{proyecto}'.\nQuedo a su entera disposición para cualquier consulta.\n\n"
            "Saludos cordiales,\n\n" + _FIRMA_CONTACTO
        ),
        "whatsapp_mensaje": (
            "Estimado {cliente},\n\nAdjunto a este mensaje encontrará la cotización {numero} "
            "para el proyecto '{proyecto}'.\n\nQuedo a su entera disposición para cualquier consulta.\n\n"
            "Saludos cordiales,\n\n" + _FIRMA_CONTACTO
        ),
    },
    {
        "clave": TIPO_SOFTWARE,
        "nombre": TIPO_NOMBRES[TIPO_SOFTWARE],
        "prefijo": "SW",
        "encabezado_nombre": "ING. JOSE LUIS MUÑOZ",
        "encabezado_titulo": "DESARROLLADOR DE SOFTWARE",
        "ruc": "RUC: 8-791-273 | D.V. 94",
        "email": "joseluism1412@gmail.com",
        "telefono": "64998718",
        "firma": "Ing. Jose Luis Munoz",
        "logo_path": "",
        "condiciones": (
            "<ul><li>Validez de la oferta: 30 días.</li>"
            "<li>Forma de pago: 40% al inicio, 30% a la entrega del prototipo y 30% a la puesta en producción.</li>"
            "<li>Cambios fuera del alcance se cotizan por separado.</li>"
            "<li>No incluye costos de hosting, dominios ni licencias de terceros.</li></ul>"
        ),
        "email_asunto": "Cotización {numero} - Desarrollo de Software - {proyecto}",
        "email_cuerpo": (
            "Estimado {cliente},\n\nAdjunto a este correo encontrará la propuesta {numero} "
            "para el proyecto '{proyecto}'.\nQuedo a su entera disposición para cualquier consulta.\n\n"
            "Saludos cordiales,\n\n" + _FIRMA_CONTACTO
        ),
        "whatsapp_mensaje": (
            "Estimado {cliente},\n\nAdjunto a este mensaje encontrará la propuesta {numero} "
            "para el proyecto '{proyecto}'.\n\nQuedo a su entera disposición para cualquier consulta.\n\n"
            "Saludos cordiales,\n\n" + _FIRMA_CONTACTO
        ),
    },
]
