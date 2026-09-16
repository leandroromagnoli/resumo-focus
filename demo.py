"""Demo do pipeline: baixa o boletim Focus e extrai o texto, em sequência."""

import argparse
import sys
import webbrowser
from pathlib import Path

# Adiciona a pasta src/ ao path de import para poder importar os módulos
# baixar_focus e extrair_texto sem precisar transformá-los em um pacote.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from baixar_focus import baixar
from extrair_texto import extrair


def main():
    parser = argparse.ArgumentParser(
        description="Baixa o boletim Focus e extrai o texto do PDF."
    )
    parser.add_argument(
        "--abrir",
        action="store_true",
        help="Abre o .txt gerado no navegador padrão ao final.",
    )
    args = parser.parse_args()

    # Etapa 1: baixa o PDF mais recente para a pasta data/.
    _data_publicacao, caminho_pdf = baixar("data")
    tamanho_kb = caminho_pdf.stat().st_size / 1024
    print(f"[1/2] PDF baixado: {caminho_pdf.name} ({tamanho_kb:.1f} KB)")

    # Etapa 2: extrai o texto do PDF baixado.
    caminho_txt = extrair(caminho_pdf)
    print(f"[2/2] Texto extraído: {caminho_txt}")

    if args.abrir:
        # file:// URI necessária para o webbrowser abrir um arquivo local.
        webbrowser.open(caminho_txt.resolve().as_uri())


if __name__ == "__main__":
    main()
