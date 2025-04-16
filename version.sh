#!/bin/bash
# Usuń poprzednie pliki
rm -rf *.egg-info
#rm -rf dist
rm -rf build
# Usuń stare buildy
#rm -rf dist/ build/ *.egg-info/

# publish.sh
#!/bin/bash
echo "Starting publication process..."
python -m venv venv
source venv/bin/activate
# Upewnij się że mamy najnowsze narzędzia
pip install --upgrade pip build twine

# Sprawdź czy jesteśmy w virtualenv
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Aktywuj najpierw virtualenv!"
    exit 1
fi


pip install -r requirements.txt


# Zainstaluj w trybie edytowalnym
pip install -e .
python version/init.py -f src/movatalk/__init__.py
python version/setup.py
python version/src.py
#python version/project.py
python changelog.py
#python increment.py
bash git.sh
bash publish.sh
