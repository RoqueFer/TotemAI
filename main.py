import sys
import os


project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connector import init_db
from ui.interface import AITotemApp


def main():
    
    init_db()
    
    AITotemApp().run()

if __name__ == '__main__':
    main()

