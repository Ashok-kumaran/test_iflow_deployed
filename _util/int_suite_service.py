import os, subprocess, time
from urllib.parse import urlparse
from datetime import datetime

def i_flow_path(i_flow_name: str) -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_dir = os.path.join(project_root, "_temp/integration_suite", "i_flow")
    os.makedirs(base_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # print(f"🐞 ts: {ts}")

    dest_path = os.path.join(base_dir, f"{i_flow_name}.zip")
    return os.path.normpath(dest_path)

def i_package_path(i_package_name: str) -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_dir = os.path.join(project_root, "_temp/integration_suite", "i_package")
    os.makedirs(base_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # print(f"🐞 ts: {ts}")

    dest_path = os.path.join(base_dir, f"{i_package_name}.zip")
    return os.path.normpath(dest_path)
