# Eksportuje PipelineEngine, YamlParser, ComponentRegistry
# movatalk/pipeline/__init__.py
"""
Moduł pipeline zawiera implementację systemu przetwarzania pipelinów DSL.
"""

from movatalk.pipeline.engine import PipelineEngine
from movatalk.pipeline.parser import YamlParser
from movatalk.pipeline.components import ComponentRegistry

__all__ = ['PipelineEngine', 'YamlParser', 'ComponentRegistry']