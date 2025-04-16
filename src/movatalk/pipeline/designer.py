# kidsvoiceai/pipeline/designer.py
"""
Generator i wizualizator pipelinów do łatwego tworzenia aplikacji KidsVoiceAI.
"""

import os
import yaml
import json
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Union


class PipelineTemplate:
    """
    Klasa reprezentująca szablon pipelinu.
    """

    def __init__(self, name: str, description: str, template: Dict[str, Any]):
        """
        Inicjalizacja szablonu pipelinu.

        Args:
            name (str): Nazwa szablonu.
            description (str): Opis szablonu.
            template (dict): Szablon pipelinu w formacie YAML/JSON.
        """
        self.name = name
        self.description = description
        self.template = template

    def generate(self, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Wygeneruj pipeline na podstawie szablonu z podanymi zmiennymi.

        Args:
            variables (dict, optional): Zmienne do zmodyfikowania szablonu.

        Returns:
            dict: Wygenerowany pipeline.
        """
        if variables is None:
            variables = {}

        # Stwórz kopię szablonu, aby nie modyfikować oryginału
        import copy
        pipeline = copy.deepcopy(self.template)

        # Zaktualizuj zmienne
        if 'variables' not in pipeline:
            pipeline['variables'] = {}

        # Dodaj zmienne z parametrów
        for key, value in variables.items():
            pipeline['variables'][key] = value

        return pipeline


class PipelineDesigner:
    """
    Klasa do projektowania i generowania pipelinów KidsVoiceAI.
    """

    def __init__(self):
        """
        Inicjalizacja projektanta pipelinów.
        """
        self.templates = {}
        self.components = {}
        self.load_builtin_templates()
        self.load_components()

    def load_builtin_templates(self):
        """
        Załaduj wbudowane szablony pipelinów.
        """
        # Szablon: Prosty asystent
        simple_assistant = {
            "name": "Prosty asystent",
            "description": "Podstawowy asystent głosowy z kontrolą rodzicielską",
            "version": "1.0.0",
            "variables": {
                "greeting": "Witaj! Jestem twoim asystentem. Jak mogę Ci dzisiaj pomóc?",
                "goodbye": "Do widzenia! Miło było z Tobą rozmawiać."
            },
            "steps": [
                {
                    "name": "initialize_logger",
                    "type": "component",
                    "component": "logger",
                    "params": {
                        "level": "info",
                        "message": "Inicjalizacja asystenta głosowego"
                    }
                },
                {
                    "name": "speak_greeting",
                    "type": "component",
                    "component": "text_to_speech",
                    "params": {
                        "text": "${variables.greeting}"
                    }
                },
                {
                    "name": "main_loop",
                    "type": "component",
                    "component": "loop",
                    "params": {
                        "type": "count",
                        "iterations": 5,
                        "steps": [
                            {
                                "name": "listen",
                                "type": "component",
                                "component": "audio_record",
                                "params": {
                                    "duration": 5,
                                    "output_var": "audio_file"
                                }
                            },
                            {
                                "name": "transcribe",
                                "type": "component",
                                "component": "speech_to_text",
                                "params": {
                                    "audio_path": "${results.audio_file}",
                                    "output_var": "transcript"
                                }
                            },
                            {
                                "name": "query_llm",
                                "type": "component",
                                "component": "local_llm",
                                "params": {
                                    "text": "${results.transcript}",
                                    "output_var": "response"
                                }
                            },
                            {
                                "name": "speak_response",
                                "type": "component",
                                "component": "text_to_speech",
                                "params": {
                                    "text": "${results.response}"
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "speak_goodbye",
                    "type": "component",
                    "component": "text_to_speech",
                    "params": {
                        "text": "${variables.goodbye}"
                    }
                }
            ]
        }

        # Szablon: Quiz
        quiz = {
            "name": "Quiz edukacyjny",
            "description": "Quiz z pytaniami na różne tematy",
            "version": "1.0.0",
            "variables": {
                "category": "matematyka",
                "welcome_message": "Witaj w quizie! Zadam Ci 5 pytań z kategorii ${variables.category}.",
                "questions": []
            },
            "steps": [
                {
                    "name": "welcome",
                    "type": "component",
                    "component": "text_to_speech",
                    "params": {
                        "text": "${variables.welcome_message}"
                    }
                },
                {
                    "name": "initialize_score",
                    "type": "component",
                    "component": "variable_set",
                    "params": {
                        "name": "score",
                        "value": 0,
                        "scope": "state"
                    }
                },
                {
                    "name": "quiz_loop",
                    "type": "component",
                    "component": "loop",
                    "params": {
                        "type": "count",
                        "iterations": 5,
                        "steps": [
                            {
                                "name": "ask_question",
                                "type": "component",
                                "component": "text_to_speech",
                                "params": {
                                    "text": "${variables.questions[variables.loop_index].pytanie}"
                                }
                            },
                            {
                                "name": "listen_answer",
                                "type": "component",
                                "component": "audio_record",
                                "params": {
                                    "duration": 5,
                                    "output_var": "answer_audio"
                                }
                            },
                            {
                                "name": "process_answer",
                                "type": "component",
                                "component": "speech_to_text",
                                "params": {
                                    "audio_path": "${results.answer_audio}",
                                    "output_var": "answer"
                                }
                            }
                            # Inne kroki oceny odpowiedzi...
                        ]
                    }
                }
            ]
        }

        # Dodaj szablony do słownika
        self.templates["simple_assistant"] = PipelineTemplate(
            "Prosty asystent",
            "Podstawowy asystent głosowy",
            simple_assistant
        )

        self.templates["quiz"] = PipelineTemplate(
            "Quiz edukacyjny",
            "Quiz z pytaniami na różne tematy",
            quiz
        )

    def load_components(self):
        """
        Załaduj dostępne komponenty pipeline'ów.
        """
        from kidsvoiceai.pipeline.components import ComponentRegistry
        registry = ComponentRegistry()

        for name, component in registry.get_all_components().items():
            self.components[name] = {
                "name": component.name,
                "description": component.description
            }

    def list_templates(self) -> List[Dict[str, str]]:
        """
        Zwróć listę dostępnych szablonów.

        Returns:
            list: Lista słowników z nazwami i opisami szablonów.
        """
        return [
            {"id": template_id, "name": template.name, "description": template.description}
            for template_id, template in self.templates.items()
        ]

    def list_components(self) -> List[Dict[str, str]]:
        """
        Zwróć listę dostępnych komponentów.

        Returns:
            list: Lista słowników z nazwami i opisami komponentów.
        """
        return [
            {"id": comp_id, "name": comp["name"], "description": comp["description"]}
            for comp_id, comp in self.components.items()
        ]

    def generate_from_template(self, template_id: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Wygeneruj pipeline na podstawie szablonu.

        Args:
            template_id (str): Identyfikator szablonu.
            variables (dict, optional): Zmienne do zmodyfikowania szablonu.

        Returns:
            dict: Wygenerowany pipeline.

        Raises:
            ValueError: Jeśli szablon o podanym ID nie istnieje.
        """
        if template_id not in self.templates:
            raise ValueError(f"Szablon '{template_id}' nie istnieje.")

        return self.templates[template_id].generate(variables)

    def save_pipeline(self, pipeline: Dict[str, Any], file_path: str) -> bool:
        """
        Zapisz pipeline do pliku YAML.

        Args:
            pipeline (dict): Pipeline do zapisania.
            file_path (str): Ścieżka do pliku wyjściowego.

        Returns:
            bool: True jeśli zapisano pomyślnie, False w przeciwnym razie.
        """
        try:
            file_path = os.path.expanduser(file_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(pipeline, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            return True
        except Exception as e:
            print(f"Błąd zapisywania pipeline'u: {str(e)}")
            return False

    def load_pipeline(self, file_path: str) -> Dict[str, Any]:
        """
        Wczytaj pipeline z pliku YAML.

        Args:
            file_path (str): Ścieżka do pliku YAML.

        Returns:
            dict: Wczytany pipeline.

        Raises:
            FileNotFoundError: Jeśli plik nie istnieje.
            ValueError: Jeśli plik nie jest poprawnym plikiem YAML.
        """
        file_path = os.path.expanduser(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Nie znaleziono pliku: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                pipeline = yaml.safe_load(f)

            return pipeline
        except Exception as e:
            raise ValueError(f"Błąd wczytywania pipeline'u: {str(e)}")

    def visualize_pipeline(self, pipeline: Dict[str, Any], output_format: str = "svg",
                           output_file: Optional[str] = None) -> Optional[str]:
        """
        Wygeneruj wizualizację pipeline'u.

        Args:
            pipeline (dict): Pipeline do wizualizacji.
            output_format (str): Format wyjściowy (svg, png, pdf).
            output_file (str, optional): Ścieżka do pliku wyjściowego.

        Returns:
            str or None: Ścieżka do pliku z wizualizacją lub None w przypadku błędu.
        """
        try:
            # Sprawdź czy graphviz jest zainstalowany
            try:
                import graphviz
            except ImportError:
                print("Pakiet 'graphviz' nie jest zainstalowany. Zainstaluj go za pomocą: pip install graphviz")
                return None

            # Utwórz graf
            graph = graphviz.Digraph(
                name=pipeline.get("name", "Pipeline"),
                comment=pipeline.get("description", ""),
                format=output_format
            )

            # Dodaj styl
            graph.attr("graph", rankdir="TB", splines="polyline", ranksep="0.5", nodesep="0.5", margin="0.5")
            graph.attr("node", shape="box", style="rounded,filled", fillcolor="lightblue", fontname="Arial",
                       margin="0.2")
            graph.attr("edge", fontname="Arial", fontsize="10")

            # Dodaj węzeł zmiennych
            if "variables" in pipeline and pipeline["variables"]:
                variables_node = "variables"
                graph.node(variables_node, "Variables", shape="record", fillcolor="lightgreen")

                # Dodaj podgraf dla zmiennych
                with graph.subgraph(name="cluster_variables") as var_subgraph:
                    var_subgraph.attr(label="Variables", style="filled", fillcolor="aliceblue")

                    for var_name, var_value in pipeline["variables"].items():
                        if isinstance(var_value, (dict, list)):
                            var_value = "[complex]"
                        var_node = f"var_{var_name}"
                        var_subgraph.node(var_node, f"{var_name}: {var_value}")
                        graph.edge(variables_node, var_node, style="dashed")

            # Dodaj kroki
            previous_node = None

            for i, step in enumerate(pipeline.get("steps", [])):
                step_id = f"step_{i}"
                step_label = step.get("name", f"Step {i}")

                # Kolor węzła w zależności od typu
                fillcolor = "lightblue"
                if step.get("type") == "component":
                    fillcolor = "lightsalmon"
                elif step.get("type") == "python":
                    fillcolor = "lightgreen"
                elif step.get("type") == "shell":
                    fillcolor = "lightgray"

                # Dodaj węzeł kroku
                graph.node(step_id, step_label, fillcolor=fillcolor)

                # Połącz z poprzednim krokiem
                if previous_node:
                    graph.edge(previous_node, step_id)

                previous_node = step_id

                # Dodaj parametry kroku
                if "params" in step:
                    params_node = f"{step_id}_params"

                    # Przygotuj etykietę z parametrami
                    params_text = "Params:\n"
                    for param_name, param_value in step["params"].items():
                        if isinstance(param_value, (dict, list)):
                            param_value = "[complex]"
                        params_text += f"{param_name}: {param_value}\n"

                    graph.node(params_node, params_text, shape="note", fillcolor="lightyellow")
                    graph.edge(step_id, params_node, style="dashed")

                # Jeśli krok jest pętlą, pokaż jego podetapy
                if step.get("type") == "component" and step.get("component") == "loop" and "steps" in step.get("params",
                                                                                                               {}):
                    loop_steps = step["params"]["steps"]

                    # Dodaj podgraf dla kroków pętli
                    with graph.subgraph(name=f"cluster_{step_id}") as loop_subgraph:
                        loop_subgraph.attr(label=f"Loop: {step.get('params', {}).get('type', 'unknown')}",
                                           style="filled", fillcolor="aliceblue")

                        previous_loop_node = None

                        for j, loop_step in enumerate(loop_steps):
                            loop_step_id = f"{step_id}_loop_{j}"
                            loop_step_label = loop_step.get("name", f"Loop Step {j}")

                            # Kolor węzła w zależności od typu
                            loop_fillcolor = "lightblue"
                            if loop_step.get("type") == "component":
                                loop_fillcolor = "lightsalmon"
                            elif loop_step.get("type") == "python":
                                loop_fillcolor = "lightgreen"
                            elif loop_step.get("type") == "shell":
                                loop_fillcolor = "lightgray"

                            # Dodaj węzeł kroku pętli
                            loop_subgraph.node(loop_step_id, loop_step_label, fillcolor=loop_fillcolor)

                            # Połącz z poprzednim krokiem
                            if previous_loop_node:
                                loop_subgraph.edge(previous_loop_node, loop_step_id)

                            previous_loop_node = loop_step_id

                        # Połącz pierwszy krok pętli z węzłem pętli
                        if loop_steps:
                            first_loop_step_id = f"{step_id}_loop_0"
                            graph.edge(step_id, first_loop_step_id, label="iteration")

            # Renderuj graf
            if output_file:
                output_file = os.path.expanduser(output_file)
                return graph.render(output_file, cleanup=True)
            else:
                # Użyj pliku tymczasowego
                with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp:
                    tmp_path = tmp.name

                return graph.render(tmp_path, cleanup=True)

        except Exception as e:
            print(f"Błąd wizualizacji pipeline'u: {str(e)}")
            return None

    def create_pipeline_wizard(self, output_file: str) -> bool:
        """
        Uruchom interaktywnego kreatora pipeline'u.

        Args:
            output_file (str): Ścieżka do pliku wyjściowego.

        Returns:
            bool: True jeśli pipeline został utworzony pomyślnie, False w przeciwnym razie.
        """
        try:
            pipeline = {
                "name": "",
                "description": "",
                "version": "1.0.0",
                "variables": {},
                "steps": []
            }

            print("=== Kreator Pipeline'u KidsVoiceAI ===")

            # Informacje podstawowe
            pipeline["name"] = input("Nazwa pipeline'u: ")
            pipeline["description"] = input("Opis pipeline'u: ")

            # Zmienne
            print("\n=== Zmienne ===")
            print("Dodaj zmienne pipeline'u (puste pole kończy dodawanie):")

            while True:
                var_name = input("Nazwa zmiennej: ")
                if not var_name:
                    break

                var_value = input(f"Wartość dla '{var_name}': ")
                pipeline["variables"][var_name] = var_value

            # Kroki
            print("\n=== Kroki ===")
            print("Dodaj kroki pipeline'u (puste pole kończy dodawanie):")

            step_counter = 1
            while True:
                print(f"\nKrok {step_counter}:")
                step_name = input("Nazwa kroku (puste pole kończy dodawanie): ")
                if not step_name:
                    break

                # Typ kroku
                print("Dostępne typy:")
                print("1. component - Komponent pipeline'u")
                print("2. python - Kod Python")
                print("3. shell - Komenda powłoki")

                step_type_choice = input("Wybierz typ (1-3): ")
                step_type = "component"  # Domyślnie

                if step_type_choice == "2":
                    step_type = "python"
                elif step_type_choice == "3":
                    step_type = "shell"

                # Przygotuj krok
                step = {
                    "name": step_name,
                    "type": step_type
                }

                # Dodaj specyficzne pola w zależności od typu
                if step_type == "component":
                    # Pokaż dostępne komponenty
                    print("\nDostępne komponenty:")
                    components = self.list_components()
                    for i, comp in enumerate(components, 1):
                        print(f"{i}. {comp['name']} - {comp['description']}")

                    comp_choice = input("Wybierz komponent (numer): ")
                    try:
                        comp_index = int(comp_choice) - 1
                        if 0 <= comp_index < len(components):
                            step["component"] = components[comp_index]["id"]
                        else:
                            print("Nieprawidłowy wybór. Używam 'logger'.")
                            step["component"] = "logger"
                    except:
                        print("Nieprawidłowy wybór. Używam 'logger'.")
                        step["component"] = "logger"

                    # Parametry komponentu
                    step["params"] = {}
                    print("\nDodaj parametry komponentu (puste pole kończy dodawanie):")

                    while True:
                        param_name = input("Nazwa parametru: ")
                        if not param_name:
                            break

                        param_value = input(f"Wartość dla '{param_name}': ")
                        step["params"][param_name] = param_value

                elif step_type == "python":
                    print("\nWprowadź kod Python (zakończ wpisując 'END' w nowej linii):")
                    code_lines = []

                    while True:
                        line = input()
                        if line == "END":
                            break
                        code_lines.append(line)

                    step["code"] = "\n".join(code_lines)

                elif step_type == "shell":
                    step["command"] = input("Wprowadź komendę powłoki: ")
                    step["ignore_errors"] = input("Ignorować błędy? (t/n): ").lower() == "t"

                # Dodaj krok do pipeline'u
                pipeline["steps"].append(step)
                step_counter += 1

            # Zapisz pipeline
            if self.save_pipeline(pipeline, output_file):
                print(f"\nPipeline został zapisany do pliku: {output_file}")

                # Zapytaj o wizualizację
                if input("Czy chcesz wygenerować wizualizację pipeline'u? (t/n): ").lower() == "t":
                    viz_format = input("Format wizualizacji (svg/png/pdf) [domyślnie: svg]: ") or "svg"
                    viz_output = output_file.rsplit(".", 1)[0] + f".{viz_format}"
                    viz_path = self.visualize_pipeline(pipeline, viz_format, viz_output)

                    if viz_path:
                        print(f"Wizualizacja zapisana do: {viz_path}")
                    else:
                        print("Nie udało się wygenerować wizualizacji.")

                return True
            else:
                print("Nie udało się zapisać pipeline'u.")
                return False

        except KeyboardInterrupt:
            print("\nPrzerwano tworzenie pipeline'u.")
            return False
        except Exception as e:
            print(f"Błąd kreatora: {str(e)}")
            return False


# Funkcja do uruchomienia projektanta z linii poleceń
def main():
    """
    Funkcja główna projektanta pipelinów KidsVoiceAI.
    """
    import argparse

    parser = argparse.ArgumentParser(description="KidsVoiceAI Pipeline Designer")
    subparsers = parser.add_subparsers(dest="command", help="Komenda do wykonania")

    # Komenda: list-templates
    list_templates_parser = subparsers.add_parser("list-templates", help="Wyświetl dostępne szablony")

    # Komenda: list-components
    list_components_parser = subparsers.add_parser("list-components", help="Wyświetl dostępne komponenty")

    # Komenda: generate
    generate_parser = subparsers.add_parser("generate", help="Wygeneruj pipeline z szablonu")
    generate_parser.add_argument("template", help="ID szablonu")
    generate_parser.add_argument("output", help="Ścieżka do pliku wyjściowego")
    generate_parser.add_argument("--var", "-v", action="append", nargs=2, metavar=("NAME", "VALUE"),
                                 help="Zmienna do ustawienia (można użyć wielokrotnie)")

    # Komenda: visualize
    visualize_parser = subparsers.add_parser("visualize", help="Wizualizuj pipeline")
    visualize_parser.add_argument("input", help="Ścieżka do pliku YAML z pipeline'm")
    visualize_parser.add_argument("--output", "-o", help="Ścieżka do pliku wyjściowego (bez rozszerzenia)")
    visualize_parser.add_argument("--format", "-f", choices=["svg", "png", "pdf"], default="svg",
                                  help="Format wyjściowy (domyślnie: svg)")

    # Komenda: wizard
    wizard_parser = subparsers.add_parser("wizard", help="Uruchom interaktywnego kreatora pipeline'u")
    wizard_parser.add_argument("output", help="Ścieżka do pliku wyjściowego")

    # Komenda: run
    run_parser = subparsers.add_parser("run", help="Uruchom pipeline")
    run_parser.add_argument("input", help="Ścieżka do pliku YAML z pipeline'm")
    run_parser.add_argument("--var", "-v", action="append", nargs=2, metavar=("NAME", "VALUE"),
                            help="Zmienna do ustawienia (można użyć wielokrotnie)")

    args = parser.parse_args()

    # Inicjalizacja projektanta
    designer = PipelineDesigner()

    # Obsługa komend
    if args.command == "list-templates":
        templates = designer.list_templates()
        print("Dostępne szablony:")
        for template in templates:
            print(f"  {template['id']}: {template['name']} - {template['description']}")

    elif args.command == "list-components":
        components = designer.list_components()
        print("Dostępne komponenty:")
        for component in components:
            print(f"  {component['id']}: {component['name']} - {component['description']}")

    elif args.command == "generate":
        variables = {}
        if args.var:
            for name, value in args.var:
                variables[name] = value

        try:
            pipeline = designer.generate_from_template(args.template, variables)
            if designer.save_pipeline(pipeline, args.output):
                print(f"Pipeline wygenerowany i zapisany do: {args.output}")
            else:
                print("Nie udało się zapisać pipeline'u.")
        except Exception as e:
            print(f"Błąd generowania pipeline'u: {str(e)}")

    elif args.command == "visualize":
        try:
            pipeline = designer.load_pipeline(args.input)

            output = args.output
            if not output:
                output = os.path.splitext(args.input)[0]

            viz_path = designer.visualize_pipeline(pipeline, args.format, output)

            if viz_path:
                print(f"Wizualizacja zapisana do: {viz_path}")
            else:
                print("Nie udało się wygenerować wizualizacji.")

        except Exception as e:
            print(f"Błąd wizualizacji pipeline'u: {str(e)}")

    elif args.command == "wizard":
        designer.create_pipeline_wizard(args.output)

    elif args.command == "run":
        try:
            # Wczytaj pipeline
            pipeline = designer.load_pipeline(args.input)

            # Ustaw dodatkowe zmienne
            if args.var:
                if "variables" not in pipeline:
                    pipeline["variables"] = {}

                for name, value in args.var:
                    pipeline["variables"][name] = value

            # Uruchom pipeline
            from kidsvoiceai.pipeline.engine import PipelineEngine
            engine = PipelineEngine()

            if engine.load_pipeline(pipeline):
                print(f"Uruchamianie pipeline'u: {pipeline.get('name', args.input)}")
                success = engine.start()

                if success:
                    print("Pipeline zakończony pomyślnie.")
                else:
                    print("Pipeline zakończony z błędami.")

                # Pokaż wyniki
                if "results" in engine.pipeline_context:
                    print("\nWyniki:")
                    for key, value in engine.pipeline_context["results"].items():
                        if isinstance(value, (dict, list)):
                            print(f"  {key}: {json.dumps(value, indent=2)}")
                        else:
                            print(f"  {key}: {value}")
            else:
                print("Nie udało się załadować pipeline'u.")

        except Exception as e:
            print(f"Błąd uruchamiania pipeline'u: {str(e)}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()