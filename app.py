import os
import sys

# Add the project directory to the sys.path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Import the Django WSGI application
from dishdecode_project.wsgi import application

# Render and other hosts look for a variable named 'app' or 'application'
app = application
