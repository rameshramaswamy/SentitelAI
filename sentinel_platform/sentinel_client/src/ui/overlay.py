# sentinel_client/src/ui/overlay.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtGui import QGuiApplication

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.fade_out)

    def init_ui(self):
        # Window Flags: Frameless, On Top, Tool (no taskbar icon)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        # Translucent Background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True) # Click-through

        # Geometry (Top Right Corner)
        # OPTIMIZATION: Dynamic Positioning (Top Right of Primary Screen)
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Width of overlay is 400
        x = screen_geometry.width() - 420 
        y = 50 
        
        self.setGeometry(x, y, 400, 150)
        self.move(1400, 50) # Adjust based on your screen res

        # Layout
        layout = QVBoxLayout()
        self.title_label = QLabel("Sentinel Active")
        self.msg_label = QLabel("Listening...")
        
        # Styling
        self.title_label.setStyleSheet("color: #00FF00; font-weight: bold; font-size: 14pt;")
        self.msg_label.setStyleSheet("color: white; font-size: 12pt;")
        
        # Background Container (Semi-transparent black box)
        self.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            border-radius: 10px;
            padding: 10px;
        """)

        layout.addWidget(self.title_label)
        layout.addWidget(self.msg_label)
        self.setLayout(layout)

    def show_message(self, title: str, message: str, color: str = "#FFFFFF", duration_ms: int = 5000):
        """Updates the overlay content."""
        self.title_label.setText(title)
        self.msg_label.setText(message)
        self.title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14pt;")
        
        self.show()
        # Reset timer
        self.hide_timer.start(duration_ms)

    def fade_out(self):
        self.hide()