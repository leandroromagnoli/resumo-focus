# Projeto Boletim Focus

Pipeline que baixa o boletim Focus do Banco Central do Brasil (BCB), extrai o
texto do PDF e, numa automação agendada, gera um resumo executivo enviado por
e-mail.

**Importante:** os scripts Python deste repositório fazem apenas o download
e a extração de texto — nada mais. O resumo executivo é escrito por um
agente que lê o texto extraído (seguindo as regras de [CLAUDE.md](CLAUDE.md),
como nunca citar uma mediana que não esteja no texto). A geração do resumo
e o envio por e-mail acontecem na automação agendada, fora destes scripts.

## Estrutura

```
Projeto_BoletimFocus/
├── CLAUDE.md                        # briefing do projeto
├── README.md
├── requirements.txt
├── pytest.ini
├── demo.py                          # roda o pipeline localmente (download + extração)
├── .github/
│   └── workflows/
│       └── focus-download.yml       # automação semanal (download + extração + commit)
├── src/
│   ├── baixar_focus.py              # baixa o PDF mais recente do Focus
│   └── extrair_texto.py             # extrai o texto do PDF em .txt
├── tests/
│   └── test_baixar_focus.py
├── data/                            # PDFs e textos baixados (focus_AAAA-MM-DD.*)
└── output/
    └── focus/                       # resumos executivos em markdown (gerados pelo agente)
```

## Como rodar localmente

Instale as dependências:

```
pip install -r requirements.txt
```

Rode o pipeline completo (baixa o PDF mais recente e extrai o texto):

```
python demo.py
```

Use `--abrir` para abrir o `.txt` gerado no navegador padrão ao final:

```
python demo.py --abrir
```

Os scripts também podem ser rodados individualmente:

```
python src/baixar_focus.py
python src/extrair_texto.py
```

## Como rodar os testes

Testes offline (sem chamada de rede):

```
pytest -m "not network"
```

Incluindo o teste que faz o download real do BCB:

```
pytest -m network
```

Todos os testes:

```
pytest
```

## Automação

O workflow [.github/workflows/focus-download.yml](.github/workflows/focus-download.yml)
roda toda segunda-feira às 9h15 BRT (12h15 UTC), ou manualmente via
`workflow_dispatch`. Ele baixa o PDF, extrai o texto e commita os arquivos
de volta em `data/`. A geração do resumo executivo em `output/focus/` e o
envio por e-mail ficam a cargo do agente, fora do escopo destes scripts.
