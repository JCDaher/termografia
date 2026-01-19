"""
Módulo de banco de dados.
Gerencia persistência de dados em SQLite.
"""

from database.db_manager import DatabaseManager, get_db_manager

__all__ = ['DatabaseManager', 'get_db_manager']
