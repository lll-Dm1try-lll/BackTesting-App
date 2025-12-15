from __future__ import annotations

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../.."))

project = "Backtester"
author = "Дмитрий Т."
year = datetime.now().year
copyright = f"{year}, {author}"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = ["_build"]

html_theme = "alabaster"
html_static_path = ["_static"]
