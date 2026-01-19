notepad CLAUDE_INSTRUCTIONS.md
# INSTRUÇÕES PARA CLAUDE CODE

Desenvolver aplicativo Windows desktop em Python para análise termográfica médica.

## FASE 1 - MVP (COMEÇAR AQUI)

1. **config/security.py** - Criptografia DPAPI (win32crypt)
2. **core/flir_processor.py** - Processar imagens FLIR, extrair temperatura
3. **core/thermal_analyzer.py** - Calcular ΔT, classificar assimetrias
4. **api/claude_client.py** - Integração Anthropic API
5. **api/prompts.py** - System prompts
6. **ui/main_window.py** - Interface PyQt6 básica
7. **database/schema.sql** - Banco SQLite
8. **main.py** - Entry point

## FUNCIONALIDADES

- Processar imagens FLIR radiométricas
- Detectar assimetrias em dermátomos (L1-S1, T1-T12)
- Análise BTT (Brain Thermal Tunnel) para cefaleia
- Gerar laudos com Claude Sonnet 4
- Exportar PDF profissional
- Dados 100% locais (SQLite)

## TECNOLOGIAS
Python 3.11+, PyQt6, OpenCV, NumPy, Anthropic API, SQLite, ReportLab

Repositório: C:\Users\Win10\Documents\termografia
