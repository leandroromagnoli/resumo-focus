"""Baixa o PDF mais recente do boletim Focus do Banco Central do Brasil."""

from datetime import date, timedelta
from pathlib import Path

import requests

# User-Agent de navegador: o servidor do BCB pode rejeitar requisições
# sem esse cabeçalho, tratando-as como acesso automatizado.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

URL_BASE = "https://www.bcb.gov.br/content/focus/focus/R{data}.pdf"


def ultima_segunda(hoje: date) -> date:
    """Retorna a segunda-feira mais recente ESTRITAMENTE anterior a 'hoje'.

    Se 'hoje' já for segunda-feira, retrocede para a segunda da semana
    passada (7 dias antes), pois a segunda da semana atual coincidiria
    com 'hoje' e não seria estritamente anterior.
    """
    # weekday(): segunda-feira = 0, domingo = 6.
    dias_desde_segunda = hoje.weekday()
    if dias_desde_segunda == 0:
        dias_para_voltar = 7
    else:
        dias_para_voltar = dias_desde_segunda
    return hoje - timedelta(days=dias_para_voltar)


def baixar(dest: str):
    """Tenta baixar o boletim Focus, partindo da última segunda-feira.

    Parte da última segunda-feira estritamente anterior a hoje e, se o
    PDF não estiver disponível nessa data (ex.: feriado), recua um dia
    por vez, até 7 tentativas no total (cobre o caso de feriados
    prolongados na segunda-feira).

    Retorna uma tupla (data_da_publicacao, caminho_do_arquivo).
    Levanta RuntimeError se nenhuma das 7 tentativas funcionar.
    """
    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)

    data_inicial = ultima_segunda(date.today())
    headers = {"User-Agent": USER_AGENT}

    for tentativa in range(7):
        data_candidata = data_inicial - timedelta(days=tentativa)
        url = URL_BASE.format(data=data_candidata.strftime("%Y%m%d"))

        try:
            resposta = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException:
            # Falha de rede nesta tentativa: passa para o dia anterior.
            continue

        # Só aceita a resposta se ela realmente for um PDF válido
        # (o BCB pode retornar 200 com uma página de erro em HTML).
        if resposta.status_code == 200 and resposta.content[:4] == b"%PDF":
            nome_arquivo = f"focus_{data_candidata.strftime('%Y-%m-%d')}.pdf"
            caminho_arquivo = dest_path / nome_arquivo
            caminho_arquivo.write_bytes(resposta.content)
            return data_candidata, caminho_arquivo

    raise RuntimeError(
        "Não foi possível encontrar o PDF do boletim Focus nas últimas "
        "7 tentativas (verifique feriados prolongados ou mudança na URL)."
    )


def main():
    data_publicacao, caminho_arquivo = baixar("data")
    tamanho_kb = caminho_arquivo.stat().st_size / 1024
    print(f"Boletim Focus de {data_publicacao} baixado em: {caminho_arquivo}")
    print(f"Tamanho: {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
