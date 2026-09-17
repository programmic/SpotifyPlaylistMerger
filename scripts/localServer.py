# localServer.py

from flask import Flask, render_template, request
import threading
import logging
import socket
import sys

app = Flask(__name__)
auth_code = None


@app.route("/callback")
def callback():
    """OAuth redirect endpoint."""
    global auth_code
    auth_code = request.args.get("code")

    # 2. Render the external file from the /templates directory
    return render_template("callback.html")

def is_port_in_use(host: str, port: int) -> bool:
    """Check if a port is already occupied on the host."""
    with socket.socket(socket.AF_SOCKET if hasattr(socket, 'AF_SOCKET') else socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def find_open_port(host: str, start_port: int = 8888, max_port: int = 65535) -> int:
    """Find an open port starting from start_port."""
    for port in range(start_port, max_port + 1):
        if not is_port_in_use(host, port):
            return port
    raise RuntimeError(f"No open ports found in range {start_port}-{max_port}")

def start_server(quiet: bool = False):
    """Start the local flask server after verifying the port is free.

    If quiet is True, suppress werkzeug/flask startup output.
    """
    host = '127.0.0.1'
    port = 8888

    # Spotify requires the redirect URI, including its port, to match exactly.
    if is_port_in_use(host, port):
        raise RuntimeError(
            f"Port {port} is already in use. Stop the other process so Spotify can "
            "redirect to the registered URI."
        )

    if quiet:
        # Reduce verbosity from werkzeug/flask to hide the development server banner
        try:
            logging.getLogger('werkzeug').setLevel(logging.ERROR)
        except Exception:
            pass
        try:
            logging.getLogger('flask.app').setLevel(logging.ERROR)
        except Exception:
            pass

    thread = threading.Thread(target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False))
    thread.daemon = True
    thread.start()

def get_auth_code():
    return auth_code
