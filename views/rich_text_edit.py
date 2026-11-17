from PyQt6.QtWidgets import QTextEdit, QToolBar, QComboBox, QColorDialog, QMenu, QToolButton
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QFont,
    QKeySequence,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextDocumentFragment,
    QTextFormat,
    QTextListFormat,
)
from PyQt6.QtCore import Qt

FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 36]

# Por debajo de esta saturación el color es negro/blanco/gris y puede perderse con el tema
MIN_COLOR_SATURATION = 40


def _apply_char_format(doc, start, end, modify):
    """Aplica `modify(fmt)` al formato de cada tramo de texto entre start y end."""
    changes = []
    block = doc.findBlock(start)
    while block.isValid() and block.position() < end:
        it = block.begin()
        while not it.atEnd():
            fragment = it.fragment()
            if fragment.isValid():
                frag_start = max(fragment.position(), start)
                frag_end = min(fragment.position() + fragment.length(), end)
                if frag_start < frag_end:
                    fmt = fragment.charFormat()
                    modify(fmt)
                    changes.append((frag_start, frag_end, fmt))
            it += 1
        block = block.next()

    cursor = QTextCursor(doc)
    for frag_start, frag_end, fmt in changes:
        cursor.setPosition(frag_start)
        cursor.setPosition(frag_end, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(fmt)


def sanitize_document(doc, keep_style=False):
    """Quita colores y fuentes que hacen ilegible el texto con el tema actual.

    Con keep_style=True (contenido guardado) se respetan los tamaños y los colores
    elegidos por el usuario; solo se quitan negros/blancos/grises y fondos.
    """

    def clean(fmt):
        if not keep_style or fmt.foreground().color().hslSaturation() < MIN_COLOR_SATURATION:
            fmt.clearForeground()
        fmt.clearBackground()
        fmt.clearProperty(QTextFormat.Property.FontFamilies)
        if not keep_style:
            fmt.clearProperty(QTextFormat.Property.FontPointSize)

    cursor = QTextCursor(doc)
    block = doc.begin()
    while block.isValid():
        block_fmt = block.blockFormat()
        block_fmt.clearBackground()
        block_char_fmt = block.charFormat()
        clean(block_char_fmt)
        cursor.setPosition(block.position())
        cursor.setBlockFormat(block_fmt)
        cursor.setBlockCharFormat(block_char_fmt)
        block = block.next()

    _apply_char_format(doc, 0, doc.characterCount(), clean)


class RichTextEdit(QTextEdit):
    """QTextEdit que limpia los estilos del texto pegado para que se lea con cualquier tema."""

    def insertFromMimeData(self, source):
        if source.hasHtml():
            doc = QTextDocument()
            doc.setHtml(source.html())
            sanitize_document(doc)
            self.textCursor().insertFragment(QTextDocumentFragment(doc))
            self.ensureCursorVisible()
        else:
            super().insertFromMimeData(source)

    def set_clean_html(self, html):
        self.setHtml(html)
        sanitize_document(self.document(), keep_style=True)


class FormattingToolBar(QToolBar):
    """Barra de formato (tamaño, estilos, color, alineación y listas) para un QTextEdit."""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        self.size_combo.addItems([str(size) for size in FONT_SIZES])
        self.size_combo.setToolTip("Tamaño de fuente")
        self.size_combo.setMinimumContentsLength(3)
        self.size_combo.textActivated.connect(self._set_font_size)
        self.addWidget(self.size_combo)
        self.addSeparator()

        self.bold_action = self._add_toggle(
            "N", "Negrita (Ctrl+B)", QKeySequence.StandardKey.Bold, self._set_bold
        )
        self.italic_action = self._add_toggle(
            "K", "Cursiva (Ctrl+I)", QKeySequence.StandardKey.Italic, self._set_italic
        )
        self.underline_action = self._add_toggle(
            "S", "Subrayado (Ctrl+U)", QKeySequence.StandardKey.Underline, self._set_underline
        )
        self.strike_action = self._add_toggle(
            "T", "Tachado", None, self._set_strikeout
        )
        self._style_action_font(self.bold_action, bold=True)
        self._style_action_font(self.italic_action, italic=True)
        self._style_action_font(self.underline_action, underline=True)
        self._style_action_font(self.strike_action, strikeout=True)

        color_menu = QMenu(self)
        color_menu.addAction("Elegir color...", self._choose_color)
        color_menu.addAction("Automático", self._reset_color)
        color_button = QToolButton()
        color_button.setText("Color")
        color_button.setToolTip("Color del texto")
        color_button.setMenu(color_menu)
        color_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.addWidget(color_button)
        self.addSeparator()

        align_group = QActionGroup(self)
        self.align_actions = {}
        for label, tooltip, alignment in [
            ("Izq", "Alinear a la izquierda", Qt.AlignmentFlag.AlignLeft),
            ("Centro", "Centrar", Qt.AlignmentFlag.AlignHCenter),
            ("Der", "Alinear a la derecha", Qt.AlignmentFlag.AlignRight),
            ("Just", "Justificar", Qt.AlignmentFlag.AlignJustify),
        ]:
            action = self._add_toggle(
                label, tooltip, None,
                lambda _checked, a=alignment: self.editor.setAlignment(a),
            )
            align_group.addAction(action)
            self.align_actions[alignment] = action
        self.addSeparator()

        self.bullet_action = self._add_toggle(
            "• Lista", "Lista con viñetas", None,
            lambda checked: self._toggle_list(QTextListFormat.Style.ListDisc, checked),
        )
        self.number_action = self._add_toggle(
            "1. Lista", "Lista numerada", None,
            lambda checked: self._toggle_list(QTextListFormat.Style.ListDecimal, checked),
        )
        self.addSeparator()

        clear_action = self.addAction("Sin formato")
        clear_action.setToolTip("Quitar formato del texto seleccionado")
        clear_action.triggered.connect(self._clear_format)

        self.editor.currentCharFormatChanged.connect(self._update_char_state)
        self.editor.cursorPositionChanged.connect(self._update_block_state)
        self._update_char_state(self.editor.currentCharFormat())
        self._update_block_state()

    def _add_toggle(self, text, tooltip, shortcut, slot):
        action = QAction(text, self)
        action.setToolTip(tooltip)
        action.setCheckable(True)
        if shortcut is not None:
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
            self.editor.addAction(action)
        # triggered (y no toggled) para que sincronizar el estado no reaplique el formato
        action.triggered.connect(slot)
        self.addAction(action)
        return action

    @staticmethod
    def _style_action_font(action, bold=False, italic=False, underline=False, strikeout=False):
        font = QFont(action.font())
        font.setBold(bold)
        font.setItalic(italic)
        font.setUnderline(underline)
        font.setStrikeOut(strikeout)
        action.setFont(font)

    def _merge_format(self, fmt):
        self.editor.mergeCurrentCharFormat(fmt)
        self.editor.setFocus()

    def _set_font_size(self, text):
        try:
            size = float(text)
        except ValueError:
            return
        if size > 0:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            self._merge_format(fmt)

    def _set_bold(self, checked):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        self._merge_format(fmt)

    def _set_italic(self, checked):
        fmt = QTextCharFormat()
        fmt.setFontItalic(checked)
        self._merge_format(fmt)

    def _set_underline(self, checked):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(checked)
        self._merge_format(fmt)

    def _set_strikeout(self, checked):
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(checked)
        self._merge_format(fmt)

    def _choose_color(self):
        color = QColorDialog.getColor(
            self.editor.currentCharFormat().foreground().color(), self, "Color del texto"
        )
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._merge_format(fmt)

    def _reset_color(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            _apply_char_format(
                self.editor.document(),
                cursor.selectionStart(),
                cursor.selectionEnd(),
                lambda fmt: fmt.clearForeground(),
            )
        fmt = self.editor.currentCharFormat()
        fmt.clearForeground()
        self.editor.setCurrentCharFormat(fmt)
        self.editor.setFocus()

    def _toggle_list(self, style, checked):
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        current_list = cursor.currentList()
        if checked:
            list_fmt = QTextListFormat()
            list_fmt.setStyle(style)
            if current_list:
                list_fmt.setIndent(current_list.format().indent())
                current_list.setFormat(list_fmt)
            else:
                cursor.createList(list_fmt)
        else:
            doc = self.editor.document()
            block = doc.findBlock(cursor.selectionStart())
            last = doc.findBlock(cursor.selectionEnd())
            while block.isValid():
                text_list = block.textList()
                if text_list:
                    text_list.remove(block)
                    block_cursor = QTextCursor(block)
                    block_fmt = block.blockFormat()
                    block_fmt.setIndent(0)
                    block_cursor.setBlockFormat(block_fmt)
                if block == last:
                    break
                block = block.next()
        cursor.endEditBlock()
        self._update_block_state()
        self.editor.setFocus()

    def _clear_format(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.setCharFormat(QTextCharFormat())
        self.editor.setCurrentCharFormat(QTextCharFormat())
        self.editor.setFocus()

    def _update_char_state(self, fmt):
        self.bold_action.setChecked(fmt.fontWeight() >= QFont.Weight.Bold)
        self.italic_action.setChecked(fmt.fontItalic())
        self.underline_action.setChecked(fmt.fontUnderline())
        self.strike_action.setChecked(fmt.fontStrikeOut())
        size = fmt.fontPointSize() or self.editor.font().pointSizeF()
        self.size_combo.setEditText(f"{size:g}")

    def _update_block_state(self):
        alignment = self.editor.alignment() & Qt.AlignmentFlag.AlignHorizontal_Mask
        if alignment == Qt.AlignmentFlag.AlignJustify:
            key = Qt.AlignmentFlag.AlignJustify
        elif alignment & Qt.AlignmentFlag.AlignHCenter:
            key = Qt.AlignmentFlag.AlignHCenter
        elif alignment & Qt.AlignmentFlag.AlignRight:
            key = Qt.AlignmentFlag.AlignRight
        else:
            key = Qt.AlignmentFlag.AlignLeft
        self.align_actions[key].setChecked(True)

        current_list = self.editor.textCursor().currentList()
        list_style = current_list.format().style() if current_list else None
        self.bullet_action.setChecked(
            list_style in (
                QTextListFormat.Style.ListDisc,
                QTextListFormat.Style.ListCircle,
                QTextListFormat.Style.ListSquare,
            )
        )
        self.number_action.setChecked(
            list_style in (
                QTextListFormat.Style.ListDecimal,
                QTextListFormat.Style.ListLowerAlpha,
                QTextListFormat.Style.ListUpperAlpha,
                QTextListFormat.Style.ListLowerRoman,
                QTextListFormat.Style.ListUpperRoman,
            )
        )
