"""
Módulo de configuração.
Gerencia segurança e criptografia de credenciais.
"""

from config.security import SecurityManager, get_security_manager

__all__ = ['SecurityManager', 'get_security_manager']
