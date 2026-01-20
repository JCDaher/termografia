"""
Cliente para Anthropic API (Claude AI) para geração de laudos médicos.
Gerencia chamadas à API e geração de relatórios.
"""

from anthropic import Anthropic, APIError
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from config.security import get_security_manager
from api.prompts import get_system_prompt, get_dermatome_prompt, get_btt_prompt
from api.prompts_professional import get_system_prompt_professional, get_professional_dermatome_prompt

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Cliente para integração com Claude AI da Anthropic."""

    # Modelos disponíveis (ordenados por preferência e disponibilidade)
    # Usando modelos com maior chance de estar acessível em qualquer tier de API key
    MODEL_SONNET_3_5 = "claude-3-5-sonnet-20241022"  # Sonnet 3.5 mais recente
    MODEL_SONNET_3_5_OLD = "claude-3-5-sonnet-20240620"  # Versão estável
    MODEL_HAIKU = "claude-3-5-haiku-20241022"  # Mais rápido e econômico
    MODEL_OPUS_3 = "claude-3-opus-20240229"  # Opus 3 (legado, mas ainda disponível)

    # Modelo padrão - Haiku é o mais acessível e econômico
    MODEL_SONNET = MODEL_HAIKU

    def __init__(self, api_key: Optional[str] = None, model: str = MODEL_SONNET):
        """
        Inicializa o cliente Claude.

        Args:
            api_key: API key da Anthropic. Se None, tenta carregar do SecurityManager
            model: Modelo Claude a usar
        """
        self.model = model

        # Carrega API key
        if api_key is None:
            try:
                security_manager = get_security_manager()
                api_key = security_manager.load_api_key()

                if api_key is None:
                    raise ClaudeClientError(
                        "API key não encontrada. Configure usando:\n"
                        "Configurações > Configurar API Key"
                    )
            except Exception as e:
                # Se houver erro ao carregar (ex: erro de descriptografia)
                raise ClaudeClientError(str(e))

        # Inicializa cliente Anthropic
        try:
            self.client = Anthropic(api_key=api_key)
            logger.info(f"Cliente Claude inicializado com modelo: {model}")
        except Exception as e:
            raise ClaudeClientError(f"Erro ao inicializar cliente Anthropic: {e}")

    def generate_report(self, exam_type: str, exam_data: Dict[str, Any],
                       temperature: float = 1.0,
                       max_tokens: int = 8192,
                       use_professional_template: bool = True) -> str:
        """
        Gera laudo médico usando Claude AI.

        Args:
            exam_type: Tipo de exame ('dermatome' ou 'btt')
            exam_data: Dados do exame para gerar o laudo
            temperature: Temperatura do modelo (0-1, padrão 1.0)
            max_tokens: Número máximo de tokens na resposta (aumentado para 8192 para laudos profissionais)
            use_professional_template: Se True, usa template profissional padronizado (padrão: True)

        Returns:
            Laudo médico gerado

        Raises:
            ClaudeClientError: Se houver erro na geração
        """
        try:
            # Usa template profissional para dermátomos por padrão
            if exam_type.lower() == 'dermatome' and use_professional_template:
                system_prompt = get_system_prompt_professional()
                user_prompt = get_professional_dermatome_prompt(exam_data)
                logger.info(f"Gerando laudo {exam_type} com template profissional...")
            else:
                # Fallback para templates antigos (BTT ou modo legado)
                system_prompt = get_system_prompt(exam_type)

                # Obtém user prompt baseado no tipo de exame
                if exam_type.lower() == 'dermatome':
                    user_prompt = get_dermatome_prompt(exam_data)
                elif exam_type.lower() == 'btt':
                    user_prompt = get_btt_prompt(exam_data)
                else:
                    raise ClaudeClientError(f"Tipo de exame não reconhecido: {exam_type}")

                logger.info(f"Gerando laudo {exam_type} com Claude...")

            # Chamada à API com fallback automático para múltiplos modelos
            # Tenta em ordem: mais acessível primeiro (Haiku), depois mais avançados
            models_to_try = [
                self.MODEL_HAIKU,  # Mais acessível e econômico - tenta primeiro
                self.MODEL_SONNET_3_5_OLD,  # Sonnet 3.5 versão estável
                self.MODEL_SONNET_3_5,  # Sonnet 3.5 mais recente
                self.MODEL_OPUS_3,  # Opus 3 (requer tier pago)
            ]

            # Remove duplicatas mantendo ordem
            seen = set()
            models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

            logger.info(f"Modelos a tentar (em ordem): {models_to_try}")

            last_error = None
            for model in models_to_try:
                try:
                    logger.info(f"Tentando gerar laudo com modelo: {model}")
                    response = self.client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system_prompt,
                        messages=[
                            {
                                "role": "user",
                                "content": user_prompt
                            }
                        ]
                    )

                    # Extrai texto da resposta
                    report_text = response.content[0].text

                    logger.info(f"✅ Laudo gerado com sucesso usando {model} ({len(report_text)} caracteres)")

                    # Atualiza o modelo atual se funcionou com fallback
                    if model != self.model:
                        logger.info(f"Modelo atualizado de {self.model} para {model}")
                        self.model = model

                    return report_text

                except APIError as e:
                    last_error = e
                    error_str = str(e)
                    # Se for erro 404 (modelo não encontrado), tenta próximo
                    if "404" in error_str or "not_found" in error_str:
                        logger.warning(f"❌ Modelo {model} não disponível (404), tentando próximo...")
                        continue
                    # Se for erro de permissão, tenta próximo
                    elif "permission" in error_str.lower() or "access" in error_str.lower():
                        logger.warning(f"❌ Sem permissão para modelo {model}, tentando próximo...")
                        continue
                    else:
                        # Outro tipo de erro (ex: rate limit, auth), não tenta fallback
                        logger.error(f"Erro crítico na API Anthropic: {e}")
                        raise ClaudeClientError(f"Erro na API Anthropic: {e}")

            # Se chegou aqui, todos os modelos falharam
            logger.error(f"❌ Todos os modelos falharam!")
            logger.error(f"Modelos tentados: {models_to_try}")
            logger.error(f"Último erro: {last_error}")

            # Mensagem de erro mais detalhada e útil
            error_msg = (
                "❌ Nenhum modelo Claude disponível funcionou.\n\n"
                f"Modelos tentados:\n"
            )
            for m in models_to_try:
                error_msg += f"  • {m}\n"

            error_msg += (
                f"\nÚltimo erro: {last_error}\n\n"
                "🔍 POSSÍVEIS CAUSAS:\n\n"
                "1. API Key sem créditos\n"
                "   → Verifique em: https://console.anthropic.com/settings/billing\n"
                "   → Adicione créditos ou configure faturamento\n\n"
                "2. API Key sem acesso aos modelos\n"
                "   → Algumas contas têm acesso limitado\n"
                "   → Tente criar uma nova API key\n\n"
                "3. API Key inválida\n"
                "   → Verifique se copiou corretamente (deve começar com 'sk-ant-api03-')\n"
                "   → Crie uma nova em: https://console.anthropic.com/settings/keys\n\n"
                "4. Problemas de rede\n"
                "   → Verifique sua conexão com internet\n"
                "   → Tente desabilitar VPN/proxy\n\n"
                "💡 SOLUÇÃO RÁPIDA:\n"
                "   1. Acesse: https://console.anthropic.com/settings/keys\n"
                "   2. Crie uma nova API key\n"
                "   3. Adicione créditos (mínimo $5 USD)\n"
                "   4. Configure na aplicação (aba Configurações)"
            )

            raise ClaudeClientError(error_msg)
        except Exception as e:
            logger.error(f"Erro ao gerar laudo: {e}")
            raise ClaudeClientError(f"Erro ao gerar laudo: {e}")

    def generate_dermatome_report(self, exam_data: Dict[str, Any]) -> str:
        """
        Gera laudo de análise de dermátomos.

        Args:
            exam_data: Dados do exame de dermátomos

        Returns:
            Laudo médico formatado
        """
        return self.generate_report('dermatome', exam_data)

    def generate_btt_report(self, exam_data: Dict[str, Any]) -> str:
        """
        Gera laudo de análise BTT (Brain Thermal Tunnel).

        Args:
            exam_data: Dados do exame BTT

        Returns:
            Laudo médico formatado
        """
        return self.generate_report('btt', exam_data)

    def test_connection(self) -> bool:
        """
        Testa a conexão com a API Anthropic.

        Returns:
            True se conexão bem-sucedida, False caso contrário
        """
        try:
            # Faz uma chamada simples para testar
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": "Responda apenas 'OK' se você estiver funcionando."
                    }
                ]
            )

            logger.info("Teste de conexão com Claude: OK")
            return True

        except Exception as e:
            logger.error(f"Teste de conexão com Claude falhou: {e}")
            return False

    def get_usage_info(self, response) -> Dict[str, int]:
        """
        Extrai informações de uso de tokens da resposta.

        Args:
            response: Resposta da API

        Returns:
            Dicionário com info de uso
        """
        if hasattr(response, 'usage'):
            return {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
        return {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}


class ClaudeClientError(Exception):
    """Exceção para erros do cliente Claude."""
    pass


# Cache do cliente para reutilização
_claude_client = None


def get_claude_client(api_key: Optional[str] = None,
                     model: str = ClaudeClient.MODEL_SONNET) -> ClaudeClient:
    """
    Retorna instância do ClaudeClient (padrão Singleton).

    Args:
        api_key: API key (opcional, carrega do SecurityManager se None)
        model: Modelo Claude a usar

    Returns:
        Instância de ClaudeClient
    """
    global _claude_client

    # Se já existe um cliente e os parâmetros são os mesmos, reutiliza
    if _claude_client is not None and _claude_client.model == model:
        return _claude_client

    # Cria novo cliente
    _claude_client = ClaudeClient(api_key=api_key, model=model)
    return _claude_client


def configure_api_key(api_key: str) -> None:
    """
    Configura e salva a API key da Anthropic de forma segura.

    Args:
        api_key: API key da Anthropic
    """
    try:
        security_manager = get_security_manager()
        security_manager.save_api_key(api_key)
        logger.info("API key configurada com sucesso")
    except Exception as e:
        raise ClaudeClientError(f"Erro ao configurar API key: {e}")


def has_api_key() -> bool:
    """
    Verifica se existe uma API key configurada.

    Returns:
        True se existe API key, False caso contrário
    """
    security_manager = get_security_manager()
    return security_manager.has_api_key()


if __name__ == '__main__':
    # Teste básico
    print("=== Teste do ClaudeClient ===\n")

    # Verifica se tem API key configurada
    if not has_api_key():
        print("⚠️  Nenhuma API key configurada.")
        print("Configure usando:")
        print("  from api.claude_client import configure_api_key")
        print("  configure_api_key('sua-api-key-aqui')")
        print()

        # Para teste, pode-se configurar temporariamente
        test_key = input("Digite sua API key da Anthropic para teste (ou Enter para pular): ").strip()
        if test_key:
            configure_api_key(test_key)
        else:
            print("Teste cancelado - API key necessária")
            exit(0)

    try:
        # Cria cliente
        client = get_claude_client()
        print(f"Cliente criado com modelo: {client.model}\n")

        # Testa conexão
        print("Testando conexão com Claude...")
        if client.test_connection():
            print("✓ Conexão bem-sucedida!\n")
        else:
            print("✗ Falha na conexão\n")
            exit(1)

        # Teste de geração de laudo simples
        print("Gerando laudo de teste...")

        test_exam_data = {
            'patient_name': 'Paciente Teste',
            'exam_date': '2024-01-15 14:30',
            'clinical_indication': 'Teste do sistema',
            'equipment': 'FLIR T540',
            'dermatome_analyses': [
                {
                    'dermatome': 'C5',
                    'left_temp': 34.5,
                    'right_temp': 35.2,
                    'delta_t': 0.7,
                    'classification': 'Leve'
                }
            ]
        }

        report = client.generate_dermatome_report(test_exam_data)

        print("Laudo gerado:")
        print("-" * 80)
        print(report[:500] + "...")  # Mostra primeiros 500 caracteres
        print("-" * 80)
        print(f"\nTotal: {len(report)} caracteres")

        print("\n✓ Teste concluído com sucesso!")

    except ClaudeClientError as e:
        print(f"✗ Erro: {e}")
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
