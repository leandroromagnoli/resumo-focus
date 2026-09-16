"""Testes para o parser determinístico de src/gerar_card.py.

Usa o texto real já commitado em data/focus_2026-09-11.txt e confere os
valores extraídos contra o card de referência fornecido pelo usuário
(assets/referencia_layout_bcb.jpg) - garante que o parser nunca "inventa"
um valor que não esteja no texto-fonte.
"""

import sys
from pathlib import Path

# Adiciona a pasta src/ ao path de import, como feito em demo.py.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gerar_card import extrair_medianas

TXT_REFERENCIA = Path(__file__).parent.parent / "data" / "focus_2026-09-11.txt"


def _carregar_dados():
    texto = TXT_REFERENCIA.read_text(encoding="utf-8")
    return extrair_medianas(texto)


def test_anos_extraidos():
    dados = _carregar_dados()
    assert dados["ano1"] == "2026"
    assert dados["ano2"] == "2027"


def test_ipca():
    dados = _carregar_dados()
    ipca = next(i for i in dados["indicadores"] if i["nome"] == "IPCA")
    assert ipca["ano1_valor"] == "4,90"
    assert ipca["ano1_seta"] == "▼"
    assert ipca["ano2_valor"] == "4,30"
    assert ipca["ano2_seta"] == "▲"


def test_pib():
    dados = _carregar_dados()
    pib = next(i for i in dados["indicadores"] if i["nome"] == "PIB")
    assert pib["ano1_valor"] == "1,89"
    assert pib["ano1_seta"] == "▼"
    assert pib["ano2_valor"] == "1,45"
    assert pib["ano2_seta"] == "▼"


def test_cambio():
    dados = _carregar_dados()
    cambio = next(i for i in dados["indicadores"] if i["nome"] == "CÂMBIO")
    assert cambio["ano1_valor"] == "5,20"
    assert cambio["ano1_seta"] is None
    assert cambio["ano2_valor"] == "5,28"
    assert cambio["ano2_seta"] == "▼"


def test_selic():
    dados = _carregar_dados()
    selic = next(i for i in dados["indicadores"] if i["nome"] == "SELIC")
    assert selic["ano1_valor"] == "13,75"
    assert selic["ano1_seta"] is None
    assert selic["ano2_valor"] == "12,00"
    assert selic["ano2_seta"] is None
