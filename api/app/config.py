

import os

import doctr

PROJECT_NAME: str = "docTR API template"
PROJECT_DESCRIPTION: str = "Template API for Optical Character Recognition"
VERSION: str = doctr.__version__
DEBUG: bool = os.environ.get("DEBUG", "") != "False"
