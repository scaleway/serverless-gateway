project = "scw_gateway"
author = "Scaleway Serverless Team"
project_copyright = f"2023, {author}"
release = "0.0.1"
version = release

extensions = [
    "sphinx_rtd_theme",
    "myst_parser",  # Markdown
    "sphinx.ext.autodoc",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
