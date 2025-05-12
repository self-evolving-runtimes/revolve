import subprocess

import streamlit as st
import random
import time
from src.revolve.main import run_workflow
from src.revolve.functions import test_db
import os

code_dir = "src/revolve/source_generated"

predefined_prompts = [
    "Create CRUD operations for all the tables",
    "Generate API endpoints for the user table",
    "Check the code and refactor it",
    "Run the tests and fix the errors",
    "Create CRUD operations for the doctors table",
]

if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_file_viewer" not in st.session_state:
    st.session_state.show_file_viewer = True

if "show_ribbon" not in st.session_state:
    st.session_state.show_ribbon = True
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

st.markdown(
    """
    <style>
    .ribbon-btn-small {
        font-size: 10px !important;
        line-height: 1.15em !important;
        height: 3em !important;
        padding: 0.25em 0.6em !important;
        border-radius: 1.2em !important;
        white-space: pre-line !important;
        margin-bottom: 0.2em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Revolve")

readme_message = """
## Welcome to Revolve

**Revolve** is an agent-based code generation and editing tool designed to streamline your development workflow.

### Getting Started

1. Configure your database connection.
2. Enter a task prompt describing what you want to build.

### What Can Revolve Do?

- Generate API endpoints based on your prompt.
- Create service files with the required business logic.
- Automatically write and include test cases for the generated code.
- Continuously edit and refine existing code to match evolving requirements.
"""

with st.expander("📖 Readme", expanded=False):
    st.markdown(readme_message)

with st.expander("🔧 Database Configuration", expanded=False):
    db_name = st.text_input("DB_NAME", value="newdb")
    db_user = st.text_input("DB_USER", value="postgres")
    db_password = st.text_input("DB_PASSWORD", value="admin", type="password")
    db_host = st.text_input("DB_HOST", value="localhost")
    db_port = st.text_input("DB_PORT", value="5432")
    if st.button("Test Connection", use_container_width=True):
        try:
            result = test_db(
                db_name=db_name,
                db_user=db_user,
                db_password=db_password,
                db_host=db_host,
                db_port=db_port,
            )
            if result:
                st.toast("✅ Connection successful!", icon="🎉")
            else:
                st.toast("❌ Connection failed.", icon="⚠️")
        except Exception as e:
            st.toast(f"❌ Error: {str(e)}", icon="⚠️")

with st.expander("📂 Generated Resource", expanded=False):
    if os.path.isdir(code_dir):
        py_files = [f for f in os.listdir(code_dir) if f.endswith(".py")]

        if py_files and st.session_state.show_file_viewer:
            col1, col2 = st.columns([1, 3])

            with col1:
                selected_file = st.selectbox(
                    "Select a file", ["-- Select --"] + py_files
                )
                if st.button("🧹 Wipe Folder"):
                    for file in py_files:
                        os.remove(os.path.join(code_dir, file))
                    st.session_state.show_file_viewer = False
                    st.rerun()

            with col2:
                if selected_file and selected_file != "-- Select --":
                    file_path = os.path.join(code_dir, selected_file)
                    with open(file_path, "r") as f:
                        file_content = f.read()
                    st.code(file_content, language="python")
                else:
                    st.info("Select a Python file to preview.")

        elif not py_files:
            st.info("No Python files found in this directory.")
    else:
        st.warning("Directory not found.")

if st.session_state.show_ribbon:
    st.markdown("**🚀 Quick Start**")
    ribbon_cols = st.columns(len(predefined_prompts))
    for i, prompt_text in enumerate(predefined_prompts):
        with ribbon_cols[i]:
            btn_label = f":blue[{prompt_text}]"
            if st.button(btn_label, key=f"ribbon_{i}", help=prompt_text):
                st.session_state.pending_prompt = prompt_text.replace("\n", " ")
                st.session_state.show_ribbon = False
                st.rerun()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

status_messages = [
    "🌐 Connecting the dots...",
    "📦 Wrapping things up...",
    "🧠 Thinking it through...",
    "💡 Coming up with ideas...",
    "🔧 Setting things up...",
    "📡 Syncing with the server...",
    "🕓 Hang tight, almost there...",
    "🔬 Fine-tuning the details...",
    "🌀 Just a moment...",
    "✨ It's happening...",
    "🎛️ Running your request...",
    "🎲 Working behind the scenes...",
]
status_placeholder = st.empty()
status_update_interval = 5
last_status_update = 0
current_status_message = None

if "system_logs" not in st.session_state:
    st.session_state.system_logs = []

with st.sidebar.expander("📝 System Messages"):
    if len(st.session_state.system_logs) > 0:
        md = "\n\n".join(st.session_state.system_logs)
        st.markdown(md)
    status_function_placeholder = st.empty()

def render_sidebar_controls(code_dir):
    """Renders server controls in the sidebar."""

    py_files = [f for f in os.listdir(code_dir) if f.endswith(".py")] if os.path.isdir(code_dir) else []
    code_available = len(py_files) > 0

    with st.sidebar.expander("⚡ Server Controls", expanded=True):
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


def response_generator(prompt):
    db_config = {
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
        "DB_HOST": db_host,
        "DB_PORT": db_port,
    }
    model_response = run_workflow(prompt, db_config=db_config)
    return model_response


chat_input = st.chat_input("Enter prompt?")
if chat_input:
    st.session_state.pending_prompt = chat_input
    st.session_state.show_ribbon = False
    st.rerun()

# Execute the sidebar controls function
render_sidebar_controls(code_dir)

prompt = st.session_state.get("pending_prompt")
if prompt:
    function_messages = []
    st.session_state.pending_prompt = None  # So it doesn't repeat
    with st.spinner("", show_time=True):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        for response_object in response_generator(st.session_state.messages):
            if response_object["yield"] == False:
                with st.chat_message("assistant"):
                    response_text = response_object["text"]
                    st.write(response_text)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response_text}
                    )

                    # Check if the response is "Task completed."
                    if "Task completed." in response_text:
                        st.session_state.show_preview = True

                    py_files = [f for f in os.listdir(code_dir) if f.endswith(".py")]
                    if py_files:
                        st.session_state.show_file_viewer = True
                    st.rerun()
            else:
                now = time.time()
                if (now - last_status_update > status_update_interval) or (
                    current_status_message is None
                ):
                    current_status_message = random.choice(status_messages)
                    status_placeholder.info(current_status_message)
                    last_status_update = now
                else:
                    status_placeholder.info(current_status_message)

                text = response_object["text"]
                func = response_object["name"]

                new_log = f"**{func}:**\n\n```python\n{text[:1000]}...\n```"
                function_messages.append(new_log)
                st.session_state.system_logs.append(new_log)

                md = "\n\n".join(function_messages)
                status_function_placeholder.markdown(md)

                # if "generate_api" == func:
                #     with st.chat_message("assistant"):
                #         st.session_state.messages.append(
                #             {"role": "assistant",
                #              "content":  text
                #              }
                #         )
                #         st.write(
                #             text
                #            )

