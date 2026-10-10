"""Prompt templates for LLM interactions."""
from src.prompts.templates import (
    CLASSIFIER_PROMPT,
    GENERATOR_PROMPT,
    VERIFIER_PROMPT,
    get_classifier_prompt,
    get_generator_prompt
)

__all__ = [
    'CLASSIFIER_PROMPT',
    'GENERATOR_PROMPT',
    'VERIFIER_PROMPT',
    'get_classifier_prompt',
    'get_generator_prompt'
]
