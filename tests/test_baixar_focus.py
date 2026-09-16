"""Testes para src/baixar_focus.py."""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

# Adiciona a pasta src/ ao path de import, como feito em demo.py.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from baixar_focus import baixar, ultima_segunda


# ---------------------------------------------------------------------------
# Testes puros de ultima_segunda (sem rede)
# ---------------------------------------------------------------------------


def test_ultima_segunda_quinta():
    # Quinta-feira, 17/09/2026 -> segunda da mesma semana, 14/09/2026.
    hoje = date(2026, 9, 17)
    assert ultima_segunda(hoje) == date(2026, 9, 14)


def test_ultima_segunda_terca():
    # Terça-feira, 15/09/2026 -> segunda da mesma semana, 14/09/2026.
    hoje = date(2026, 9, 15)
    assert ultima_segunda(hoje) == date(2026, 9, 14)


def test_ultima_segunda_quando_hoje_e_segunda():
    # Segunda-feira, 14/09/2026 -> deve recuar para a segunda anterior,
    # 07/09/2026, pois o resultado precisa ser ESTRITAMENTE anterior a hoje.
    hoje = date(2026, 9, 14)
    assert ultima_segunda(hoje) == date(2026, 9, 7)


def test_ultima_segunda_domingo():
    # Domingo, 13/09/2026 -> segunda da semana anterior, 07/09/2026.
    hoje = date(2026, 9, 13)
    assert ultima_segunda(hoje) == date(2026, 9, 7)


def test_ultima_segunda_varredura_60_dias():
    # Para qualquer data num intervalo de 60 dias, o resultado deve ser
    # sempre uma segunda-feira estritamente anterior à data dada.
    data_base = date(2026, 1, 1)
    for i in range(60):
        hoje = data_base + timedelta(days=i)
        resultado = ultima_segunda(hoje)
        assert resultado.weekday() == 0, f"{resultado} não é segunda-feira"
        assert resultado < hoje, f"{resultado} não é anterior a {hoje}"


# ---------------------------------------------------------------------------
# Teste de rede (download real do BCB)
# ---------------------------------------------------------------------------


@pytest.mark.network
def test_baixar_download_real(tmp_path):
    hoje = date.today()

    data_publicacao, caminho_arquivo = baixar(str(tmp_path))

    # O arquivo deve ter sido criado.
    assert caminho_arquivo.exists()

    # Deve começar com os bytes mágicos de um PDF.
    conteudo = caminho_arquivo.read_bytes()
    assert conteudo[:4] == b"%PDF"

    # Deve ter mais de 50 KB (um boletim Focus real é bem maior que isso;
    # um valor pequeno indicaria uma página de erro ou PDF corrompido).
    assert len(conteudo) > 50 * 1024

    # O nome do arquivo deve corresponder à data de publicação retornada.
    nome_esperado = f"focus_{data_publicacao.strftime('%Y-%m-%d')}.pdf"
    assert caminho_arquivo.name == nome_esperado

    # A data de publicação deve estar numa janela plausível: não pode
    # ser no futuro, e não deve estar mais de 14 dias no passado (a
    # função parte da última segunda e recua no máximo 6 dias além
    # dela, então esse é o pior caso esperado).
    assert data_publicacao < hoje
    assert (hoje - data_publicacao).days <= 14
