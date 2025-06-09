# localServer.py

from flask import Flask, request
import threading

app = Flask(__name__)
auth_code = None

@app.route('/callback')
def callback():
    global auth_code
    auth_code = request.args.get('code')
    return "<h2>Auth code received. You can close this tab.</h2>"

def start_server():
    thread = threading.Thread(target=lambda: app.run(port=8888, debug=False, use_reloader=False))
    thread.daemon = True
    thread.start()

def get_auth_code():
    return auth_code
