# Projeto Boletim Focus

## Objetivo

Baixar o boletim Focus do Banco Central do Brasil (BCB) toda segunda-feira,
extrair o texto do PDF e preparar um resumo executivo.

## Fonte

- Página oficial: https://www.bcb.gov.br/publicacoes/focus
- Padrão de URL do PDF: `https://www.bcb.gov.br/content/focus/focus/R{AAAAMMDD}.pdf`
  (ex.: publicação de 09/09/2026 → `R20260909.pdf`)

## Convenções

- Arquivos nomeados `focus_AAAA-MM-DD` (data da publicação, não da execução).
- `data/` guarda os PDFs baixados e os textos extraídos.
- `output/focus/` guarda os resumos executivos em markdown.

## Regras

- Nunca inventar número: toda mediana citada no resumo deve estar presente
  no texto extraído do PDF.
- Quando a segunda-feira é feriado, o BCB publica o boletim na terça-feira.
  O download deve retroceder dia a dia (segunda → terça → quarta → ...) até
  encontrar o PDF disponível.

## Estrutura

- `src/` — código-fonte (download, extração, resumo).
- `tests/` — testes automatizados.
- `data/` — PDFs e textos brutos baixados.
- `output/focus/` — resumos executivos em markdown.
- `.github/workflows/` — automação (ex.: execução semanal via GitHub Actions).
