import os
from pathlib import Path

def init_storage():
    """Initialize storage directories"""
    
    directories = [
        "uploads",
        "static",
        "logs"
    ]
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
    
    print("Storage directories initialized")