"""
Neon Lights Windows Controller Application
Main Entry Point - React Desktop Edition
"""
import sys
import os
import time
import logging

# Ensure package directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import webview
from neon_controller.server import NeonHttpServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("NeonApp")


def run():
    server = NeonHttpServer(host="127.0.0.1", port=8765)
    server.start()

    window = webview.create_window(
        title="Neon Lights Studio",
        url="http://127.0.0.1:8765",
        width=1180,
        height=820,
        min_size=(950, 680),
        background_color="#080A11",
    )
    try:
        webview.start()
    except Exception as ex:
        logger.warning(f"Native window error: {ex}. Opening in browser fallback...")
        import webbrowser
        webbrowser.open("http://127.0.0.1:8765")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    finally:
        server.stop()


if __name__ == "__main__":
    run()
