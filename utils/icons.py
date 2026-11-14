"""Iconos de línea (SVG 24x24) dibujados en tiempo de ejecución con el color pedido.
Sin archivos externos, así funcionan igual en desarrollo y en el ejecutable."""
from PyQt6.QtCore import Qt, QByteArray, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

_PATHS = {
    "quotes": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>'
              '<path d="M9 13h6M9 17h6"/>',
    "calculator": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8"/>'
                  '<path d="M8.5 11h.01M12 11h.01M15.5 11h.01M8.5 14.5h.01M12 14.5h.01M15.5 14.5h.01'
                  'M8.5 18h.01M12 18h.01M15.5 18h.01"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/>'
             '<path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7'
                'M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "trash": '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    "save": '<path d="M5 3h11l3 3v13a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2z"/><path d="M8 3v5h7V3M8 21v-7h8v7"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "chat": '<path d="M21 12a8.5 8.5 0 0 1-12.6 7.4L3 21l1.6-5.2A8.5 8.5 0 1 1 21 12z"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "arrow-right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "download": '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    "x": '<path d="M6 6l12 12M18 6 6 18"/>',
    "tag": '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.5"/>',
    "minus": '<path d="M5 12h14"/>',
}


def icon(name, color="#1F2937", size=18):
    body = _PATHS.get(name, "")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    scale = 2  # nítido en pantallas HiDPI
    pix = QPixmap(QSize(size * scale, size * scale))
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    pix.setDevicePixelRatio(scale)
    return QIcon(pix)
