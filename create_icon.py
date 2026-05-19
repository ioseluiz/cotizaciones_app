"""
Genera los iconos de la aplicacion en formato ICO (Windows) e ICNS (macOS).
Ejecutar una sola vez: python create_icon.py
Requiere: Pillow  (pip install pillow)
"""
import sys
import os
import subprocess
from PIL import Image, ImageDraw


SIZE = 1024
BG_COLOR = (21, 101, 192)      # azul Material Design 800
DOC_COLOR = (255, 255, 255)    # blanco
LINE_COLOR = (189, 220, 255)   # azul claro para lineas de texto
ACCENT_COLOR = (255, 193, 7)   # amarillo para el check


def rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + 2*radius, y0 + 2*radius], fill=fill)
    draw.ellipse([x1 - 2*radius, y0, x1, y0 + 2*radius], fill=fill)
    draw.ellipse([x0, y1 - 2*radius, x0 + 2*radius, y1], fill=fill)
    draw.ellipse([x1 - 2*radius, y1 - 2*radius, x1, y1], fill=fill)


def draw_icon(size=SIZE):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size

    # Fondo con esquinas redondeadas
    radius = int(s * 0.18)
    rounded_rect(draw, [0, 0, s - 1, s - 1], radius, BG_COLOR)

    # Documento (rectangulo blanco con esquina doblada)
    doc_x0 = int(s * 0.22)
    doc_y0 = int(s * 0.14)
    doc_x1 = int(s * 0.78)
    doc_y1 = int(s * 0.86)
    fold = int(s * 0.16)

    # Cuerpo del documento
    doc_shape = [
        (doc_x0, doc_y0),
        (doc_x1 - fold, doc_y0),
        (doc_x1, doc_y0 + fold),
        (doc_x1, doc_y1),
        (doc_x0, doc_y1),
    ]
    draw.polygon(doc_shape, fill=DOC_COLOR)

    # Triangulo de esquina doblada
    fold_shape = [
        (doc_x1 - fold, doc_y0),
        (doc_x1 - fold, doc_y0 + fold),
        (doc_x1, doc_y0 + fold),
    ]
    draw.polygon(fold_shape, fill=(180, 210, 240))

    # Lineas de texto simuladas
    line_x0 = doc_x0 + int(s * 0.08)
    line_x1 = doc_x1 - int(s * 0.08)
    line_h = int(s * 0.045)
    line_gap = int(s * 0.075)
    start_y = doc_y0 + int(s * 0.22)

    for i in range(5):
        y = start_y + i * line_gap
        # Ultima linea mas corta
        x1 = line_x1 if i < 4 else line_x0 + int((line_x1 - line_x0) * 0.55)
        draw.rounded_rectangle([line_x0, y, x1, y + line_h], radius=int(line_h / 2), fill=LINE_COLOR)

    # Check verde/amarillo en la esquina inferior derecha
    cx = int(s * 0.70)
    cy = int(s * 0.72)
    cr = int(s * 0.13)
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=ACCENT_COLOR)
    # Simbolo de check
    lw = max(4, int(s * 0.014))
    check = [
        (cx - int(cr * 0.45), cy),
        (cx - int(cr * 0.1), cy + int(cr * 0.38)),
        (cx + int(cr * 0.45), cy - int(cr * 0.30)),
    ]
    draw.line(check, fill=(21, 101, 192), width=lw)

    return img


def save_ico(img, path):
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [img.resize((s, s), Image.LANCZOS) for s in sizes]
    frames[0].save(path, format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=frames[1:])
    print(f"ICO guardado: {path}")


def save_icns(img, path):
    """Genera el ICNS usando iconutil de macOS."""
    iconset_dir = path.replace(".icns", ".iconset")
    os.makedirs(iconset_dir, exist_ok=True)

    specs = [
        ("icon_16x16.png", 16),
        ("icon_16x16@2x.png", 32),
        ("icon_32x32.png", 32),
        ("icon_32x32@2x.png", 64),
        ("icon_128x128.png", 128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png", 256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png", 512),
        ("icon_512x512@2x.png", 1024),
    ]
    for filename, size in specs:
        img.resize((size, size), Image.LANCZOS).save(
            os.path.join(iconset_dir, filename), "PNG"
        )

    result = subprocess.run(
        ["iconutil", "-c", "icns", iconset_dir, "-o", path],
        capture_output=True
    )
    if result.returncode == 0:
        print(f"ICNS guardado: {path}")
    else:
        print(f"iconutil fallo: {result.stderr.decode()}")
        print("Guarda el PNG manualmente y conviertelo en Mac con iconutil.")

    # Limpiar iconset temporal
    import shutil
    shutil.rmtree(iconset_dir, ignore_errors=True)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    img = draw_icon()

    # Guardar PNG base
    png_path = "assets/app_icon.png"
    img.save(png_path, "PNG")
    print(f"PNG guardado: {png_path}")

    # ICO para Windows
    save_ico(img, "installer/windows/app.ico")

    # ICNS para macOS (solo si estamos en Mac)
    if sys.platform == "darwin":
        save_icns(img, "installer/mac/app.icns")
    else:
        print("Ejecuta este script en macOS para generar el .icns")
