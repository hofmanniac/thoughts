import json

class Config:

    values = None

    def __init__(self):
        with open("config.json", "r") as f:
            self.values = json.load(f)