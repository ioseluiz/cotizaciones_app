"""Lista de anexos del PDF y diálogo para escribir páginas de texto."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QDialog, QLineEdit,
)

from models.annex_model import TIPOS
from views.rich_text_edit import RichTextEdit, FormattingToolBar
from views.widgets import ViewHelpers, make_button, make_label

ROLE_ANNEX = Qt.ItemDataRole.UserRole
ROLE_FIXED = Qt.ItemDataRole.UserRole + 1


class AnnexList(QWidget):
    """Anexos en orden de aparición en el PDF.

    En una cotización, los anexos fijos del negocio aparecen primero con una
    casilla para incluirlos o excluirlos; no se editan ni se mueven desde ahí.
    """

    add_file_requested = pyqtSignal()
    add_text_requested = pyqtSignal()
    edit_requested = pyqtSignal(dict)
    remove_requested = pyqtSignal(dict)
    order_changed = pyqtSignal(list)          # ids de los anexos propios en el nuevo orden
    inclusion_changed = pyqtSignal(int, bool)  # (id del anexo fijo, incluido)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.list = QListWidget()
        self.list.setMinimumHeight(110)
        self.list.setToolTip("Doble clic para editar")
        lay.addWidget(self.list)

        btns = QHBoxLayout()
        self.add_file_btn = make_button("Agregar PDF o imagen...", "ghost", "plus")
        self.add_text_btn = make_button("Página de texto...", "ghost", "plus",
                                        "Escribir una página adicional con formato")
        self.edit_btn = make_button("Editar", "ghost", None, "Cambiar el título o el texto del anexo")
        self.remove_btn = make_button("Quitar", "ghost", "minus", "Quitar el anexo seleccionado")
        self.up_btn = make_button("↑", "ghost", None, "Mover antes")
        self.down_btn = make_button("↓", "ghost", None, "Mover después")
        for b in (self.add_file_btn, self.add_text_btn, self.edit_btn, self.remove_btn):
            btns.addWidget(b)
        btns.addStretch()
        btns.addWidget(self.up_btn)
        btns.addWidget(self.down_btn)
        lay.addLayout(btns)

        self.add_file_btn.clicked.connect(self.add_file_requested)
        self.add_text_btn.clicked.connect(self.add_text_requested)
        self.edit_btn.clicked.connect(self._emit_edit)
        self.remove_btn.clicked.connect(self._emit_remove)
        self.up_btn.clicked.connect(lambda: self._move(-1))
        self.down_btn.clicked.connect(lambda: self._move(1))
        self.list.itemDoubleClicked.connect(lambda _i: self._emit_edit())
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.currentRowChanged.connect(lambda _r: self._update_buttons())
        self._editable = True
        self._update_buttons()

    # ------------------------------------------------------------------ datos
    def set_annexes(self, fixed, own, excluded=frozenset(), checkable=True):
        """fixed: anexos fijos del negocio; own: anexos propios (editables)."""
        self.list.blockSignals(True)
        self.list.clear()
        n = 0
        for a in fixed:
            n += 1
            item = QListWidgetItem(f"{TIPOS.get(a['tipo'], a['tipo'])} · {a['titulo']}   (fijo del negocio)")
            item.setData(ROLE_ANNEX, a)
            item.setData(ROLE_FIXED, True)
            if checkable:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked if a["id"] in excluded else Qt.CheckState.Checked)
                item.setToolTip("Desmarque para no incluirlo en esta cotización")
            self.list.addItem(item)
        for a in own:
            n += 1
            item = QListWidgetItem(f"{TIPOS.get(a['tipo'], a['tipo'])} · {a['titulo']}")
            item.setData(ROLE_ANNEX, a)
            item.setData(ROLE_FIXED, False)
            self.list.addItem(item)
        self.list.blockSignals(False)
        self._update_buttons()

    def set_editable(self, editable):
        """False: solo se pueden marcar/desmarcar los fijos (cotización sin guardar)."""
        self._editable = editable
        self._update_buttons()

    def select_annex(self, annex_id):
        for row in range(self.list.count()):
            if self.list.item(row).data(ROLE_ANNEX)["id"] == annex_id:
                self.list.setCurrentRow(row)
                return

    # --------------------------------------------------------------- interno
    def _current(self):
        item = self.list.currentItem()
        if item is None or item.data(ROLE_FIXED):
            return None
        return item.data(ROLE_ANNEX)

    def _own_rows(self):
        return [r for r in range(self.list.count()) if not self.list.item(r).data(ROLE_FIXED)]

    def _update_buttons(self):
        own = self._current() is not None and self._editable
        self.add_file_btn.setEnabled(self._editable)
        self.add_text_btn.setEnabled(self._editable)
        for b in (self.edit_btn, self.remove_btn):
            b.setEnabled(own)
        rows = self._own_rows()
        row = self.list.currentRow()
        self.up_btn.setEnabled(own and bool(rows) and row > rows[0])
        self.down_btn.setEnabled(own and bool(rows) and row < rows[-1])

    def _emit_edit(self):
        annex = self._current()
        if annex and self._editable:
            self.edit_requested.emit(annex)

    def _emit_remove(self):
        annex = self._current()
        if annex and self._editable:
            self.remove_requested.emit(annex)

    def _move(self, delta):
        rows = self._own_rows()
        row = self.list.currentRow()
        if row not in rows:
            return
        target = row + delta
        if target not in rows:
            return
        item = self.list.takeItem(row)
        self.list.insertItem(target, item)
        self.list.setCurrentRow(target)
        self.order_changed.emit([self.list.item(r).data(ROLE_ANNEX)["id"] for r in self._own_rows()])

    def _on_item_changed(self, item):
        if item.data(ROLE_FIXED):
            self.inclusion_changed.emit(item.data(ROLE_ANNEX)["id"], item.checkState() == Qt.CheckState.Checked)


class TextAnnexDialog(QDialog, ViewHelpers):
    """Escribir o editar una página de texto con formato."""

    def __init__(self, parent=None, titulo="", contenido=""):
        super().__init__(parent)
        self.setWindowTitle("Página de texto")
        self.resize(760, 560)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        lay.addWidget(make_label("Título del anexo", "muted"))
        self.title_input = QLineEdit(titulo)
        self.title_input.setPlaceholderText("Ej. Alcance detallado, Metodología, Términos y condiciones")
        lay.addWidget(self.title_input)
        lay.addWidget(make_label("Contenido", "muted"))
        self.content_edit = RichTextEdit()
        self.content_edit.setAcceptRichText(True)
        self.content_edit.set_clean_html(contenido)
        lay.addWidget(FormattingToolBar(self.content_edit))
        lay.addWidget(self.content_edit, 1)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = make_button("Cancelar")
        cancel.clicked.connect(self.reject)
        ok = make_button("Aceptar", "primary")
        ok.clicked.connect(self._accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        lay.addLayout(btns)

    def _accept(self):
        if not self.title_input.text().strip():
            self.show_error("El anexo necesita un título")
            return
        if not self.content_edit.toPlainText().strip():
            self.show_error("Escriba el contenido de la página")
            return
        self.accept()

    def values(self):
        return self.title_input.text().strip(), self.content_edit.toHtml()
