import subprocess

import streamlit as st
import random
import time
from src.revolve.main import run_workflow
from src.revolve.functions import test_db
import os
import streamlit as st
import os
import time

code_dir = "src/revolve/source_generated"

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def render_sidebar_controls(code_dir):
    """Renders server controls in the sidebar."""

    py_files = [f for f in os.listdir(code_dir) if f.endswith(".py")] if os.path.isdir(code_dir) else []
    code_available = len(py_files) > 0

    col1, col2 = st.columns([1, 1])

    with col1:
        st.button("Start", key="start_server", on_click=start_process)

    with col2:
        st.button("Stop", key="stop_server", on_click=stop_process)

    # Show server status
    pid = st.session_state.get("process_pid")
    if pid:
        st.success(f"Server up {st.session_state.get('process_link')})")
    else:
        st.warning("Server is not running")

def start_process():
    if "process_pid" not in st.session_state:
        st.session_state["process_pid"] = None
        st.session_state["process_started"] = False

    COMMAND = ["python", "api.py"]
    env_vars = os.environ.copy()
    env_vars["PORT"] = os.environ.get("PORT", str(random.randint(1024, 65535)))
    env_vars["STATIC_DIR"] = os.environ.get("STATIC_DIR", "-")
    try:
        process = subprocess.Popen(COMMAND, cwd=code_dir, env=env_vars)
        st.session_state["process_pid"] = process.pid
        st.session_state["process_started"] = True
        link = f"http://localhost:{env_vars['PORT']}"
        st.session_state["process_link"] =  link

    except Exception as e:
        print(f"Error starting the server: {e}")
        return None

def stop_process():
    pid = st.session_state.get("process_pid")
    if pid:
        os.kill(pid, 9)
        st.success(f"Process with PID {pid} stopped")
        st.session_state["process_pid"] = None
        st.session_state["link"] = None
    else:
        st.warning("No process is running")

api_file_path = os.path.join(code_dir, "api.py")

def check_api_file():
    return os.path.exists(api_file_path)

while not check_api_file():
    time.sleep(3)
    st.rerun()

render_sidebar_controls(code_dir)

