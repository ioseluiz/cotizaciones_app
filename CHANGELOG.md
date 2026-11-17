# Changelog

All notable changes to CotizacionesApp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Estimador de proyectos (nueva sección): actividades con horas por tarifa según
  rol, gastos fijos, entregables, contingencia, margen e ITBMS (7%) con resumen en
  vivo. Incluye plantillas editables para software e ingeniería estructural y
  genera la cotización con un ítem por fase.
- Separación por negocio (Estructural / Software): cotizaciones, estimados,
  clientes, roles y plantillas filtrados por el negocio activo, con numeración
  propia (EST-0001, SW-0001). El encabezado del PDF, las condiciones, el correo y
  el mensaje de WhatsApp se configuran por negocio. Las cotizaciones existentes se
  migran automáticamente (con respaldo) y conservan su número.
- Editor de texto con formato (tamaño, negrita, cursiva, subrayado, tachado,
  color, alineación y listas) en las observaciones de la cotización, las
  condiciones por defecto de Configuración y las notas del estimador. Al pegar
  texto se quitan los colores y fondos que no se leen con el tema.
- Atajos de teclado (Ctrl+N, Ctrl+S, Ctrl+F, Ctrl+1 a Ctrl+4) y avisos breves en
  la barra de estado.

### Changed
- Rediseño de la interfaz: tema claro propio (independiente del modo oscuro de
  Windows) con el color de cada negocio, barra lateral con iconos que se contrae
  en ventanas angostas, y tablas que se ajustan al tamaño de la ventana.
- Cotizaciones: lista con buscador, barra de acciones fija y botón "Ver PDF".
  Clientes en formato lista y ficha; Configuración organizada en pestañas.
- El PDF usa el color del negocio, fechas en formato dd/mm/aaaa y montos con
  separador de miles ($1,200.00), igual que en la app.
- Envío por WhatsApp: se abre directamente WhatsApp Web en lugar de pasar por
  la página intermedia de wa.me, y el aviso indica Cmd+V para pegar el PDF en Mac.

### Fixed
- Cotización duplicada al guardar dos veces una cotización nueva.
- Pérdida de la fecha al editar una cotización.
- Desplegables con texto blanco sobre fondo blanco y encabezado del calendario
  ilegible.
- Ahora se pide confirmación antes de eliminar un cliente que tiene cotizaciones.

## [1.0.3] - 2026-06-01

### Changed
- La base de datos y la configuración ahora se guardan en una carpeta estable por
  usuario (`%APPDATA%\CotizacionesApp` en Windows). Así los datos se conservan al
  instalar, actualizar o desinstalar el ejecutable. La base de datos existente se
  migra automáticamente la primera vez que se abre esta versión.

### Fixed
- Envío por WhatsApp: el PDF ahora se copia al portapapeles para pegarlo (Ctrl+V)
  en el chat y se abre el Explorador con el archivo seleccionado, en lugar de
  pedir al usuario que lo busque manualmente.

## [1.0.1] - 2026-05-18

### Fixed
- Error "No module named 'email'" al ejecutar en Windows: email.mime.* y smtplib
  fueron incorrectamente excluidos del bundle de PyInstaller

### Changed
- Empaquetado con PyInstaller en modo --onedir (inicio más rápido, menos problemas con antivirus)
- Ícono de aplicación agregado (ventana, barra de tareas e instalador de Windows)

## [1.0.0] - 2026-05-18

### Added
- Gestión de clientes (crear, editar, eliminar)
- Generación de cotizaciones con items detallados
- Exportación de cotizaciones a PDF
- Envío de cotizaciones por correo (Gmail)
- Almacenamiento seguro de credenciales con keyring
- Configuración de ruta de base de datos y respaldo
