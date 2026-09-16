"""Gera o card visual (IPCA, PIB, Câmbio, Selic) a partir do texto do Focus.

Todo o parsing dos números é determinístico (regex sobre o texto extraído
do PDF) - nada aqui é decidido por um modelo de linguagem, seguindo a mesma
regra de "nunca inventar número" do resto do projeto. Se o layout do PDF
mudar e o parsing não encontrar o que espera, uma exceção é levantada em
vez de desenhar um valor errado.
"""

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PASTA_DATA = Path("data")
PASTA_ASSETS = Path("assets")
PASTA_SAIDA = Path("output/focus")

FONTE_BOLD = PASTA_ASSETS / "fonts" / "DejaVuSans-Bold.ttf"
FONTE_REGULAR = PASTA_ASSETS / "fonts" / "DejaVuSans.ttf"
LOGO_PETROBRAS = PASTA_ASSETS / "logo_petrobras.jpg"
SELO_INTERNO = PASTA_ASSETS / "publico.jpg"

# Aproximação pública das cores institucionais da Petrobras (verde e
# amarelo) - ajustar se houver o hex exato do manual de marca.
VERDE_PETROBRAS = (0, 92, 63)
VERDE_CLARO = (232, 245, 238)
AMARELO_PETROBRAS = (255, 204, 0)
CINZA_TEXTO = (60, 60, 60)
CINZA_CLARO = (140, 140, 140)
VERMELHO_QUEDA = (196, 30, 30)
VERDE_ALTA = (0, 92, 63)
CINZA_ESTAVEL = (120, 120, 120)
BRANCO = (255, 255, 255)
PRETO = (20, 20, 20)
VERDE_VALOR = (0, 133, 66)  # #008542 - cor das medianas

LARGURA = 640
ALTURA_HEADER = 110
ALTURA_QUAD = 280
ALTURA_LEGENDA = 50
ALTURA_RODAPE = 60
ALTURA = ALTURA_HEADER + 2 * ALTURA_QUAD + ALTURA_LEGENDA + ALTURA_RODAPE

INDICADORES = [
    ("IPCA", "%", r"IPCA \(variação %\)"),
    ("PIB", "var. %", r"PIB Total \(variação % sobre ano anterior\)"),
    ("CÂMBIO", "R$/US$", r"Câmbio \(R\$/US\$\)"),
    ("SELIC", "% a.a.", r"Selic \(% a\.a\)"),
]

MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def _consumir_bloco_ano(tokens: list, indice: int):
    """Consome um bloco de ano: há4, há1, hoje, [seta], (semanas), resp30.

    Retorna (valor_hoje, seta, novo_indice). 'seta' é '▲', '▼' ou None
    (quando o indicador está estável).
    """
    indice += 2  # pula "há 4 semanas" e "há 1 semana"
    hoje = tokens[indice]
    indice += 1
    seta = None
    if tokens[indice] in ("▲", "▼"):
        seta = tokens[indice]
        indice += 1
    indice += 1  # pula o "(semanas)"
    indice += 1  # pula o respondentes-30-dias
    return hoje, seta, indice


def extrair_medianas(texto: str) -> dict:
    """Extrai as medianas de IPCA/PIB/Câmbio/Selic para os dois primeiros
    anos da tabela anual do Focus, com a seta de comparação semanal.
    """
    # Restringe a busca à tabela ANUAL: "Câmbio" e "Selic" também aparecem
    # numa segunda tabela (mensal), com estrutura diferente, mais adiante
    # no texto.
    marcador_mensal = re.search(
        r"\b(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)/20\d{2}\b", texto
    )
    texto_anual = texto[: marcador_mensal.start()] if marcador_mensal else texto

    match_anos = re.search(r"\b(20\d{2})\s+(20\d{2})\s+20\d{2}\s+20\d{2}\b", texto_anual)
    if not match_anos:
        raise ValueError("Não foi possível localizar o cabeçalho de anos no texto.")
    ano1, ano2 = match_anos.group(1), match_anos.group(2)

    indicadores = []
    for nome, unidade, rotulo_regex in INDICADORES:
        match = re.search(rotulo_regex + r"\s+(.+)", texto_anual)
        if not match:
            raise ValueError(f"Linha de '{nome}' não encontrada no texto.")
        # Números com vírgula decimal (valores), números inteiros sem
        # vírgula (contagem de respondentes), parênteses (semanas) e setas.
        tokens = re.findall(r"-?\d+,\d+|\(\d+\)|[▲▼]|-?\d+", match.group(1))

        hoje1, seta1, i = _consumir_bloco_ano(tokens, 0)
        i += 2  # colunas extras do ano 1 (resp. 5 dias úteis)
        hoje2, seta2, _ = _consumir_bloco_ano(tokens, i)

        indicadores.append(
            {
                "nome": nome,
                "unidade": unidade,
                "ano1_valor": hoje1,
                "ano1_seta": seta1,
                "ano2_valor": hoje2,
                "ano2_seta": seta2,
            }
        )

    return {"ano1": ano1, "ano2": ano2, "indicadores": indicadores}


def _cor_seta(seta):
    if seta == "▲":
        return VERDE_ALTA
    if seta == "▼":
        return VERMELHO_QUEDA
    return CINZA_ESTAVEL


def _texto_centralizado(draw, texto, fonte, centro_x, y, cor):
    caixa = draw.textbbox((0, 0), texto, font=fonte)
    largura = caixa[2] - caixa[0]
    draw.text((centro_x - largura / 2, y), texto, font=fonte, fill=cor)


def _data_extenso(data_iso: str) -> str:
    ano, mes, dia = data_iso.split("-")
    return f"{int(dia)} de {MESES_PT[int(mes) - 1]} de {ano}"


def desenhar_card(dados: dict, data_publicacao: str) -> Image.Image:
    fonte_titulo = ImageFont.truetype(str(FONTE_BOLD), 30)
    fonte_subtitulo = ImageFont.truetype(str(FONTE_REGULAR), 14)
    fonte_quad_titulo = ImageFont.truetype(str(FONTE_BOLD), 20)
    fonte_quad_unidade = ImageFont.truetype(str(FONTE_REGULAR), 13)
    fonte_ano = ImageFont.truetype(str(FONTE_REGULAR), 15)
    fonte_valor = ImageFont.truetype(str(FONTE_BOLD), 34)
    fonte_seta = ImageFont.truetype(str(FONTE_BOLD), 24)
    fonte_legenda = ImageFont.truetype(str(FONTE_REGULAR), 13)
    fonte_rodape = ImageFont.truetype(str(FONTE_REGULAR), 12)

    img = Image.new("RGB", (LARGURA, ALTURA), BRANCO)
    draw = ImageDraw.Draw(img)

    # --- Cabeçalho (logo + título) ---
    if LOGO_PETROBRAS.exists():
        logo = Image.open(LOGO_PETROBRAS)
        escala = 60 / logo.height
        logo = logo.resize((int(logo.width * escala), 60))
        img.paste(logo, (24, (ALTURA_HEADER - 6 - logo.height) // 2))
        x_titulo = 24 + logo.width + 20
    else:
        x_titulo = 24

    draw.text((x_titulo, 22), "Boletim Focus", font=fonte_titulo, fill=VERDE_PETROBRAS)
    draw.text(
        (x_titulo, 58),
        "Resumo das Expectativas de Mercado",
        font=fonte_subtitulo,
        fill=CINZA_TEXTO,
    )
    # Faixa amarela divisória
    draw.rectangle(
        [(0, ALTURA_HEADER - 6), (LARGURA, ALTURA_HEADER)], fill=AMARELO_PETROBRAS
    )

    # --- Grade 2x2 ---
    fundo_quad = [VERDE_CLARO, BRANCO, BRANCO, VERDE_CLARO]
    for idx, indicador in enumerate(dados["indicadores"]):
        col = idx % 2
        lin = idx // 2
        x0 = col * (LARGURA // 2)
        y0 = ALTURA_HEADER + lin * ALTURA_QUAD
        x1 = x0 + LARGURA // 2
        y1 = y0 + ALTURA_QUAD

        draw.rectangle([(x0, y0), (x1, y1)], fill=fundo_quad[idx])

        titulo = f"{indicador['nome']} ({indicador['unidade']})"
        draw.text((x0 + 20, y0 + 18), titulo, font=fonte_quad_titulo, fill=VERDE_PETROBRAS)

        centro_col1 = x0 + (x1 - x0) // 4 + 10
        centro_col2 = x0 + 3 * (x1 - x0) // 4 - 10

        for centro_x, ano, valor, seta in (
            (centro_col1, dados["ano1"], indicador["ano1_valor"], indicador["ano1_seta"]),
            (centro_col2, dados["ano2"], indicador["ano2_valor"], indicador["ano2_seta"]),
        ):
            _texto_centralizado(draw, ano, fonte_ano, centro_x, y0 + 75, CINZA_CLARO)
            _texto_centralizado(draw, valor, fonte_valor, centro_x, y0 + 100, VERDE_VALOR)
            simbolo = seta if seta else "="
            _texto_centralizado(
                draw, simbolo, fonte_seta, centro_x, y0 + 150, _cor_seta(seta)
            )

    # Linhas divisórias da grade
    y_meio = ALTURA_HEADER + ALTURA_QUAD
    draw.line([(0, y_meio), (LARGURA, y_meio)], fill=BRANCO, width=4)
    draw.line(
        [(LARGURA // 2, ALTURA_HEADER), (LARGURA // 2, ALTURA_HEADER + 2 * ALTURA_QUAD)],
        fill=BRANCO,
        width=4,
    )

    # --- Legenda ---
    y_legenda = ALTURA_HEADER + 2 * ALTURA_QUAD + 18
    legenda = "▲ Aumento     ▼ Diminuição     = Estabilidade"
    _texto_centralizado(draw, legenda, fonte_legenda, LARGURA // 2, y_legenda, CINZA_TEXTO)

    # --- Rodapé (fonte dos dados) ---
    y_rodape = ALTURA_HEADER + 2 * ALTURA_QUAD + ALTURA_LEGENDA
    draw.rectangle([(0, y_rodape), (LARGURA, y_rodape + 2)], fill=AMARELO_PETROBRAS)
    texto_rodape = f"Fonte: Boletim Focus, Banco Central do Brasil - {_data_extenso(data_publicacao)}"
    _texto_centralizado(
        draw, texto_rodape, fonte_rodape, LARGURA // 2, y_rodape + 22, CINZA_TEXTO
    )

    # Selo "uso interno" no canto inferior direito.
    if SELO_INTERNO.exists():
        selo = Image.open(SELO_INTERNO)
        escala = 28 / selo.height
        selo = selo.resize((int(selo.width * escala), 28))
        img.paste(selo, (LARGURA - selo.width - 16, ALTURA - selo.height - 10))

    return img


def _txt_mais_recente(pasta: Path = PASTA_DATA):
    arquivos = sorted(pasta.glob("focus_*.txt"))
    return arquivos[-1] if arquivos else None


def gerar_card(txt_path: Path, dest: Path = PASTA_SAIDA) -> Path:
    match_data = re.search(r"(\d{4}-\d{2}-\d{2})", txt_path.stem)
    if not match_data:
        raise ValueError(f"Não foi possível extrair a data do nome: {txt_path.name}")
    data_publicacao = match_data.group(1)

    texto = txt_path.read_text(encoding="utf-8")
    dados = extrair_medianas(texto)
    imagem = desenhar_card(dados, data_publicacao)

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    caminho_saida = dest / f"card_focus_{data_publicacao}.jpg"
    imagem.save(caminho_saida, "JPEG", quality=92)
    return caminho_saida


def main():
    parser = argparse.ArgumentParser(
        description="Gera o card visual do boletim Focus (IPCA, PIB, Câmbio, Selic)."
    )
    parser.add_argument(
        "--txt",
        help="Caminho de um .txt específico. Se omitido, usa o focus_*.txt "
        "mais recente de data/.",
    )
    args = parser.parse_args()

    if args.txt:
        txt_path = Path(args.txt)
    else:
        txt_encontrado = _txt_mais_recente()
        if txt_encontrado is None:
            print("Nenhum .txt encontrado em data/. Rode src/baixar_focus.py e src/extrair_texto.py primeiro.")
            return 1
        txt_path = txt_encontrado

    caminho_saida = gerar_card(txt_path)
    tamanho_kb = caminho_saida.stat().st_size / 1024
    print(f"Card gerado em: {caminho_saida} ({tamanho_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
