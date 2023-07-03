# Gateway docs

To build the docs:

```bash
# Set up Python environment
cd docs
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# Make docs
make html

# Open
xdg-open _build/html/index.html
```
