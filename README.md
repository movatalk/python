# [movatalk](http://lib.pyfunc.com)

libs for cameramonit, ocr, fin-officer, cfo, and other projects


## Install


```bash
pip install movatalk
```

```bash
git clone https://github.com/pyfunc/lib.git pyfunc
```


## Contributing

```bash
python3 -m venv pytest-env
source pytest-env/bin/activate
```

```bash
pip install --upgrade pip
pip install pytest
```

run the test, execute the pytest command:
```bash
pytest
```



## Tips

simple method to generate a requirements.txt file is to pipe them,
```bash
pip freeze > requirements.txt
pip freeze > requirements/runtime.txt
```

## if push not possible

```
[remote rejected] (refusing to allow a Personal Access Token to create or update workflow `.github/workflows/python-app.yml` without `workflow` scope)
```

Problem z odrzuceniem tokena dostępu osobistego (Personal Access Token, PAT) podczas próby aktualizacji pliku workflow, 
musisz zaktualizować uprawnienia swojego tokena. 

### Oto kroki, które powinieneś podjąć:

1. Przejdź do ustawień GitHub:
   - Kliknij na swój awatar w prawym górnym rogu GitHub
   - Wybierz "Settings"

2. Przejdź do ustawień deweloperskich:
   - W lewym menu wybierz "Developer settings"

3. Zarządzaj tokenami dostępu:
   - Wybierz "Personal access tokens"
   - Następnie "Tokens (classic)"

4. Utwórz nowy token lub zaktualizuj istniejący:
   - Jeśli tworzysz nowy, kliknij "Generate new token"
   - Jeśli aktualizujesz istniejący, znajdź odpowiedni token i kliknij "Edit"

5. Dodaj uprawnienie "workflow":
   - Przewiń do sekcji "Select scopes"
   - Zaznacz pole obok "workflow"

6. Zapisz zmiany:
   - Przewiń na dół i kliknij "Generate token" (dla nowego) lub "Update token" (dla istniejącego)

7. Skopiuj nowy token:
   - Upewnij się, że skopiowałeś nowy token, ponieważ nie będziesz mógł go zobaczyć ponownie

8. Zaktualizuj token w swoim lokalnym repozytorium:
   - Jeśli używasz HTTPS, zaktualizuj swoje dane logowania
   - Jeśli używasz SSH, upewnij się, że Twój klucz SSH jest poprawnie skonfigurowany

9. Spróbuj ponownie wykonać push:
   - Użyj nowego tokena do autoryzacji

Pamiętaj, że tokeny dostępu osobistego są bardzo wrażliwe na bezpieczeństwo.
Traktuj je jak hasła i nigdy nie udostępniaj ich publicznie. Jeśli przypadkowo ujawnisz swój token, natychmiast go usuń i wygeneruj nowy.

Po wykonaniu tych kroków, powinieneś być w stanie zaktualizować plik workflow bez problemów. Jeśli nadal napotkasz problemy, upewnij się, że masz odpowiednie uprawnienia w repozytorium i że workflow nie są zablokowane przez ustawienia organizacji lub repozytorium.

# update PAT in repo
our local repo and want to push it to a remote repo.

create a PAT (personal access token): official doc here. Make sure to tick the box "workflow" when creating it.
In the terminal, instead of the classic

```bash
git remote add origin https://github.com/<account>/<repo>.git
```

swap it by
```bash
git remote add origin https://<PAT>@github.com/<account>/<repo>.git
```
example
```bash
# check
git remote -v
PAT=...
git remote add origin https://$PAT@github.com/pyfunc/lib.git
# OR update:
git remote set-url origin https://$PAT@github.com/pyfunc/lib.git
# check
git remote -v
git push
```

Follow-up with the classic git branch -M main and git push -u origin main

That worked for me. Hopefully for you too.

## pypi publishing

[Creating a PyPI Project with a Trusted Publisher - PyPI Docs](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)



## Creating tags from the command line

To create a tag on your current branch, run this:
```bash
git tag <tagname>
```

If you want to include a description with your tag, add -a to create an annotated tag:
```bash
git tag <tagname> -a
```

This will create a local tag with the current state of the branch you are on. 
When pushing to your remote repo, tags are NOT included by default. 
You will need to explicitly say that you want to push your tags to your remote repo:
```bash
git push origin --tags
```

example:

```bash
git tag 0.1.12
git push origin --tags
```



## test

```bash
pip install build
pip install build hatchling
```


```bash
py -m build
```





## init

The `__init__.py` file is used to mark a directory as a Python package and can also be used to initialize code, define the package's public API, and handle package-level variables or imports.

Here’s a basic guide on preparing the `__init__.py` file for your project located in the `src/movatalk/` directory.

### Basic `__init__.py`

1. **Creating the `__init__.py` File**:
   - Navigate to `src/movatalk/` directory.
   - Create an `__init__.py` file in this directory.

Here is a basic example of what this file might contain:



### Ensuring Proper Package Structure

Here's what your final project structure might look like:

```
my_project/
├── src/
│   └── movatalk/
│       ├── __init__.py
│       ├── module1.py
│       └── module2.py
├── pyproject.toml
├── README.md
└── requirements.txt
```







Hoe generate an `__init__.py` file automatically based on information in `pyproject.toml` typically

Let's break down how you can achieve this:

1. **Understand the data to be included in `__init__.py`**: Essentially, you might want to include metadata (like version), and possibly auto-imports of modules/classes/functions.

2. **Create a script to generate `__init__.py`**: This script would read `pyproject.toml`, extract the relevant information, and generate the `__init__.py` file.

### Step-by-Step Guide

#### Step 1: Install Required Libraries

You will need `toml` for parsing `pyproject.toml`. Install it using `pip`.

```bash
pip install toml
```

#### Step 2: generate_init.py

Create a Python script, e.g., `generate_init.py`, at the root of your project:

Ensure that your `generate_init.py` script runs as part of your build process in your GitHub Actions workflow.

Here's an updated GitHub Actions workflow to include the script execution:

```bash
py generate_init.py -p src/movatalk
py generate_init.py -p src/movatalk/config
py generate_init.py -p src/movatalk/csv
py generate_init.py -p src/movatalk/email
py generate_init.py -p src/movatalk/file
py generate_init.py -p src/movatalk/function
py generate_init.py -p src/movatalk/github
py generate_init.py -p src/movatalk/local
py generate_init.py -p src/movatalk/markdown
py generate_init.py -p src/movatalk/ml
py generate_init.py -p src/movatalk/ocr
py generate_init.py -p src/movatalk/report
py generate_init.py -p src/movatalk/serialization
py generate_init.py -p src/movatalk/text

```

```bash
py -m build
```
```bash
py -m incremental.update movatalk --newversion=0.1.18
py -m incremental.update movatalk --create
py -m incremental.update movatalk --patch

py -m incremental.update movatalk --rc
py -m incremental.update movatalk
```

```bash
pip install dist/movatalk-0.1.15-py3-none-any.whl
```


## validate pyproject.toml

```bash
pip install 'validate-pyproject[all]'
```


```bash
validate-pyproject pyproject.toml
```



## Quick Start

### Local Development
1. Create virtual environment
```bash
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

I see a persistent issue with your package publication process. Let me help you resolve these problems:

1. Version Detection Problem
The error messages show that the version is not being correctly detected:
```
❌ Could not find version in src/movatalk/__init__.py
❌ Could not find version in ./src/movatalk/_version.py
❌ Could not find version in ./pyproject.toml
```

2. License Classifier Issue
There's an ongoing problem with the license classifier in the `pyproject.toml`.

1. Replace your existing `pyproject.toml` with the new version
2. Create `src/movatalk/_version.py` with the content I provided
3. Remove any existing `setup.py` if it exists
4. Use `python -m build` to create distribution
5. Use `twine upload dist/*` to publish

Recommended workflow:
```bash
# Ensure you're in your project root
python -m pip install --upgrade build twine
python -m build
python -m twine upload dist/*
```
