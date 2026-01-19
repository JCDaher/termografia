"""
Módulo core.
Processamento de imagens FLIR e análise térmica.
"""

from core.flir_processor import FLIRProcessor
from core.thermal_analyzer import ThermalAnalyzer, AsymmetryResult, BTTResult

__all__ = ['FLIRProcessor', 'ThermalAnalyzer', 'AsymmetryResult', 'BTTResult']
