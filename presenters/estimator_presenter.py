import re
from PyQt6.QtCore import QObject, Qt, QDate, pyqtSignal
from PyQt6.QtWidgets import QTableWidgetItem, QComboBox, QListWidgetItem

from models.client_model import ClientModel
from models.estimate_model import EstimateModel
from models.quote_model import QuoteModel
from models.role_model import RoleModel
from models.template_model import TemplateModel
from models.business_model import BusinessModel, format_quote_number
from utils.estimate_calculator import Activity, Expense, calculate, build_quote_items
from views.estimator_view import (
    EstimatorView,
    COL_FASE,
    COL_ACTIVIDAD,
    COL_ROL,
    COL_HORAS,
    COL_TARIFA,
    COL_COSTO,
    COL_GASTO_DESC,
    COL_GASTO_MONTO,
)
from views.roles_dialog import RolesDialog


def _to_float(text):
    try:
        return float(str(text).strip().replace(",", ".") or 0)
    except ValueError:
        return 0.0


def _html_body(html):
    """Extrae el contenido del <body> de un documento HTML de QTextEdit."""
    m = re.search(r"<body[^>]*>(.*)</body>", html or "", re.S | re.I)
    return m.group(1).strip() if m else (html or "")


class EstimatorPresenter(QObject):
    quote_generated_signal = pyqtSignal()

    def __init__(self, view: EstimatorView, estimate_model: EstimateModel, role_model: RoleModel,
                 template_model: TemplateModel, quote_model: QuoteModel, client_model: ClientModel,
                 business_model: BusinessModel, context):
        super().__init__()
        self.business_model = business_model
        self.context = context
        self.view = view
        self.estimate_model = estimate_model
        self.role_model = role_model
        self.template_model = template_model
        self.quote_model = quote_model
        self.client_model = client_model

        self.selected_estimate_id = None
        self.roles = {}  # id -> (nombre, tarifa, tipo)

        v = self.view
        v.add_activity_btn.clicked.connect(lambda: self.add_activity_row())
        v.remove_activity_btn.clicked.connect(self.remove_activity_row)
        v.add_expense_btn.clicked.connect(lambda: self.add_expense_row())
        v.remove_expense_btn.clicked.connect(self.remove_expense_row)
        v.add_deliverable_btn.clicked.connect(self.add_deliverable)
        v.remove_deliverable_btn.clicked.connect(self.remove_deliverable)
        v.activities_table.itemChanged.connect(self.recalculate)
        v.expenses_table.itemChanged.connect(self.recalculate)
        v.contingency_spin.valueChanged.connect(self.recalculate)
        v.margin_spin.valueChanged.connect(self.recalculate)
        v.itbms_check.stateChanged.connect(self.recalculate)
        self.context.changed.connect(self.on_business_changed)
        v.load_template_btn.clicked.connect(self.load_template)
        v.save_template_btn.clicked.connect(self.save_template)
        v.delete_template_btn.clicked.connect(self.delete_template)
        v.roles_btn.clicked.connect(self.edit_roles)
        v.save_btn.clicked.connect(self.save_estimate)
        v.clear_btn.clicked.connect(self.clear_form)
        v.generate_quote_btn.clicked.connect(self.generate_quote)
        v.estimates_table.itemSelectionChanged.connect(self.on_estimate_selected)
        v.delete_estimate_btn.clicked.connect(self.delete_estimate)

        self.load_roles()
        self.load_clients()
        self.load_templates()
        self.load_estimates()
        self.recalculate()

    # ------------------------------------------------------------------ carga
    def load_clients(self):
        current = self.view.client_combo.currentData()
        self.view.client_combo.clear()
        for c in self.client_model.get_all_clients(self.context.current):
            self.view.client_combo.addItem(c[1], userData=c[0])
        self._select_client(current)

    def _select_client(self, client_id):
        idx = self.view.client_combo.findData(client_id)
        if idx >= 0:
            self.view.client_combo.setCurrentIndex(idx)

    def load_roles(self):
        self.roles = {r[0]: (r[1], r[2], r[3]) for r in self.role_model.get_all_roles()}

    def load_templates(self):
        self.view.template_combo.clear()
        for t in self.template_model.get_templates(self.current_type()):
            self.view.template_combo.addItem(t[1], userData=t[0])

    def load_estimates(self):
        table = self.view.estimates_table
        table.blockSignals(True)
        table.setRowCount(0)
        prefijo = self.prefijo()
        for row, e in enumerate(self.estimate_model.get_all_estimates(self.context.current)):
            estimate_id, fecha, cliente, proyecto, quote_id, numero = e
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(estimate_id)))
            table.setItem(row, 1, QTableWidgetItem(fecha))
            table.setItem(row, 2, QTableWidgetItem(cliente))
            table.setItem(row, 3, QTableWidgetItem(proyecto))
            table.setItem(row, 4, QTableWidgetItem(format_quote_number(prefijo, numero) if quote_id else ""))
        table.blockSignals(False)

    def current_type(self):
        """El tipo de estimado es siempre el negocio activo."""
        return self.context.current

    def business(self):
        return self.business_model.get(self.context.current) or {}

    def prefijo(self):
        return self.business().get("prefijo", "")

    def _quote_code(self, quote_id):
        return format_quote_number(self.prefijo(), self.estimate_model.get_quote_number(quote_id))

    def on_business_changed(self, _clave):
        self.clear_form()
        self.load_clients()
        self.load_estimates()
        self.on_type_changed(self.current_type())

    # ------------------------------------------------------------ actividades
    def _roles_for_current_type(self):
        return self.role_model.get_roles_for_type(self.current_type())

    def _build_role_combo(self, rol_id=None, rol_nombre=""):
        combo = QComboBox()
        combo.addItem("— Sin rol —", userData=None)
        for r in self._roles_for_current_type():
            combo.addItem(f"{r[1]} (${r[2]:.2f})", userData=r[0])
        idx = combo.findData(rol_id) if rol_id is not None else 0
        if idx < 0:
            # Rol de otro tipo o eliminado: lo mostramos igual para no perder el dato
            nombre = self.roles.get(rol_id, (rol_nombre or "Rol eliminado",))[0]
            combo.addItem(nombre, userData=rol_id)
            idx = combo.count() - 1
        combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(lambda _i, c=combo: self.on_role_changed(c))
        return combo

    def add_activity_row(self, fase="", actividad="", rol_id=None, horas=0.0, tarifa=None, rol_nombre=""):
        table = self.view.activities_table
        table.blockSignals(True)
        row = table.rowCount()
        table.insertRow(row)
        if tarifa is None:
            tarifa = self.roles.get(rol_id, (None, 0.0))[1]
        table.setItem(row, COL_FASE, QTableWidgetItem(fase))
        table.setItem(row, COL_ACTIVIDAD, QTableWidgetItem(actividad))
        table.setCellWidget(row, COL_ROL, self._build_role_combo(rol_id, rol_nombre))
        table.setItem(row, COL_HORAS, QTableWidgetItem(f"{horas:g}"))
        table.setItem(row, COL_TARIFA, QTableWidgetItem(f"{tarifa:.2f}"))
        costo_item = QTableWidgetItem("0.00")
        costo_item.setFlags(costo_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, COL_COSTO, costo_item)
        table.blockSignals(False)
        self.recalculate()

    def remove_activity_row(self):
        row = self.view.activities_table.currentRow()
        if row >= 0:
            self.view.activities_table.removeRow(row)
            self.recalculate()

    def on_role_changed(self, combo):
        table = self.view.activities_table
        for row in range(table.rowCount()):
            if table.cellWidget(row, COL_ROL) is combo:
                rol_id = combo.currentData()
                if rol_id in self.roles:
                    table.blockSignals(True)
                    table.item(row, COL_TARIFA).setText(f"{self.roles[rol_id][1]:.2f}")
                    table.blockSignals(False)
                self.recalculate()
                return

    def on_type_changed(self, _tipo):
        # Reconstruir los combos de rol para el nuevo tipo, conservando la selección
        table = self.view.activities_table
        table.blockSignals(True)
        for row in range(table.rowCount()):
            old = table.cellWidget(row, COL_ROL)
            rol_id = old.currentData() if old else None
            table.setCellWidget(row, COL_ROL, self._build_role_combo(rol_id))
        table.blockSignals(False)
        self.load_templates()

    # ----------------------------------------------------- gastos/entregables
    def add_expense_row(self, descripcion="", monto=0.0):
        table = self.view.expenses_table
        table.blockSignals(True)
        row = table.rowCount()
        table.insertRow(row)
        table.setItem(row, COL_GASTO_DESC, QTableWidgetItem(descripcion))
        table.setItem(row, COL_GASTO_MONTO, QTableWidgetItem(f"{monto:.2f}"))
        table.blockSignals(False)
        self.recalculate()

    def remove_expense_row(self):
        row = self.view.expenses_table.currentRow()
        if row >= 0:
            self.view.expenses_table.removeRow(row)
            self.recalculate()

    def _add_deliverable_item(self, text):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.view.deliverables_list.addItem(item)
        return item

    def add_deliverable(self):
        item = self._add_deliverable_item("Nuevo entregable")
        self.view.deliverables_list.setCurrentItem(item)
        self.view.deliverables_list.editItem(item)

    def remove_deliverable(self):
        row = self.view.deliverables_list.currentRow()
        if row >= 0:
            self.view.deliverables_list.takeItem(row)

    # ---------------------------------------------------------------- lectura
    def _read_activities(self):
        """Devuelve lista de dicts con las actividades válidas de la tabla."""
        table = self.view.activities_table
        result = []
        for row in range(table.rowCount()):
            def text(col):
                it = table.item(row, col)
                return it.text().strip() if it else ""
            combo = table.cellWidget(row, COL_ROL)
            rol_id = combo.currentData() if combo else None
            rol_nombre = self.roles.get(rol_id, ("",))[0] if rol_id is not None else ""
            result.append({
                "row": row,
                "fase": text(COL_FASE),
                "actividad": text(COL_ACTIVIDAD),
                "rol_id": rol_id,
                "rol": rol_nombre,
                "horas": _to_float(text(COL_HORAS)),
                "tarifa_hora": _to_float(text(COL_TARIFA)),
            })
        return result

    def _read_expenses(self):
        table = self.view.expenses_table
        result = []
        for row in range(table.rowCount()):
            desc_item = table.item(row, COL_GASTO_DESC)
            monto_item = table.item(row, COL_GASTO_MONTO)
            desc = desc_item.text().strip() if desc_item else ""
            monto = _to_float(monto_item.text()) if monto_item else 0.0
            if desc or monto:
                result.append({"descripcion": desc or "Gasto", "monto": monto})
        return result

    def _read_deliverables(self):
        lst = self.view.deliverables_list
        return [lst.item(i).text().strip() for i in range(lst.count()) if lst.item(i).text().strip()]

    @staticmethod
    def _to_calc(activities, expenses):
        acts = [Activity(a["fase"], a["actividad"], a["horas"], a["tarifa_hora"], a["rol"])
                for a in activities if a["actividad"] or a["horas"]]
        exps = [Expense(e["descripcion"], e["monto"]) for e in expenses]
        return acts, exps

    # ----------------------------------------------------------------- cálculo
    def recalculate(self, *_args):
        activities = self._read_activities()
        table = self.view.activities_table
        table.blockSignals(True)
        for a in activities:
            costo_item = table.item(a["row"], COL_COSTO)
            if costo_item:
                costo_item.setText(f"{a['horas'] * a['tarifa_hora']:.2f}")
        table.blockSignals(False)

        acts, exps = self._to_calc(activities, self._read_expenses())
        s = calculate(acts, exps, self.view.contingency_spin.value(),
                      self.view.margin_spin.value(), self.view.itbms_check.isChecked())
        labels = self.view.summary_labels
        labels["horas_totales"].setText(f"{s.horas_totales:g} h")
        for key in ("costo_horas", "gastos", "contingencia", "margen", "subtotal", "itbms"):
            labels[key].setText(f"${getattr(s, key):,.2f}")
        self.view.total_label.setText(f"TOTAL: ${s.total:,.2f}")
        return s

    # --------------------------------------------------------------- plantillas
    def load_template(self):
        template_id = self.view.template_combo.currentData()
        if template_id is None:
            return
        has_content = self.view.activities_table.rowCount() or self.view.deliverables_list.count()
        if has_content and not self.view.ask_yes_no(
                "Esto reemplazará las actividades y entregables actuales. ¿Continuar?"):
            return
        tpl = self.template_model.get_template(template_id)
        self.view.activities_table.setRowCount(0)
        for a in tpl["actividades"]:
            self.add_activity_row(a["fase"], a["actividad"], a["rol_id"], a["horas"], a["tarifa_hora"], a["rol"])
        self.view.deliverables_list.clear()
        for d in tpl["entregables"]:
            self._add_deliverable_item(d)
        self.recalculate()

    def save_template(self):
        activities = [a for a in self._read_activities() if a["actividad"]]
        if not activities:
            self.view.show_error("Agregue al menos una actividad con nombre para guardar la plantilla.")
            return
        nombre = self.view.ask_text("Guardar plantilla", "Nombre de la plantilla:",
                                    self.view.template_combo.currentText())
        if not nombre:
            return
        try:
            self.template_model.save_template(nombre, self.current_type(), activities, self._read_deliverables())
        except Exception as e:
            self.view.show_error(f"Error guardando plantilla: {e}")
            return
        self.load_templates()
        self.view.template_combo.setCurrentText(nombre)
        self.view.show_info(f"Plantilla '{nombre}' guardada.")

    def delete_template(self):
        template_id = self.view.template_combo.currentData()
        if template_id is None:
            return
        nombre = self.view.template_combo.currentText()
        if not self.view.ask_yes_no(f"¿Eliminar la plantilla '{nombre}'?"):
            return
        self.template_model.delete_template(template_id)
        self.load_templates()

    # -------------------------------------------------------------------- roles
    def edit_roles(self):
        dialog = RolesDialog(self.role_model.get_all_roles(), self.view)
        if not dialog.exec():
            return
        rows = dialog.get_rows()
        kept_ids = {r[0] for r in rows if r[0] is not None}
        try:
            for role_id in set(self.roles) - kept_ids:
                self.role_model.delete_role(role_id)
            for role_id, nombre, tarifa, tipo in rows:
                if role_id is None:
                    self.role_model.add_role(nombre, tarifa, tipo)
                else:
                    self.role_model.update_role(role_id, nombre, tarifa, tipo)
        except Exception as e:
            self.view.show_error(f"Error guardando roles: {e}")
        self.load_roles()
        # Refrescar combos (las tarifas de filas existentes no cambian)
        self.on_type_changed(self.current_type())

    # ---------------------------------------------------------------- estimados
    def _collect_data(self):
        """Valida el formulario y devuelve el dict del estimado, o None si hay errores."""
        cliente_id = self.view.client_combo.currentData()
        if not cliente_id:
            self.view.show_error("Debe seleccionar un cliente")
            return None
        proyecto = self.view.project_input.text().strip()
        if not proyecto:
            self.view.show_error("El proyecto es obligatorio")
            return None
        activities = [a for a in self._read_activities() if a["actividad"] or a["horas"]]
        for a in activities:
            if not a["actividad"]:
                self.view.show_error(f"La actividad de la fila {a['row'] + 1} no tiene descripción.")
                return None
            if a["horas"] < 0 or a["tarifa_hora"] < 0:
                self.view.show_error(f"La actividad '{a['actividad']}' tiene horas o tarifa negativas.")
                return None
        if not activities:
            self.view.show_error("Debe agregar al menos una actividad")
            return None
        return {
            "cliente_id": cliente_id,
            "tipo": self.current_type(),
            "proyecto": proyecto,
            "fecha": self.view.date_edit.date().toString("yyyy-MM-dd"),
            "contingencia_pct": self.view.contingency_spin.value(),
            "margen_pct": self.view.margin_spin.value(),
            "aplica_itbms": self.view.itbms_check.isChecked(),
            "notas": self.view.notes_edit.toHtml() if self.view.notes_edit.toPlainText().strip() else "",
            "actividades": activities,
            "gastos": self._read_expenses(),
            "entregables": self._read_deliverables(),
        }

    def _persist(self, data):
        if self.selected_estimate_id:
            self.estimate_model.update_estimate(self.selected_estimate_id, data)
        else:
            self.selected_estimate_id = self.estimate_model.add_estimate(data)
        return self.selected_estimate_id

    def _reselect(self, estimate_id):
        table = self.view.estimates_table
        for row in range(table.rowCount()):
            if table.item(row, 0).text() == str(estimate_id):
                table.blockSignals(True)
                table.selectRow(row)
                table.blockSignals(False)
                self.view.delete_estimate_btn.setEnabled(True)
                return

    def save_estimate(self):
        data = self._collect_data()
        if not data:
            return
        try:
            estimate_id = self._persist(data)
        except Exception as e:
            self.view.show_error(f"Error guardando estimado: {e}")
            return
        self.load_estimates()
        self._reselect(estimate_id)
        self.view.save_btn.setText("Actualizar Estimado")
        self.view.show_info(f"Estimado #{estimate_id} guardado")

    def on_estimate_selected(self):
        selected = self.view.estimates_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        estimate_id = int(self.view.estimates_table.item(row, 0).text())
        data = self.estimate_model.get_estimate(estimate_id)
        if not data:
            return
        self._fill_form(data)
        self.selected_estimate_id = estimate_id
        self.view.save_btn.setText("Actualizar Estimado")
        self.view.delete_estimate_btn.setEnabled(True)

    def _fill_form(self, data):
        v = self.view
        self._select_client(data["cliente_id"])
        v.project_input.setText(data["proyecto"])
        v.date_edit.setDate(QDate.fromString(data["fecha"], "yyyy-MM-dd"))
        for w in (v.contingency_spin, v.margin_spin, v.itbms_check):
            w.blockSignals(True)
        v.contingency_spin.setValue(data["contingencia_pct"])
        v.margin_spin.setValue(data["margen_pct"])
        v.itbms_check.setChecked(data["aplica_itbms"])
        for w in (v.contingency_spin, v.margin_spin, v.itbms_check):
            w.blockSignals(False)
        v.notes_edit.setHtml(data["notas"])

        v.activities_table.setRowCount(0)
        for a in data["actividades"]:
            self.add_activity_row(a["fase"], a["actividad"], a["rol_id"], a["horas"], a["tarifa_hora"], a["rol"])
        v.expenses_table.setRowCount(0)
        for g in data["gastos"]:
            self.add_expense_row(g["descripcion"], g["monto"])
        v.deliverables_list.clear()
        for d in data["entregables"]:
            self._add_deliverable_item(d)
        self.recalculate()

    def clear_form(self):
        v = self.view
        self.selected_estimate_id = None
        v.project_input.clear()
        v.date_edit.setDate(QDate.currentDate())
        v.notes_edit.clear()
        v.activities_table.setRowCount(0)
        v.expenses_table.setRowCount(0)
        v.deliverables_list.clear()
        v.estimates_table.clearSelection()
        v.delete_estimate_btn.setEnabled(False)
        v.save_btn.setText("Guardar Estimado")
        self.recalculate()

    def delete_estimate(self):
        if not self.selected_estimate_id:
            return
        if not self.view.ask_yes_no(
                f"¿Eliminar el estimado #{self.selected_estimate_id}? (La cotización generada, si existe, se conserva)"):
            return
        try:
            self.estimate_model.delete_estimate(self.selected_estimate_id)
        except Exception as e:
            self.view.show_error(f"Error eliminando estimado: {e}")
            return
        self.clear_form()
        self.load_estimates()

    # ---------------------------------------------------------------- cotización
    def generate_quote(self):
        data = self._collect_data()
        if not data:
            return
        try:
            estimate_id = self._persist(data)
        except Exception as e:
            self.view.show_error(f"Error guardando estimado: {e}")
            return

        acts, exps = self._to_calc(data["actividades"], data["gastos"])
        items = build_quote_items(acts, exps, data["contingencia_pct"], data["margen_pct"], data["aplica_itbms"])
        summary = calculate(acts, exps, data["contingencia_pct"], data["margen_pct"], data["aplica_itbms"])

        observaciones = f"<p><b>Esfuerzo estimado:</b> {summary.horas_totales:g} horas.</p>"
        if data["notas"]:
            observaciones += _html_body(data["notas"])
        condiciones = self.business().get("condiciones")
        if condiciones:
            observaciones += _html_body(condiciones)

        existing = self.estimate_model.get_estimate(estimate_id)["cotizacion_id"]
        if existing and not self.estimate_model.quote_exists(existing):
            existing = None
        try:
            if existing and self.view.ask_yes_no(
                    f"Este estimado ya generó la cotización {self._quote_code(existing)}.\n\n"
                    "Sí = actualizar esa cotización\nNo = crear una cotización nueva"):
                quote_id = existing
                self.quote_model.update_quote(quote_id, data["cliente_id"], data["fecha"],
                                              data["proyecto"], observaciones, items, data["entregables"])
                accion = "actualizada"
            else:
                quote_id = self.quote_model.add_quote(data["tipo"], data["cliente_id"], data["fecha"],
                                                      data["proyecto"], observaciones, items, data["entregables"])
                accion = "creada"
            self.estimate_model.link_quote(estimate_id, quote_id)
        except Exception as e:
            self.view.show_error(f"Error generando cotización: {e}")
            return

        self.load_estimates()
        self._reselect(estimate_id)
        self.view.save_btn.setText("Actualizar Estimado")
        self.quote_generated_signal.emit()
        self.view.show_info(
            f"Cotización {self._quote_code(quote_id)} {accion} por ${summary.total:,.2f}.\n"
            "Puede revisarla, enviarla por correo o WhatsApp desde la pestaña Cotizaciones."
        )
