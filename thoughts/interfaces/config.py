import json
import os

# Configuration file paths
DEV_CONFIG_FILE = "cortices/config.dev.json"
CONFIG_FILE = "cortices/config.json"

class Config:

    values = None

    def __init__(self):

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the root of the project
        project_root = os.path.abspath(os.path.join(script_dir, "../.."))
        
        # Try dev version first
        dev_config_path = os.path.join(project_root, DEV_CONFIG_FILE)
        config_path = os.path.join(project_root, CONFIG_FILE)
        
        # Load dev config if it exists, otherwise fallback to regular config
        if os.path.exists(dev_config_path):
            actual_config_path = dev_config_path
            # print(f"Loading dev config from: {dev_config_path}")
        else:
            actual_config_path = config_path
            # print(f"Loading config from: {config_path}")

        with open(actual_config_path, "r") as f:
            self.values = json.load(f)