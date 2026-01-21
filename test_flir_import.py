"""
Script de teste para diagnosticar problemas com importação FLIR.
"""

print("=" * 60)
print("TESTE DE IMPORTAÇÃO FLIR")
print("=" * 60)

print("\n1. Testando import bs4...")
try:
    from bs4 import BeautifulSoup
    print("   ✅ bs4 importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro ao importar bs4: {e}")

print("\n2. Testando import do parser...")
try:
    from core.flir_html_parser import parse_flir_html
    print("   ✅ Parser importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro ao importar parser: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Verificando módulos necessários...")
modules_to_check = [
    'bs4',
    'numpy',
    'pathlib',
    'dataclasses'
]

for module_name in modules_to_check:
    try:
        __import__(module_name)
        print(f"   ✅ {module_name}")
    except ImportError as e:
        print(f"   ❌ {module_name}: {e}")

print("\n" + "=" * 60)
print("TESTE COMPLETO")
print("=" * 60)
print("\nSe todos os itens acima mostrarem ✅, o sistema está OK.")
print("Se houver ❌, instale o módulo faltante com:")
print("  pip install <nome-do-modulo>")
print("\nPara beautifulsoup4:")
print("  pip install beautifulsoup4")
