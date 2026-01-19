"""
Módulo de API.
Integração com Claude AI da Anthropic.
"""

from api.claude_client import ClaudeClient, get_claude_client, configure_api_key, has_api_key
from api.prompts import get_dermatome_prompt, get_btt_prompt, get_system_prompt

__all__ = [
    'ClaudeClient',
    'get_claude_client',
    'configure_api_key',
    'has_api_key',
    'get_dermatome_prompt',
    'get_btt_prompt',
    'get_system_prompt'
]
