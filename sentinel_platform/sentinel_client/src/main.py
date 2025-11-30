# sentinel_client/src/main.py
import sys
import signal
from PyQt6.QtWidgets import QApplication
from src.ui.overlay import OverlayWindow
from src.core.audio_engine import AudioEngine
from src.core.network import NetworkWorker

def main():
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    
    # 1. Init UI
    overlay = OverlayWindow()
    overlay.show_message("Sentinel", "Initializing...", "#FFFF00")

    # 2. Init Audio
    audio = AudioEngine()
    try:
        audio.start()
    except Exception as e:
        print(f"Audio Error: {e}")
        return

    # 3. Init Network
    worker = NetworkWorker(audio_engine=audio)
    
    # Wire Signals
    worker.sig_connected.connect(
        lambda sid: overlay.show_message("Connected", f"Session: {sid}", "#00FF00")
    )
    
    worker.sig_trigger.connect(
        lambda payload: overlay.show_message(
            payload.content.title, 
            payload.content.message, 
            payload.content.color_hex
        )
    )
    
    worker.sig_error.connect(
        lambda err: overlay.show_message("Error", err, "#FF0000")
    )

    # Start Background Thread
    worker.start()

    # Start Event Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()