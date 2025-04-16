# [movatalk](http://lib.movatalk.com)

# System pipelinów KidsVoiceAI

System pipelinów KidsVoiceAI umożliwia tworzenie złożonych aplikacji głosowych za pomocą prostych plików konfiguracyjnych YAML, bez konieczności pisania kodu w Pythonie. Pipelines łączą gotowe komponenty i operacje w jeden spójny przepływ pracy.

## Spis treści

1. [Wprowadzenie do pipelinów](#wprowadzenie-do-pipelinów)
2. [Struktura pliku YAML](#struktura-pliku-yaml)
3. [Komponenty pipelinów](#komponenty-pipelinów)
4. [Zmienne i kontekst](#zmienne-i-kontekst)
5. [Kroki warunkowe i pętle](#kroki-warunkowe-i-pętle)
6. [Programistyczne użycie pipelinów](#programistyczne-użycie-pipelinów)
7. [Tworzenie własnych komponentów](#tworzenie-własnych-komponentów)
8. [Kreator pipelinów](#kreator-pipelinów)
9. [Wizualizacja pipelinów](#wizualizacja-pipelinów)
10. [Przykłady](#przykłady)

## Wprowadzenie do pipelinów

Pipeline to sekwencja kroków, które są wykonywane kolejno, aby osiągnąć określony cel. W kontekście KidsVoiceAI, pipeline może reprezentować na przykład asystenta głosowego, który:

1. Słucha pytania użytkownika
2. Przetwarza mowę na tekst
3. Wysyła zapytanie do modelu językowego
4. Filtruje odpowiedź pod kątem bezpieczeństwa
5. Zamienia tekst na mowę i odtwarza odpowiedź

Zamiast pisać kod w Pythonie, możesz zdefiniować taki przepływ pracy w pliku YAML, który jest łatwy do czytania i modyfikacji.

## Struktura pliku YAML

Plik pipeline'u YAML składa się z następujących elementów:

```yaml
name: "Nazwa pipeline'u"
description: "Opis działania pipeline'u"
version: "1.0.0"

variables:
  zmienna1: "wartość1"
  zmienna2: "wartość2"

steps:
  - name: "k
```


## Install


```bash
pip install movatalk
```

```bash
git clone https://github.com/movatalk/python.git movatalk
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
git remote add origin https://$PAT@github.com/movatalk/python.git
# OR update:
git remote set-url origin https://$PAT@github.com/movatalk/python.git
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
