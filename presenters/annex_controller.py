"""Conecta una AnnexList con AnnexModel. Lo usan Cotizaciones (anexos de la
cotización + fijos del negocio) y Configuración (anexos fijos del negocio).

Los cambios en anexos se guardan al momento (los archivos ya se copiaron), sin
esperar al botón Guardar del formulario.
"""
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QFileDialog

from models.annex_model import AnnexModel, FILE_FILTER, TIPO_TEXTO
from views.annex_widgets import AnnexList, TextAnnexDialog


class AnnexController(QObject):
    def __init__(self, widget: AnnexList, model: AnnexModel, view, quote_mode):
        """quote_mode=True: la lista es de una cotización (set_owner con quote_id);
        False: anexos fijos del negocio (set_owner con negocio)."""
        super().__init__()
        self.widget = widget
        self.model = model
        self.view = view  # para diálogos y avisos (ViewHelpers)
        self.quote_mode = quote_mode
        self.quote_id = None
        self.negocio = None

        widget.add_file_requested.connect(self.add_file)
        widget.add_text_requested.connect(self.add_text)
        widget.edit_requested.connect(self.edit)
        widget.remove_requested.connect(self.remove)
        widget.order_changed.connect(self.model.reorder)
        widget.inclusion_changed.connect(self.set_included)

    def set_owner(self, negocio, quote_id=None):
        self.negocio = negocio
        self.quote_id = quote_id
        self.refresh()

    def refresh(self, select_id=None):
        if self.quote_mode:
            fixed = self.model.get_business_annexes(self.negocio) if self.negocio else []
            own = self.model.get_quote_annexes(self.quote_id) if self.quote_id else []
            excluded = self.model.get_excluded(self.quote_id) if self.quote_id else set()
            self.widget.set_annexes(fixed, own, excluded, checkable=bool(self.quote_id))
            self.widget.set_editable(bool(self.quote_id))
        else:
            self.widget.set_annexes([], self.model.get_business_annexes(self.negocio) if self.negocio else [])
            self.widget.set_editable(bool(self.negocio))
        if select_id is not None:
            self.widget.select_annex(select_id)

    def _owner(self):
        return {"quote_id": self.quote_id} if self.quote_mode else {"negocio": self.negocio}

    # ------------------------------------------------------------- acciones
    def add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self.view, "Agregar anexos", "", FILE_FILTER)
        last = None
        for path in paths:
            try:
                last = self.model.add_file(path, **self._owner())
            except Exception as e:
                self.view.show_error(f"No se pudo agregar '{path}':\n{e}")
        if last is not None:
            self.refresh(last)
            self.view.show_toast(f"{len(paths)} anexo(s) agregado(s)" if len(paths) > 1 else "Anexo agregado")

    def add_text(self):
        dialog = TextAnnexDialog(self.view)
        if not dialog.exec():
            return
        titulo, contenido = dialog.values()
        try:
            annex_id = self.model.add_text(titulo, contenido, **self._owner())
        except Exception as e:
            self.view.show_error(f"No se pudo guardar el anexo: {e}")
            return
        self.refresh(annex_id)
        self.view.show_toast("Página de texto agregada")

    def edit(self, annex):
        if annex["tipo"] == TIPO_TEXTO:
            dialog = TextAnnexDialog(self.view, annex["titulo"], annex["contenido"])
            if not dialog.exec():
                return
            titulo, contenido = dialog.values()
            self.model.update(annex["id"], titulo, contenido)
        else:
            titulo = self.view.ask_text("Editar anexo", "Título del anexo:", annex["titulo"])
            if not titulo:
                return
            self.model.update(annex["id"], titulo)
        self.refresh(annex["id"])

    def remove(self, annex):
        if not self.view.ask_yes_no(f"¿Quitar el anexo '{annex['titulo']}'?", "Quitar anexo"):
            return
        self.model.delete(annex["id"])
        self.refresh()

    def set_included(self, annex_id, included):
        if self.quote_id:
            self.model.set_excluded(self.quote_id, annex_id, not included)
