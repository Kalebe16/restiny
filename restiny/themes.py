from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette


def system(app):
    app.setPalette(QPalette())
    app.setStyleSheet('')


def dark_amber(app):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.Base, QColor(45, 45, 45))
    palette.setColor(QPalette.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.Button, QColor(60, 60, 60))
    palette.setColor(QPalette.ButtonText, QColor(230, 230, 230))
    palette.setColor(
        QPalette.Disabled, QPalette.ButtonText, QColor(120, 120, 120)
    )
    palette.setColor(QPalette.Disabled, QPalette.Button, QColor(50, 50, 50))
    palette.setColor(QPalette.Highlight, QColor(255, 190, 100))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    app.setStyleSheet("""
        QPushButton {
            background-color: #3c3c3c;
            color: #e6e6e6;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover { background-color: #4c4c4c; }
        QPushButton:disabled { background-color: #2a2a2a; color: #777; }

        QLineEdit:focus { border: 2px solid #FFBE64; }

        QMenu { background-color: #2c2c2c; color: #e6e6e6; }
        QMenu::item:selected { background-color: #FFBE64; color: #000; }

        QTreeWidget::item:selected,
        QListWidget::item:selected { background-color: #FFBE64; color: #000; }
    """)


def light_amber(app):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(250, 245, 235))
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, QColor(240, 235, 225))
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(
        QPalette.Disabled, QPalette.ButtonText, QColor(150, 150, 150)
    )
    palette.setColor(QPalette.Disabled, QPalette.Button, QColor(230, 225, 215))
    palette.setColor(QPalette.Highlight, QColor(255, 200, 120))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    app.setStyleSheet("""
        QPushButton {
            background-color: #f0ebe1;
            color: #000;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover { background-color: #e2dbcf; }
        QPushButton:disabled { background-color: #ddd6c9; color: #999; }

        QLineEdit:focus { border: 2px solid #FFC878; }

        QMenu { background-color: #f0ebe1; color: #000; }
        QMenu::item:selected { background-color: #FFC878; color: #000; }

        QTreeWidget::item:selected,
        QListWidget::item:selected { background-color: #FFC878; color: #000; }
    """)
