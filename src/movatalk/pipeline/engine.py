# movatalk/pipeline/engine.py
"""
Silnik wykonujący pipeline'y zdefiniowane w DSL.
"""

import os
import time
import threading
import importlib
import subprocess
from typing import Dict, Any, List, Callable, Union, Optional


class PipelineEngine:
    """
    Silnik wykonujący pipeline'y zdefiniowane w DSL.
    """

    def __init__(self, registry=None):
        """
        Inicjalizacja silnika pipelinów.

        Args:
            registry (ComponentRegistry, optional): Rejestr komponentów.
                                                  Jeśli None, zostanie utworzony nowy.
        """
        if registry is None:
            from movatalk.pipeline.components import ComponentRegistry
            self.registry = ComponentRegistry()
        else:
            self.registry = registry

        self.current_pipeline = None
        self.pipeline_context = {}
        self.running = False
        self.execution_thread = None

    def load_pipeline(self, pipeline_config):
        """
        Wczytaj pipeline z konfiguracji.

        Args:
            pipeline_config (dict): Konfiguracja pipeline'a.

        Returns:
            bool: True jeśli pipeline został wczytany pomyślnie, False w przeciwnym razie.
        """
        try:
            self.current_pipeline = pipeline_config
            self.pipeline_context = {
                'variables': pipeline_config.get('variables', {}),
                'state': {},
                'results': {},
                'errors': []
            }
            return True
        except Exception as e:
            print(f"Błąd ładowania pipeline'a: {str(e)}")
            return False

    def load_pipeline_from_file(self, file_path):
        """
        Wczytaj pipeline z pliku YAML.

        Args:
            file_path (str): Ścieżka do pliku YAML.

        Returns:
            bool: True jeśli pipeline został wczytany pomyślnie, False w przeciwnym razie.
        """
        try:
            from movatalk.pipeline.parser import YamlParser
            parser = YamlParser()
            pipeline_config = parser.parse_file(file_path)
            return self.load_pipeline(pipeline_config)
        except Exception as e:
            print(f"Błąd ładowania pipeline'a z pliku: {str(e)}")
            return False

    def start(self, async_mode=False):
        """
        Uruchom aktualnie załadowany pipeline.

        Args:
            async_mode (bool): Czy uruchomić pipeline asynchronicznie.

        Returns:
            Union[bool, threading.Thread]: True/False jeśli synchronicznie,
                                          Thread jeśli asynchronicznie.
        """
        if self.current_pipeline is None:
            print("Błąd: Brak załadowanego pipeline'a.")
            return False

        if self.running:
            print("Pipeline już jest uruchomiony.")
            return False

        self.running = True

        if async_mode:
            self.execution_thread = threading.Thread(target=self._execute_pipeline)
            self.execution_thread.daemon = True
            self.execution_thread.start()
            return self.execution_thread
        else:
            return self._execute_pipeline()

    def stop(self):
        """
        Zatrzymaj aktualnie uruchomiony pipeline.

        Returns:
            bool: True jeśli pipeline został zatrzymany, False w przeciwnym razie.
        """
        if not self.running:
            return False

        self.running = False

        if self.execution_thread and self.execution_thread.is_alive():
            self.execution_thread.join(timeout=2.0)

        return True

    def _execute_pipeline(self):
        """
        Wykonaj aktualnie załadowany pipeline.

        Returns:
            bool: True jeśli pipeline został wykonany pomyślnie, False w przeciwnym razie.
        """
        if not self.current_pipeline or not self.running:
            return False

        try:
            # Wykonaj kroki pipeline'a
            steps = self.current_pipeline.get('steps', [])

            for step_index, step in enumerate(steps):
                if not self.running:
                    print("Pipeline został zatrzymany.")
                    return False

                step_name = step.get('name', f"step_{step_index}")
                print(f"Wykonywanie kroku: {step_name}")

                # Wykonaj krok i zapisz wynik
                success, result = self._execute_step(step)

                self.pipeline_context['results'][step_name] = result

                # Jeśli krok się nie powiódł i nie ma flagi continue_on_error, przerwij pipeline
                if not success and not step.get('continue_on_error', False):
                    print(f"Krok {step_name} zakończył się niepowodzeniem. Zatrzymuję pipeline.")
                    self.running = False
                    return False

            print("Pipeline zakończony pomyślnie.")
            self.running = False
            return True

        except Exception as e:
            print(f"Błąd wykonania pipeline'a: {str(e)}")
            self.running = False
            return False

    def _execute_step(self, step):
        """
        Wykonaj pojedynczy krok pipeline'a.

        Args:
            step (dict): Konfiguracja kroku.

        Returns:
            tuple: (success, result) - Czy krok zakończył się sukcesem i jego wynik.
        """
        try:
            step_type = step.get('type')

            if not step_type:
                raise ValueError("Brak typu dla kroku.")

            # Sprawdź czy warunek dla kroku jest spełniony
            if not self._evaluate_condition(step.get('if')):
                print(f"Warunek dla kroku {step.get('name')} nie jest spełniony. Pomijam.")
                return True, None

            # Wykonaj krok w zależności od typu
            if step_type == 'component':
                return self._execute_component_step(step)
            elif step_type == 'shell':
                return self._execute_shell_step(step)
            elif step_type == 'python':
                return self._execute_python_step(step)
            elif step_type == 'pipeline':
                return self._execute_sub_pipeline_step(step)
            else:
                raise ValueError(f"Nieznany typ kroku: {step_type}")

        except Exception as e:
            error_msg = f"Błąd wykonania kroku: {str(e)}"
            print(error_msg)
            self.pipeline_context['errors'].append(error_msg)
            return False, {"error": error_msg}

    def _execute_component_step(self, step):
        """
        Wykonaj krok typu komponent.

        Args:
            step (dict): Konfiguracja kroku.

        Returns:
            tuple: (success, result) - Czy krok zakończył się sukcesem i jego wynik.
        """
        component_name = step.get('component')
        if not component_name:
            raise ValueError("Brak nazwy komponentu dla kroku.")

        # Pobierz komponent z rejestru
        component = self.registry.get_component(component_name)
        if not component:
            raise ValueError(f"Nieznany komponent: {component_name}")

        # Pobierz parametry i zastosuj zmienne z kontekstu
        params = step.get('params', {})
        resolved_params = self._resolve_variables(params)

        # Wykonaj komponent
        return component.execute(resolved_params, self.pipeline_context)

    def _execute_shell_step(self, step):
        """
        Wykonaj krok typu shell (komenda powłoki).

        Args:
            step (dict): Konfiguracja kroku.

        Returns:
            tuple: (success, result) - Czy krok zakończył się sukcesem i jego wynik.
        """
        command = step.get('command')
        if not command:
            raise ValueError("Brak komendy dla kroku shell.")

        # Zastosuj zmienne z kontekstu
        command = self._resolve_variables_in_string(command)

        # Wykonaj komendę
        try:
            working_dir = step.get('working_dir', os.getcwd())
            working_dir = self._resolve_variables_in_string(working_dir)

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir
            )

            stdout, stderr = process.communicate()

            result = {
                "exit_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace')
            }

            success = process.returncode == 0 or step.get('ignore_errors', False)

            if not success:
                self.pipeline_context['errors'].append(
                    f"Błąd komendy shell: {stderr.decode('utf-8', errors='replace')}")

            return success, result

        except Exception as e:
            error_msg = f"Błąd wykonania komendy shell: {str(e)}"
            self.pipeline_context['errors'].append(error_msg)
            return False, {"error": error_msg}

    def _execute_python_step(self, step):
        """
        Wykonaj krok typu python (kod Python).

        Args:
            step (dict): Konfiguracja kroku.

        Returns:
            tuple: (success, result) - Czy krok zakończył się sukcesem i jego wynik.
        """
        code = step.get('code')
        if not code:
            raise ValueError("Brak kodu dla kroku python.")

        # Zastosuj zmienne z kontekstu
        code = self._resolve_variables_in_string(code)

        # Wykonaj kod Python
        try:
            local_vars = {
                'context': self.pipeline_context,
                'result': None
            }

            # Import potrzebnych modułów
            imports = step.get('imports', [])
            for module_name in imports:
                local_vars[module_name.split('.')[-1]] = importlib.import_module(module_name)

            # Wykonaj kod
            exec(code, globals(), local_vars)

            # Pobierz wynik
            result = local_vars.get('result')

            return True, result

        except Exception as e:
            error_msg = f"Błąd wykonania kodu Python: {str(e)}"
            self.pipeline_context['errors'].append(error_msg)
            return False, {"error": error_msg}

    def _execute_sub_pipeline_step(self, step):
        """
        Wykonaj krok typu pipeline (pod-pipeline).

        Args:
            step (dict): Konfiguracja kroku.

        Returns:
            tuple: (success, result) - Czy krok zakończył się sukcesem i jego wynik.
        """
        pipeline_path = step.get('path')
        if not pipeline_path:
            raise ValueError("Brak ścieżki do pipeline'a dla kroku.")

        # Zastosuj zmienne z kontekstu
        pipeline_path = self._resolve_variables_in_string(pipeline_path)

        # Utwórz nowy silnik do wykonania pod-pipeline'a
        sub_engine = PipelineEngine(self.registry)

        # Przekaż zmienne z aktualnego kontekstu
        variables = {**self.pipeline_context['variables'], **step.get('variables', {})}

        # Wczytaj i uruchom pod-pipeline
        if sub_engine.load_pipeline_from_file(pipeline_path):
            sub_engine.pipeline_context['variables'] = variables
            success = sub_engine.start()

            # Pobierz wyniki
            result = {
                "results": sub_engine.pipeline_context['results'],
                "errors": sub_engine.pipeline_context['errors']
            }

            # Jeśli skonfigurowano, zapisz zmienne z pod-pipeline'a w aktualnym kontekście
            if step.get('export_variables', False):
                for var_name, var_value in sub_engine.pipeline_context['variables'].items():
                    if var_name not in self.pipeline_context['variables']:
                        self.pipeline_context['variables'][var_name] = var_value

            return success, result
        else:
            error_msg = f"Nie udało się wczytać pod-pipeline'a: {pipeline_path}"
            self.pipeline_context['errors'].append(error_msg)
            return False, {"error": error_msg}

    def _evaluate_condition(self, condition):
        """
        Oceń warunek dla kroku.

        Args:
            condition (str): Warunek do oceny.

        Returns:
            bool: Czy warunek jest spełniony.
        """
        if condition is None:
            return True

        # Zastosuj zmienne z kontekstu
        condition = self._resolve_variables_in_string(condition)

        try:
            # Utwórz kontekst dla oceny warunku
            eval_context = {
                'context': self.pipeline_context,
                'variables': self.pipeline_context['variables'],
                'results': self.pipeline_context['results'],
                'errors': self.pipeline_context['errors']
            }

            # Ocenić warunek
            return bool(eval(condition, {}, eval_context))

        except Exception as e:
            print(f"Błąd oceny warunku: {str(e)}")
            return False

    def _resolve_variables(self, data):
        """
        Zastosuj zmienne z kontekstu w strukturze danych.

        Args:
            data (Any): Dane, w których należy zastosować zmienne.

        Returns:
            Any: Dane z zastosowanymi zmiennymi.
        """
        if isinstance(data, str):
            return self._resolve_variables_in_string(data)
        elif isinstance(data, dict):
            return {k: self._resolve_variables(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_variables(item) for item in data]
        else:
            return data

    def _resolve_variables_in_string(self, text):
        """
        Zastosuj zmienne z kontekstu w tekście.

        Args:
            text (str): Tekst, w którym należy zastosować zmienne.

        Returns:
            str: Tekst z zastosowanymi zmiennymi.
        """
        if not isinstance(text, str):
            return text

        # Zastosowanie zmiennych w formacie ${variable}
        import re

        def replace_var(match):
            var_name = match.group(1)
            var_parts = var_name.split('.')

            # Obsługa zmiennych z zagnieżdżoną strukturą (np. ${results.step1.value})
            current = self.pipeline_context
            try:
                for part in var_parts:
                    if part == 'variables':
                        current = self.pipeline_context['variables']
                    elif part == 'results':
                        current = self.pipeline_context['results']
                    elif part == 'errors':
                        current = self.pipeline_context['errors']
                    elif part == 'state':
                        current = self.pipeline_context['state']
                    elif isinstance(current, dict):
                        current = current.get(part, "")
                    else:
                        return ""

                return str(current)
            except:
                return ""

        return re.sub(r'\${([\w\d\._]+)}', replace_var, text)