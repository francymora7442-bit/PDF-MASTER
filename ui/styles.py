"""Hoja de estilos (blanco, gris claro y azul)."""

STYLESHEET = """
* { font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif; font-size: 10.5pt; color: #111827; }
QMainWindow, QDialog, QMessageBox { background: #FFFFFF; }
QWidget#Content { background: #FFFFFF; }
QStatusBar { background: #F9FAFB; border-top: 1px solid #E5E7EB; color: #6B7280; }
QStatusBar QLabel { color: #6B7280; }

#Sidebar { background: #F3F4F6; border-right: 1px solid #E5E7EB; }
#Logo { font-size: 18pt; font-weight: 700; color: #1D4ED8; }
#LogoSub { color: #6B7280; font-size: 9pt; }
#SidebarFooter { color: #6B7280; font-size: 9pt; }
QPushButton#NavButton { text-align: left; padding: 12px 16px; border: none; border-radius: 10px;
    background: transparent; color: #374151; font-weight: 500; }
QPushButton#NavButton:hover { background: #E5E7EB; }
QPushButton#NavButton:checked { background: #DBEAFE; color: #1D4ED8; font-weight: 600; }

#PageTitle { font-size: 20pt; font-weight: 700; color: #111827; }
#PageSubtitle { color: #6B7280; }
#Hint { color: #6B7280; }
#Status { color: #374151; font-weight: 500; }
#Dirty { color: #B45309; font-weight: 600; }

QPushButton { background: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 8px; padding: 6px 14px; font-weight: 500; }
QPushButton:hover { background: #F3F4F6; border-color: #9CA3AF; }
QPushButton:pressed { background: #E5E7EB; }
QPushButton:disabled { color: #9CA3AF; background: #F9FAFB; border-color: #E5E7EB; }
QPushButton[role="primary"] { background: #2563EB; border: 1px solid #2563EB; color: #FFFFFF;
    font-weight: 700; font-size: 11.5pt; padding: 10px 20px; }
QPushButton[role="primary"]:hover { background: #1D4ED8; border-color: #1D4ED8; }
QPushButton[role="primary"]:disabled { background: #93C5FD; border-color: #93C5FD; color: #FFFFFF; }
QPushButton[role="danger"] { color: #B91C1C; border-color: #FCA5A5; }
QPushButton[role="danger"]:hover { background: #FEF2F2; border-color: #F87171; }
QPushButton[role="card"] { text-align: left; padding: 20px; border: 1px solid #E5E7EB; border-radius: 14px;
    background: #F9FAFB; font-size: 11.5pt; font-weight: 500; }
QPushButton[role="card"]:hover { border-color: #2563EB; background: #EFF6FF; }

QListWidget { border: 1px solid #E5E7EB; border-radius: 10px; background: #FFFFFF; padding: 4px; outline: 0; }
QListWidget::item { padding: 6px; border-radius: 8px; }
QListWidget::item:hover { background: #F3F4F6; }
QListWidget::item:selected { background: #DBEAFE; color: #1E3A8A; }

QLineEdit, QComboBox, QSpinBox { border: 1px solid #D1D5DB; border-radius: 8px; padding: 6px 10px;
    background: #FFFFFF; min-height: 22px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #2563EB; }
QComboBox QAbstractItemView { border: 1px solid #D1D5DB; background: #FFFFFF; selection-background-color: #DBEAFE;
    selection-color: #1E3A8A; }

QProgressBar { border: none; background: #E5E7EB; border-radius: 6px; min-height: 12px; max-height: 12px; text-align: center; }
QProgressBar::chunk { background: #2563EB; border-radius: 6px; }

QGroupBox { border: 1px solid #E5E7EB; border-radius: 10px; margin-top: 14px; padding: 16px 12px 10px 12px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #374151; }

QTableWidget { border: 1px solid #E5E7EB; border-radius: 10px; gridline-color: #F3F4F6; background: #FFFFFF;
    alternate-background-color: #F9FAFB; selection-background-color: #DBEAFE; selection-color: #1E3A8A; outline: 0; }
QHeaderView::section { background: #F3F4F6; border: none; border-bottom: 1px solid #E5E7EB; padding: 8px; font-weight: 600; }

QLabel#Preview { background: #F9FAFB; border: 1px dashed #D1D5DB; border-radius: 10px; color: #9CA3AF; }

QSlider::groove:horizontal { height: 4px; background: #D1D5DB; border-radius: 2px; }
QSlider::handle:horizontal { background: #2563EB; width: 14px; margin: -6px 0; border-radius: 7px; }
QSlider::sub-page:horizontal { background: #93C5FD; border-radius: 2px; }

QScrollBar:vertical { width: 10px; background: transparent; margin: 2px; }
QScrollBar::handle:vertical { background: #D1D5DB; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #9CA3AF; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { height: 10px; background: transparent; margin: 2px; }
QScrollBar::handle:horizontal { background: #D1D5DB; border-radius: 4px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QMenu { background: #FFFFFF; border: 1px solid #E5E7EB; padding: 4px; }
QMenu::item { padding: 8px 22px; border-radius: 6px; }
QMenu::item:selected { background: #DBEAFE; color: #1E3A8A; }
QToolTip { background: #111827; color: #FFFFFF; border: none; padding: 4px 8px; }
"""
