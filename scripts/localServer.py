# localServer.py

from flask import Flask, request, make_response
import threading

app = Flask(__name__)
auth_code = None


@app.route('/callback')
def callback():
        """OAuth redirect endpoint.

        Returns an HTML page that will attempt to automatically close the tab/window
        and notify any opener via postMessage. Note: modern browsers restrict
        programmatic window closing for tabs not opened by script; this is a
        best-effort approach.
        """
        global auth_code
        auth_code = request.args.get('code')

        html = '''<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>Authentication complete</title>
        <style>body{font-family:Arial,Helvetica,sans-serif;text-align:center;padding:2rem}</style>
    </head>
    <body>
        <h2>Authentication complete</h2>
        <p>This window will attempt to close automatically. If it does not,
            please close it and return to the application.</p>
        <div id="fallback" style="display:none;margin-top:1rem">
            <button onclick="tryClose()">Close this tab</button>
        </div>
        <script>
            function tryClose(){
                try{
                    // Notify opener if present
                    if(window.opener && !window.opener.closed){
                        try{ window.opener.postMessage({type:'spotify_auth', status:'ok'}, '*'); }catch(e){}
                    }
                    // Many browsers block window.close() for tabs not opened by script.
                    // Try a few strategies.
                    window.open('', '_self');
                    window.close();
                    // If still not closed, show fallback button
                    document.getElementById('fallback').style.display = 'block';
                }catch(e){
                    document.getElementById('fallback').style.display = 'block';
                }
            }
            // Try to close shortly after loading
            setTimeout(tryClose, 200);
        </script>
    </body>
</html>'''

        resp = make_response(html)
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        return resp


def start_server():
        thread = threading.Thread(target=lambda: app.run(port=8888, debug=False, use_reloader=False))
        thread.daemon = True
        thread.start()


def get_auth_code():
        return auth_code
