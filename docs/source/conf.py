from importlib.metadata import version as get_version

# Refers to the pypi package name
project = "scw-gateway"

author = "Scaleway Serverless Team"
copyright = f"2023, {author}"

release = get_version(project)
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
