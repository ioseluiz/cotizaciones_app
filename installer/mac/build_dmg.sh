#!/usr/bin/env bash
set -euo pipefail

APP_NAME="CotizacionesApp"
VERSION="${APP_VERSION:-1.0.0}"
APP_PATH="../../dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}-v${VERSION}.dmg"
DMG_STAGING="/tmp/${APP_NAME}-dmg-staging"

echo "Building DMG for ${APP_NAME} v${VERSION}"

# Verificar que el .app existe
if [ ! -d "$APP_PATH" ]; then
  echo "ERROR: ${APP_PATH} not found. Run PyInstaller first."
  exit 1
fi

# Limpiar staging previo
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"

# Instalar create-dmg si no está disponible
if ! command -v create-dmg &>/dev/null; then
  echo "Installing create-dmg via brew..."
  brew install create-dmg
fi

create-dmg \
  --volname "${APP_NAME} ${VERSION}" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 150 185 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 450 185 \
  --no-internet-enable \
  "${DMG_NAME}" \
  "${APP_PATH}"

echo "DMG created: ${DMG_NAME}"
