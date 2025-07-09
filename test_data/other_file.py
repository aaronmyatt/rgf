def another_function():
    print("This file won't match the search pattern")

class AnotherClass:
    def process(self):
        return {"status": "ok"}

def helper_function():
    """A helper function that doesn't match the test pattern"""
    return "helper"

class ConfigManager:
    def __init__(self):
        self.config = {}
    
    def load_config(self, path):
        # Mock config loading
        self.config = {"loaded": True}
