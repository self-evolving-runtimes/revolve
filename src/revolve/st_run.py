import streamlit.web.cli as stcli
import sys

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "src/revolve/st_main.py"]
    # Place a breakpoint here if using an IDE debugger
    stcli.main()
