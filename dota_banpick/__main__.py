import sys
from streamlit.web import cli as stcli
import os
import multiprocessing as mps

def main_cli():
    cur_dir = os.path.dirname(__file__)
    entry_file_fp = os.path.join(cur_dir, '1_🎃_Homepage.py')
    sys.argv = ["streamlit", "run", f"{entry_file_fp}"]
    sys.exit(stcli.main())
    
if __name__ == "__main__":
    main_cli()