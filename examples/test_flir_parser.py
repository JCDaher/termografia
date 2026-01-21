"""
Script de teste/exemplo para o parser FLIR HTML.

Demonstra:
1. Parsing de arquivo HTML do FLIR Thermal Studio
2. Conversão para AnatomicalTemplate
3. Geração de relatório de validação
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.flir_html_parser import FLIRHTMLParser, parse_flir_html


def test_parser(html_path: Path):
    """
    Testa o parser com um arquivo HTML do FLIR.

    Args:
        html_path: Caminho para arquivo HTML
    """
    print("=" * 80)
    print("TESTE: Parser FLIR HTML")
    print("=" * 80)
    print(f"\nArquivo: {html_path}")

    if not html_path.exists():
        print(f"❌ Arquivo não encontrado: {html_path}")
        return

    # === 1. Parsing básico ===
    print("\n" + "=" * 80)
    print("1. PARSING DO ARQUIVO HTML")
    print("=" * 80)

    parser = FLIRHTMLParser()
    flir_data = parser.parse_file(html_path)

    print(f"\n✅ Parsing concluído!")
    print(f"   Arquivo fonte: {flir_data.source_file}")
    print(f"   Total de imagens: {len(flir_data.images)}")
    print(f"   Total de medições: {len(flir_data.get_all_measurements())}")

    # === 2. Detalhes das imagens ===
    print("\n" + "=" * 80)
    print("2. DETALHES DAS IMAGENS")
    print("=" * 80)

    for i, image in enumerate(flir_data.images, 1):
        print(f"\n📷 Imagem {i}: {image.filename}")
        print(f"   Informações do arquivo:")
        for key, value in image.file_info.items():
            print(f"      {key}: {value}")

        print(f"\n   Medições ({len(image.measurements)} ROIs):")
        for measurement in image.measurements:
            print(f"      {measurement}")

    # === 3. Todas as medições ===
    print("\n" + "=" * 80)
    print("3. TODAS AS MEDIÇÕES (CONSOLIDADO)")
    print("=" * 80)

    all_measurements = flir_data.get_all_measurements()
    print(f"\nTotal: {len(all_measurements)} medições\n")

    print(f"{'ROI Name':<40} {'Max':<12} {'Mean':<12} {'Min':<12}")
    print("-" * 80)

    for m in sorted(all_measurements, key=lambda x: x.roi_name):
        print(f"{m.roi_name:<40} {m.max_temp:>6.2f}°C   {m.mean_temp:>6.2f}°C   {m.min_temp:>6.2f}°C")

    # === 4. Conversão para template ===
    print("\n" + "=" * 80)
    print("4. CONVERSÃO PARA ANATOMICAL TEMPLATE")
    print("=" * 80)

    template = parser.to_anatomical_template(
        flir_data,
        template_name="Template Importado do FLIR - Teste"
    )

    print(f"\n✅ Template criado!")
    print(f"   Nome: {template.name}")
    print(f"   Categoria: {template.category}")
    print(f"   Total de ROIs: {len(template.rois)}")
    print(f"   Metadados: {template.metadata}")

    print(f"\n   ROIs no template:")
    for roi in template.rois[:5]:  # Mostra apenas primeiras 5
        print(f"      - {roi.name}")
        print(f"        Localização: {roi.anatomical_location}")
        print(f"        Tipo: {roi.region_type}")
        print(f"        Faixa esperada: {roi.expected_temp_range}")
        print(f"        Notas: {roi.notes}")
        print()

    if len(template.rois) > 5:
        print(f"      ... e mais {len(template.rois) - 5} ROIs")

    # Salva template como exemplo
    output_path = Path(__file__).parent / "template_flir_example.json"
    template.save_to_file(output_path)
    print(f"\n💾 Template salvo em: {output_path}")

    # === 5. Exemplo de validação ===
    print("\n" + "=" * 80)
    print("5. EXEMPLO DE RELATÓRIO DE VALIDAÇÃO")
    print("=" * 80)

    # Simula temperaturas do sistema (para demonstração)
    # Em uso real, viriam do MultiPointAnalyzer
    import random
    system_temperatures = {}
    for m in all_measurements:
        # Adiciona pequena variação aleatória (-0.3 a +0.3°C)
        variation = random.uniform(-0.3, 0.3)
        system_temperatures[m.roi_name] = m.mean_temp + variation

    # Gera relatório
    validation_report = parser.create_validation_report(
        flir_data,
        system_temperatures
    )

    print(validation_report)

    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 80)


def create_sample_html():
    """
    Cria arquivo HTML de exemplo para testes.
    """
    sample_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FLIR Thermal Studio - Export</title>
</head>
<body>
    <section>
        <table>
            <caption>File information</caption>
            <tr><th>File name</th><td>IR_Joelhos_Paciente123.jpg</td></tr>
            <tr><th>Resolution</th><td>640 × 480</td></tr>
            <tr><th>Date/Time</th><td>2024-01-15 14:30:25</td></tr>
        </table>

        <table>
            <caption>Measurements</caption>
            <tr><th>Name</th><th>Max</th><th>Mean</th><th>Min</th></tr>
            <tr><td>Joelho Direito</td><td>35.5 °C</td><td>34.2 °C</td><td>32.8 °C</td></tr>
            <tr><td>Joelho Esquerdo</td><td>35.1 °C</td><td>34.0 °C</td><td>32.5 °C</td></tr>
            <tr><td>Patela Direita</td><td>34.8 °C</td><td>33.5 °C</td><td>32.1 °C</td></tr>
            <tr><td>Patela Esquerda</td><td>34.6 °C</td><td>33.3 °C</td><td>31.9 °C</td></tr>
        </table>
    </section>

    <section>
        <table>
            <caption>File information</caption>
            <tr><th>File name</th><td>IR_Coluna_Paciente123.jpg</td></tr>
            <tr><th>Resolution</th><td>640 × 480</td></tr>
            <tr><th>Date/Time</th><td>2024-01-15 14:35:12</td></tr>
        </table>

        <table>
            <caption>Measurements</caption>
            <tr><th>Name</th><th>Max</th><th>Mean</th><th>Min</th></tr>
            <tr><td>C5 Esquerdo</td><td>34.2 °C</td><td>33.1 °C</td><td>31.8 °C</td></tr>
            <tr><td>C5 Direito</td><td>34.5 °C</td><td>33.3 °C</td><td>32.0 °C</td></tr>
            <tr><td>C6 Esquerdo</td><td>33.9 °C</td><td>32.8 °C</td><td>31.5 °C</td></tr>
            <tr><td>C6 Direito</td><td>34.1 °C</td><td>33.0 °C</td><td>31.7 °C</td></tr>
            <tr><td>L2-L3</td><td>35.0 °C</td><td>33.8 °C</td><td>32.4 °C</td></tr>
            <tr><td>T12-L1</td><td>34.8 °C</td><td>33.6 °C</td><td>32.2 °C</td></tr>
        </table>
    </section>
</body>
</html>"""

    sample_path = Path(__file__).parent / "sample_flir_export.html"
    with open(sample_path, 'w', encoding='utf-8') as f:
        f.write(sample_html)

    print(f"✅ Arquivo de exemplo criado: {sample_path}")
    return sample_path


def main():
    """Função principal."""
    print("\n🔥 TESTE DO PARSER FLIR HTML\n")

    if len(sys.argv) > 1:
        # Arquivo fornecido via linha de comando
        html_path = Path(sys.argv[1])
    else:
        # Cria arquivo de exemplo
        print("Nenhum arquivo fornecido. Criando arquivo de exemplo...\n")
        html_path = create_sample_html()
        print()

    # Executa teste
    test_parser(html_path)


if __name__ == "__main__":
    main()
