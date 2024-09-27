import sys
import os

# Project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.main import main

if __name__ == '__main__':
    main()