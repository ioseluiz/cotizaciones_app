# Changelog

All notable changes to CotizacionesApp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
