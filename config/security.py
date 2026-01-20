"""
Módulo de segurança para criptografia de credenciais multiplataforma.
Permite armazenamento seguro da API Key da Anthropic no Windows, macOS e Linux.
"""

import base64
import os
import json
import platform
from pathlib import Path
from typing import Optional

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class SecurityManager:
    """Gerencia criptografia e descriptografia de credenciais de forma multiplataforma."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de segurança.

        Args:
            config_dir: Diretório para armazenar arquivo de configuração.
                       Se None, usa diretório padrão do sistema operacional
        """
        if config_dir is None:
            self.config_dir = self._get_default_config_dir()
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'credentials.dat'
        self.key_file = self.config_dir / '.key'

        if not CRYPTOGRAPHY_AVAILABLE:
            raise SecurityError(
                "A biblioteca 'cryptography' não está instalada. "
                "Execute: pip install cryptography"
            )

        # Inicializa ou carrega a chave de criptografia
        self._cipher = self._get_or_create_cipher()

    def _get_default_config_dir(self) -> Path:
        """
        Retorna o diretório padrão de configuração baseado no sistema operacional.

        Returns:
            Path para diretório de configuração
        """
        system = platform.system()

        if system == 'Windows':
            # Windows: %APPDATA%/TermografiaApp
            appdata = os.getenv('APPDATA')
            if appdata:
                return Path(appdata) / 'TermografiaApp'
            return Path.home() / 'AppData' / 'Roaming' / 'TermografiaApp'

        elif system == 'Darwin':  # macOS
            # macOS: ~/Library/Application Support/TermografiaApp
            return Path.home() / 'Library' / 'Application Support' / 'TermografiaApp'

        else:  # Linux e outros Unix
            # Linux: ~/.config/termografia
            xdg_config = os.getenv('XDG_CONFIG_HOME')
            if xdg_config:
                return Path(xdg_config) / 'termografia'
            return Path.home() / '.config' / 'termografia'

    def _get_machine_id(self) -> bytes:
        """
        Gera um identificador único da máquina para usar como salt.

        Returns:
            Bytes com identificador da máquina
        """
        system = platform.system()

        # Usa informações da máquina como base para o salt
        machine_info = f"{platform.node()}-{system}-{os.getlogin() if hasattr(os, 'getlogin') else 'user'}"

        return machine_info.encode('utf-8')

    def _derive_key(self) -> bytes:
        """
        Deriva uma chave de criptografia baseada em informações da máquina.

        Returns:
            Chave de 32 bytes para Fernet
        """
        # Usa salt baseado na máquina
        salt = self._get_machine_id()

        # Password fixa (combinada com salt único por máquina)
        password = b"TermografiaApp-2024-Secure-Key"

        # Deriva chave usando PBKDF2
        from cryptography.hazmat.backends import default_backend
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def _get_or_create_cipher(self) -> Fernet:
        """
        Obtém ou cria a cifra Fernet.

        Returns:
            Instância de Fernet para criptografia
        """
        # Deriva chave baseada na máquina
        key = self._derive_key()

        # Salva hash da chave para validação futura
        from cryptography.hazmat.backends import default_backend
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(key)
        key_hash = base64.b64encode(digest.finalize()).decode()

        if self.key_file.exists():
            # Valida se a chave é a mesma
            with open(self.key_file, 'r') as f:
                stored_hash = f.read().strip()

            if stored_hash != key_hash:
                raise SecurityError(
                    "Chave de criptografia não corresponde. "
                    "Os dados podem ter sido criados em outra máquina."
                )
        else:
            # Salva hash da chave
            with open(self.key_file, 'w') as f:
                f.write(key_hash)

        return Fernet(key)

    def encrypt_data(self, data: str) -> str:
        """
        Criptografa dados.

        Args:
            data: String a ser criptografada

        Returns:
            String em base64 com dados criptografados
        """
        try:
            data_bytes = data.encode('utf-8')
            encrypted_bytes = self._cipher.encrypt(data_bytes)
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            raise SecurityError(f"Erro ao criptografar dados: {e}")

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Descriptografa dados.

        Args:
            encrypted_data: String em base64 com dados criptografados

        Returns:
            String descriptografada
        """
        try:
            encrypted_bytes = encrypted_data.encode('utf-8')
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
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
                'anthropic_api_key': encrypted_key,
                'platform': platform.system()
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
        except SecurityError:
            # Erro de descriptografia - provavelmente mudou de máquina/usuário
            raise SecurityError(
                "Não foi possível descriptografar a API key. "
                "Isso geralmente acontece quando:\n"
                "• A API key foi configurada em outra máquina\n"
                "• O nome de usuário ou hostname mudou\n\n"
                "Solução: Reconfigure a API key usando:\n"
                "Configurações > Configurar API Key"
            )
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
    print(f"Sistema operacional: {platform.system()}")

    sm = SecurityManager()
    print(f"Diretório de config: {sm.config_dir}")

    # Teste de criptografia/descriptografia
    test_data = "sk-ant-api03-test-key-123456"
    print(f"\nDados originais: {test_data}")

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
