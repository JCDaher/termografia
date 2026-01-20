#!/usr/bin/env python3
"""
Script de teste para diagnosticar problemas com API Key da Anthropic.
Testa conectividade e acesso aos modelos Claude.
"""

import sys
from anthropic import Anthropic, APIError

def test_api_key(api_key: str):
    """
    Testa uma API key da Anthropic e verifica quais modelos estão disponíveis.

    Args:
        api_key: API key da Anthropic para testar
    """
    print("=" * 70)
    print("TESTE DE API KEY - ANTHROPIC CLAUDE")
    print("=" * 70)
    print()

    # Valida formato da API key
    if not api_key.startswith("sk-ant-"):
        print("❌ ERRO: API key deve começar com 'sk-ant-'")
        print(f"   Sua key começa com: {api_key[:10]}...")
        print()
        print("Verifique se copiou corretamente do console Anthropic.")
        return False

    print(f"✓ Formato da API key: OK")
    print(f"  Key: {api_key[:15]}...{api_key[-5:]}")
    print()

    # Inicializa cliente
    try:
        client = Anthropic(api_key=api_key)
        print("✓ Cliente Anthropic inicializado")
        print()
    except Exception as e:
        print(f"❌ Erro ao inicializar cliente: {e}")
        return False

    # Lista de modelos para testar (do mais acessível ao mais avançado)
    models_to_test = [
        ("Claude 3.5 Haiku", "claude-3-5-haiku-20241022"),
        ("Claude 3.5 Sonnet (old)", "claude-3-5-sonnet-20240620"),
        ("Claude 3.5 Sonnet (new)", "claude-3-5-sonnet-20241022"),
        ("Claude 3 Opus", "claude-3-opus-20240229"),
    ]

    print("Testando acesso aos modelos...")
    print("-" * 70)

    available_models = []
    unavailable_models = []

    for model_name, model_id in models_to_test:
        print(f"\nTestando: {model_name}")
        print(f"  ID: {model_id}")

        try:
            # Tenta fazer uma chamada simples
            response = client.messages.create(
                model=model_id,
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": "Responda apenas com a palavra 'OK'."
                    }
                ]
            )

            # Se chegou aqui, o modelo funcionou
            print(f"  ✅ DISPONÍVEL")
            print(f"  Resposta: {response.content[0].text}")
            print(f"  Tokens usados: {response.usage.input_tokens + response.usage.output_tokens}")
            available_models.append((model_name, model_id))

        except APIError as e:
            error_str = str(e)

            if "404" in error_str or "not_found" in error_str:
                print(f"  ❌ NÃO ENCONTRADO (erro 404)")
                print(f"     Este modelo não existe ou foi descontinuado")
                unavailable_models.append((model_name, model_id, "404 - Não encontrado"))

            elif "401" in error_str or "invalid" in error_str.lower():
                print(f"  ❌ API KEY INVÁLIDA (erro 401)")
                print(f"     Sua API key está incorreta ou expirada")
                return False

            elif "403" in error_str or "permission" in error_str.lower():
                print(f"  ❌ SEM PERMISSÃO (erro 403)")
                print(f"     Sua conta não tem acesso a este modelo")
                unavailable_models.append((model_name, model_id, "403 - Sem permissão"))

            elif "429" in error_str or "rate_limit" in error_str.lower():
                print(f"  ⚠️  LIMITE DE TAXA (erro 429)")
                print(f"     Muitas requisições - tente novamente em alguns segundos")

            elif "insufficient_quota" in error_str.lower() or "credit" in error_str.lower():
                print(f"  ❌ SEM CRÉDITOS")
                print(f"     Sua conta não tem créditos suficientes")
                print(f"     Adicione créditos em: https://console.anthropic.com/settings/billing")
                return False

            else:
                print(f"  ❌ ERRO: {e}")
                unavailable_models.append((model_name, model_id, str(e)[:100]))

        except Exception as e:
            print(f"  ❌ ERRO INESPERADO: {e}")
            unavailable_models.append((model_name, model_id, str(e)[:100]))

    # Resumo
    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    print()

    if available_models:
        print(f"✅ MODELOS DISPONÍVEIS ({len(available_models)}):")
        for model_name, model_id in available_models:
            print(f"   • {model_name}")
            print(f"     {model_id}")
        print()
        print("🎉 SUA API KEY ESTÁ FUNCIONANDO!")
        print()
        print("Use a aplicação normalmente. O sistema escolherá automaticamente")
        print("um dos modelos disponíveis.")
        return True
    else:
        print("❌ NENHUM MODELO DISPONÍVEL")
        print()
        print("Modelos testados (todos falharam):")
        for model_name, model_id, error in unavailable_models:
            print(f"   • {model_name}: {error}")
        print()
        print("🔍 VERIFIQUE:")
        print("   1. Sua conta tem créditos?")
        print("      → https://console.anthropic.com/settings/billing")
        print()
        print("   2. Sua API key foi criada recentemente?")
        print("      → https://console.anthropic.com/settings/keys")
        print()
        print("   3. Tente criar uma NOVA API key e testar novamente")
        print()
        return False


if __name__ == "__main__":
    print()

    # Pega API key do argumento ou pede input
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        print("Digite sua API key da Anthropic:")
        print("(cole aqui e pressione Enter)")
        print()
        api_key = input("API Key: ").strip()

    print()

    if not api_key:
        print("❌ API key não fornecida.")
        print()
        print("Uso:")
        print("  python test_api_key.py")
        print("  ou")
        print("  python test_api_key.py sk-ant-api03-...")
        sys.exit(1)

    # Executa teste
    success = test_api_key(api_key)

    print()
    print("=" * 70)

    if success:
        print("✅ TESTE CONCLUÍDO COM SUCESSO")
        sys.exit(0)
    else:
        print("❌ TESTE FALHOU - VERIFIQUE OS ERROS ACIMA")
        sys.exit(1)
