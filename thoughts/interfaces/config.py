import json

class Config:

    values = None

    def __init__(self):

        import os

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the root of the project
        project_root = os.path.abspath(os.path.join(script_dir, "../.."))
        # Construct the full path to the config.json file
        config_path = os.path.join(project_root, "config.json")

        # print(f"Loading config from: {config_path}")

        with open(config_path, "r") as f:
            self.values = json.load(f)