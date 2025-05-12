import subprocess
import webbrowser
import time
import os

#pages
PAGE1 = "src/revolve/st_main.py"
PAGE2 = "src/revolve/st_api.py"

#ports
PORT1 = 8501
PORT2 = 8502

HTML_FILE = "iframe.html"

def create_iframe_html():
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Revolve</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
            }}
            iframe {{
                border: none;
            }}
        </style>
    </head>
    <body>
        <div style="display: flex; justify-content: space-around; height: 100vh;">
            <iframe src="http://localhost:{PORT2}" width="18%" height="100%"></iframe>
            <iframe src="http://localhost:{PORT1}" width="82%" height="100%"></iframe>
        </div>
    </body>
    </html>
    """
    with open(HTML_FILE, "w") as f:
        f.write(html_content)
def run_streamlit_app(script, port):
    return subprocess.Popen(
        [
            "streamlit", "run", script,
            "--server.port", str(port),
            "--server.headless", "true"
        ]
    )

if __name__ == "__main__":
    print("🔧 Streamlit apps are starting...")
    p1 = run_streamlit_app(PAGE1, PORT1)
    p2 = run_streamlit_app(PAGE2, PORT2)

    create_iframe_html()

    time.sleep(3)

    # Tarayıcıda aç
    url = f"file://{os.path.abspath(HTML_FILE)}"
    print(f"🌐 Opening in web browser: {url}")
    webbrowser.open(url)

    print("✅ Streamlit apps started. Use Ctrl+C for terminate.")
    try:
        p1.wait()
        p2.wait()
    except KeyboardInterrupt:
        print("\n🛑 Terminating...")
        p1.terminate()
        p2.terminate()