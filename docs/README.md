# Gateway docs

To build the docs (from the root of this project):

```bash
cd cli
poetry install --with doc
poetry shell

cd ../docs
make html
xdg-open build/html/index.html
```
