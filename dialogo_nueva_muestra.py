# dialogo_nueva_muestra.py — DendroLen

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QSpinBox, QComboBox, QPushButton, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, QSettings
from constantes import (
    ESPECIES, SETTINGS_ORG, SETTINGS_APP, SETTINGS_ESPECIE,
    cargar_ruta, guardar_ruta, RUTA_ABRIR,
)
from tema_manager import tema as _tema_mgr


def _cargar_especie():
    try:
        return QSettings(SETTINGS_ORG, SETTINGS_APP).value(SETTINGS_ESPECIE, "No registrada")
    except: return "No registrada"

def _guardar_especie(e):
    try: QSettings(SETTINGS_ORG, SETTINGS_APP).setValue(SETTINGS_ESPECIE, e)
    except: pass


class DialogoNuevaMuestra(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva muestra")
        self.setFixedWidth(420)
        self._result = None
        self._ruta_retomar = None
        self._build_ui()

    def _build_ui(self):
        t = _tema_mgr.t
        self.setStyleSheet(f"background-color:{t['BG_CARD']};border-radius:10px;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 18)
        lay.setSpacing(14)

        t1 = QLabel("Nueva muestra")
        t1.setStyleSheet(f"font-size:16px;font-weight:700;color:{t['TEXT_TITLE']};font-family:'Sora','Segoe UI',sans-serif;")
        t2 = QLabel("El radio actual se guardará automáticamente.")
        t2.setStyleSheet(f"font-size:12px;color:{t['TEXT_DIM']};")
        lay.addWidget(t1); lay.addWidget(t2)

        # Código + Año
        row1 = QHBoxLayout(); row1.setSpacing(12)
        c1 = QVBoxLayout(); c1.setSpacing(5)
        c1.addWidget(self._lbl("Código"))
        self.inp_codigo = QLineEdit()
        self.inp_codigo.setPlaceholderText("ej. MUE002A")
        self.inp_codigo.setMinimumHeight(34)
        c1.addWidget(self.inp_codigo)
        c2 = QVBoxLayout(); c2.setSpacing(5)
        c2.addWidget(self._lbl("Año inicio"))
        self.spn_anio = QSpinBox()
        self.spn_anio.setRange(-10000, 2200)
        self.spn_anio.setValue(1850)
        self.spn_anio.setMinimumHeight(34)
        c2.addWidget(self.spn_anio)
        row1.addLayout(c1, 3); row1.addLayout(c2, 2)
        lay.addLayout(row1)

        # Especie editable
        e_lay = QVBoxLayout(); e_lay.setSpacing(5)
        e_lay.addWidget(self._lbl("Especie"))
        self.cmb_especie = QComboBox()
        self.cmb_especie.setEditable(True)
        self.cmb_especie.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
        self.cmb_especie.setMinimumHeight(34)
        self.cmb_especie.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for e in ESPECIES: self.cmb_especie.addItem(e)
        ultima = _cargar_especie()
        idx = self.cmb_especie.findText(ultima)
        if idx >= 0: self.cmb_especie.setCurrentIndex(idx)
        else: self.cmb_especie.setEditText(ultima)
        e_lay.addWidget(self.cmb_especie)
        lay.addLayout(e_lay)

        # Continuar una serie que ya tiene archivo guardado
        self.btn_abrir = QPushButton("📂  Abrir archivo")
        self.btn_abrir.setMinimumHeight(34)
        self.btn_abrir.setStyleSheet(f"""
            QPushButton {{
                background-color:{t['BG_CARD']};border:2px solid {t['BORDER']};
                border-radius:7px;color:{t['BLUE']};font-size:13px;
                font-weight:600;padding:0 14px;
            }}
            QPushButton:hover {{border-color:{t['BLUE']};}}
        """)
        self.btn_abrir.clicked.connect(self._abrir_existente)
        lay.addWidget(self.btn_abrir)

        self.lbl_retoma = QLabel("")
        self.lbl_retoma.setWordWrap(True)
        self.lbl_retoma.setStyleSheet(f"font-size:12px;color:{t['TEXT_DIM']};")
        self.lbl_retoma.hide()
        lay.addWidget(self.lbl_retoma)

        # Botones
        foot = QHBoxLayout(); foot.setSpacing(10)
        foot.addStretch()
        cancel = QPushButton("Cancelar")
        cancel.setMinimumHeight(34)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("▷  Iniciar")
        ok.setMinimumHeight(34)
        ok.setStyleSheet(f"""
            QPushButton {{
                background-color:{t['GREEN']};border:none;border-radius:7px;
                color:white;font-size:14px;font-weight:700;padding:0 20px;
            }}
            QPushButton:hover{{background-color:#2ecc71;}}
        """)
        ok.clicked.connect(self._confirmar)
        foot.addWidget(cancel); foot.addWidget(ok)
        lay.addLayout(foot)

    def _lbl(self, text):
        t = _tema_mgr.t
        l = QLabel(text.upper())
        l.setStyleSheet(f"font-size:11px;color:{t['TEXT_DIM']};letter-spacing:1px;font-weight:700;")
        return l

    def _abrir_existente(self):
        """Carga un .rwl ya guardado para seguir midiendo esa misma serie."""
        from dialogo_config import _leer_mediciones_rwl
        t = _tema_mgr.t
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo de medición",
            cargar_ruta(RUTA_ABRIR),
            "Tucson (*.rwl *.RWL *.txt *.TXT);;Todos los archivos (*)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if not ruta:
            return
        guardar_ruta(RUTA_ABRIR, ruta)
        cod, anio, meds = _leer_mediciones_rwl(ruta)
        if not cod:
            self.lbl_retoma.setText("⚠  No se pudo leer ese archivo.")
            self.lbl_retoma.setStyleSheet(f"font-size:12px;color:{t['ORANGE']};")
            self.lbl_retoma.show()
            return
        self._ruta_retomar = ruta
        self.inp_codigo.setText(cod)
        if anio is not None:
            self.spn_anio.setValue(int(anio))
        self.lbl_retoma.setText(
            f"✓ {os.path.basename(ruta)} · {len(meds)} anillos · "
            f"se continuará desde el año {(anio or 0) + len(meds)}")
        self.lbl_retoma.setStyleSheet(f"font-size:12px;color:{t['BLUE']};")
        self.lbl_retoma.show()

    def _confirmar(self):
        codigo = self.inp_codigo.text().strip()
        if not codigo: self.inp_codigo.setFocus(); return
        especie = self.cmb_especie.currentText().strip() or "No registrada"
        _guardar_especie(especie)
        self._result = {
            "codigo": codigo, "anio": self.spn_anio.value(),
            "serie": codigo, "especie": especie,
            "archivo": self._ruta_retomar or f"{codigo}.rwl",
            "ruta_retomar": self._ruta_retomar,
        }
        self.accept()

    def get_result(self):
        return self._result
