"""Extrai o texto de um PDF do boletim Focus e salva como .txt."""

import argparse
import sys
from pathlib import Path

import pdfplumber


def extrair(pdf_path: str) -> Path:
    """Extrai o texto de todas as páginas do PDF e salva em um .txt.

    O arquivo .txt é salvo no mesmo diretório e com o mesmo nome do PDF,
    apenas trocando a extensão, codificado em UTF-8.

    Retorna o caminho do arquivo .txt gerado.
    """
    pdf_path = Path(pdf_path)
    partes_texto = []

    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                partes_texto.append(texto_pagina)

    texto_completo = "\n".join(partes_texto)

    txt_path = pdf_path.with_suffix(".txt")
    txt_path.write_text(texto_completo, encoding="utf-8")

    return txt_path


def _pdf_mais_recente(pasta_data: Path) -> Path | None:
    """Retorna o PDF focus_*.pdf mais recente da pasta, ou None se vazia."""
    pdfs = sorted(pasta_data.glob("focus_*.pdf"))
    if not pdfs:
        return None
    # Os nomes seguem o padrão focus_AAAA-MM-DD.pdf, então a ordenação
    # alfabética já corresponde à ordenação cronológica.
    return pdfs[-1]


def main():
    parser = argparse.ArgumentParser(
        description="Extrai o texto de um PDF do boletim Focus."
    )
    parser.add_argument(
        "--pdf",
        help="Caminho de um PDF específico. Se omitido, usa o focus_*.pdf "
        "mais recente da pasta data/.",
    )
    args = parser.parse_args()

    if args.pdf:
        pdf_path = Path(args.pdf)
    else:
        pasta_data = Path("data")
        pdf_encontrado = _pdf_mais_recente(pasta_data)
        if pdf_encontrado is None:
            print(
                "Nenhum PDF encontrado em data/. "
                "Rode 'python src/baixar_focus.py' primeiro."
            )
            return 1
        pdf_path = pdf_encontrado

    txt_path = extrair(pdf_path)
    print(f"Texto extraído para: {txt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
