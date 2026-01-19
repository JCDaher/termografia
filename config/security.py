"""
Módulo de segurança para criptografia de credenciais usando DPAPI do Windows.
Permite armazenamento seguro da API Key da Anthropic.
"""

import win32crypt
import base64
import os
import json
from pathlib import Path
from typing import Optional


class SecurityManager:
    """Gerencia criptografia e descriptografia de credenciais usando DPAPI do Windows."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de segurança.

        Args:
            config_dir: Diretório para armazenar arquivo de configuração.
                       Se None, usa %APPDATA%/TermografiaApp
        """
        if config_dir is None:
            appdata = os.getenv('APPDATA')
            self.config_dir = Path(appdata) / 'TermografiaApp'
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'credentials.dat'

    def encrypt_data(self, data: str) -> str:
        """
        Criptografa dados usando DPAPI do Windows.

        Args:
            data: String a ser criptografada

        Returns:
            String em base64 com dados criptografados
        """
        try:
            data_bytes = data.encode('utf-8')
            encrypted_bytes = win32crypt.CryptProtectData(
                data_bytes,
                'TermografiaApp',  # Descrição
                None,  # Entropy opcional
                None,  # Reservado
                None,  # Prompt struct
                0      # Flags
            )
            # Retorna em base64 para facilitar armazenamento
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            raise SecurityError(f"Erro ao criptografar dados: {e}")

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Descriptografa dados usando DPAPI do Windows.

        Args:
            encrypted_data: String em base64 com dados criptografados

        Returns:
            String descriptografada
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = win32crypt.CryptUnprotectData(
                encrypted_bytes,
                None,  # Entropy opcional
                None,  # Reservado
                None,  # Prompt struct
                0      # Flags
            )
            # CryptUnprotectData retorna (description, data)
            return decrypted_bytes[1].decode('utf-8')
        except Exception as e:
            raise SecurityError(f"Erro ao descriptografar dados: {e}")

    def save_api_key(self, api_key: str) -> None:
        """
        Salva a API key da Anthropic de forma criptografada.

        Args:
            api_key: API key da Anthropic
        """
        try:
            encrypted_key = self.encrypt_data(api_key)
            config = {
                'anthropic_api_key': encrypted_key
            }

            with open(self.config_file, 'w') as f:
                json.dump(config, f)

        except Exception as e:
            raise SecurityError(f"Erro ao salvar API key: {e}")

    def load_api_key(self) -> Optional[str]:
        """
        Carrega e descriptografa a API key da Anthropic.

        Returns:
            API key descriptografada ou None se não encontrada
        """
        try:
            if not self.config_file.exists():
                return None

            with open(self.config_file, 'r') as f:
                config = json.load(f)

            encrypted_key = config.get('anthropic_api_key')
            if not encrypted_key:
                return None

            return self.decrypt_data(encrypted_key)

        except FileNotFoundError:
            return None
        except Exception as e:
            raise SecurityError(f"Erro ao carregar API key: {e}")

    def delete_api_key(self) -> None:
        """Remove o arquivo de credenciais."""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
        except Exception as e:
            raise SecurityError(f"Erro ao deletar API key: {e}")

    def has_api_key(self) -> bool:
        """
        Verifica se existe uma API key salva.

        Returns:
            True se existe API key salva, False caso contrário
        """
        return self.config_file.exists()


class SecurityError(Exception):
    """Exceção para erros relacionados à segurança."""
    pass


# Instância global do gerenciador de segurança
_security_manager = None


def get_security_manager() -> SecurityManager:
    """
    Retorna a instância global do SecurityManager (padrão Singleton).

    Returns:
        Instância de SecurityManager
    """
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


if __name__ == '__main__':
    # Exemplo de uso
    print("=== Teste do SecurityManager ===\n")

    sm = SecurityManager()

    # Teste de criptografia/descriptografia
    test_data = "sk-ant-api03-test-key-123456"
    print(f"Dados originais: {test_data}")

    encrypted = sm.encrypt_data(test_data)
    print(f"Dados criptografados: {encrypted[:50]}...")

    decrypted = sm.decrypt_data(encrypted)
    print(f"Dados descriptografados: {decrypted}")
    print(f"Match: {test_data == decrypted}\n")

    # Teste de salvar/carregar API key
    print("Salvando API key de teste...")
    sm.save_api_key("sk-ant-api03-test-key-example")

    print("Carregando API key...")
    loaded_key = sm.load_api_key()
    print(f"API key carregada: {loaded_key}")

    print(f"Has API key: {sm.has_api_key()}")

    print("\nDeletando API key...")
    sm.delete_api_key()
    print(f"Has API key após deletar: {sm.has_api_key()}")
