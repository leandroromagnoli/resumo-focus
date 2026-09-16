"""Envia por e-mail o resumo em HTML do boletim Focus, via SMTP do Gmail.

Credenciais NUNCA ficam no código. São lidas de variáveis de ambiente:

- FOCUS_SMTP_USER      -> endereço Gmail remetente.
- FOCUS_SMTP_PASSWORD  -> senha de app do Gmail (não é a senha normal da
                           conta; gerada em myaccount.google.com/apppasswords).
- FOCUS_EMAIL_DEST     -> destinatários, separados por vírgula.
- FOCUS_EMAIL_BCC      -> (opcional) cópias ocultas, separadas por vírgula.
"""

import argparse
import os
import re
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

PASTA_RESUMOS = Path("output/focus")


def localizar_html_mais_recente(pasta: Path = PASTA_RESUMOS) -> Path | None:
    """Retorna o focus_*.html mais recente da pasta, ou None se não houver.

    Os nomes seguem o padrão focus_AAAA-MM-DD.html, então a ordenação
    alfabética já corresponde à ordenação cronológica.
    """
    arquivos = sorted(pasta.glob("focus_*.html"))
    if not arquivos:
        return None
    return arquivos[-1]


def _extrair_data_do_nome(html_path: Path) -> str:
    """Extrai a data AAAA-MM-DD do nome do arquivo focus_AAAA-MM-DD.html."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", html_path.stem)
    if not match:
        raise ValueError(
            f"Não foi possível extrair a data do nome do arquivo: {html_path.name}"
        )
    return match.group(1)


def _html_para_texto_simples(html: str) -> str:
    """Gera um fallback em texto simples a partir do HTML, removendo tags.

    É apenas um fallback para clientes de e-mail que não renderizam HTML;
    não precisa ser uma conversão perfeita.
    """
    texto = re.sub(r"<[^>]+>", " ", html)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n\n", texto)
    return texto.strip()


def montar_mensagem(
    html_path: Path,
    remetente: str,
    destinatarios: list[str],
    bcc: list[str] | None = None,
    assunto: str | None = None,
) -> MIMEMultipart:
    """Monta a mensagem de e-mail (HTML + fallback texto) a partir do arquivo.

    Não envia nada — só monta o objeto de mensagem, para poder ser
    inspecionado (--dry-run) ou passado para enviar().
    """
    html = html_path.read_text(encoding="utf-8")

    if assunto is None:
        data_publicacao = _extrair_data_do_nome(html_path)
        assunto = f"Resumo Focus - {data_publicacao}"

    mensagem = MIMEMultipart("alternative")
    mensagem["Subject"] = assunto
    mensagem["From"] = remetente
    mensagem["To"] = ", ".join(destinatarios)
    if bcc:
        mensagem["Bcc"] = ", ".join(bcc)

    # A ordem importa: o cliente de e-mail usa a ÚLTIMA parte compatível,
    # então o texto simples (fallback) vai primeiro e o HTML por último.
    mensagem.attach(MIMEText(_html_para_texto_simples(html), "plain", "utf-8"))
    mensagem.attach(MIMEText(html, "html", "utf-8"))

    return mensagem


def enviar(mensagem: MIMEMultipart, remetente: str, senha_app: str) -> None:
    """Conecta no SMTP do Gmail (SSL) e envia a mensagem já montada."""
    destinatarios_finais = mensagem["To"].split(", ")
    if mensagem["Bcc"]:
        destinatarios_finais += mensagem["Bcc"].split(", ")

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as servidor:
        servidor.login(remetente, senha_app)
        servidor.sendmail(remetente, destinatarios_finais, mensagem.as_string())


def main():
    parser = argparse.ArgumentParser(
        description="Envia por e-mail o resumo em HTML do boletim Focus."
    )
    parser.add_argument(
        "--html",
        help="Caminho de um resumo .html específico. Se omitido, usa o "
        "focus_*.html mais recente de output/focus/.",
    )
    parser.add_argument(
        "--dest",
        help="Destinatários, separados por vírgula. Se omitido, usa a "
        "variável de ambiente FOCUS_EMAIL_DEST.",
    )
    parser.add_argument(
        "--assunto",
        help="Assunto do e-mail. Se omitido, é derivado da data no nome "
        "do arquivo: 'Resumo Focus - AAAA-MM-DD'.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Monta e mostra o e-mail no terminal, sem enviar e sem "
        "exigir credenciais de SMTP.",
    )
    args = parser.parse_args()

    # Passo 1: localizar o HTML a enviar.
    if args.html:
        html_path = Path(args.html)
    else:
        html_encontrado = localizar_html_mais_recente()
        if html_encontrado is None:
            print(
                "Nenhum resumo .html encontrado em output/focus/. "
                "Gere o resumo antes de rodar este script."
            )
            return 1
        html_path = html_encontrado

    if not html_path.exists():
        print(f"Arquivo não encontrado: {html_path}")
        return 1

    # Passo 2: resolver destinatários (argumento tem prioridade sobre env var).
    dest_bruto = args.dest or os.environ.get("FOCUS_EMAIL_DEST", "")
    destinatarios = [d.strip() for d in dest_bruto.split(",") if d.strip()]
    if not destinatarios:
        print(
            "Nenhum destinatário definido. Use --dest ou a variável de "
            "ambiente FOCUS_EMAIL_DEST."
        )
        return 1

    bcc_bruto = os.environ.get("FOCUS_EMAIL_BCC", "")
    bcc = [b.strip() for b in bcc_bruto.split(",") if b.strip()]

    # Passo 3: resolver remetente. Em --dry-run, um placeholder basta,
    # pois nenhuma conexão SMTP será feita.
    remetente = os.environ.get("FOCUS_SMTP_USER")
    if not remetente:
        if args.dry_run:
            remetente = "(FOCUS_SMTP_USER não definida - modo dry-run)"
        else:
            print("Variável de ambiente FOCUS_SMTP_USER não definida.")
            return 1

    mensagem = montar_mensagem(
        html_path=html_path,
        remetente=remetente,
        destinatarios=destinatarios,
        bcc=bcc,
        assunto=args.assunto,
    )

    if args.dry_run:
        print("--- MODO DRY-RUN: nada será enviado ---")
        print(f"De: {mensagem['From']}")
        print(f"Para: {mensagem['To']}")
        if mensagem["Bcc"]:
            print(f"Cco: {mensagem['Bcc']}")
        print(f"Assunto: {mensagem['Subject']}")
        print("--- corpo HTML ---")
        print(html_path.read_text(encoding="utf-8"))
        return 0

    # Envio real: aqui sim as credenciais de SMTP são obrigatórias.
    senha_app = os.environ.get("FOCUS_SMTP_PASSWORD")
    if not senha_app:
        print(
            "Variável de ambiente FOCUS_SMTP_PASSWORD não definida "
            "(senha de app do Gmail)."
        )
        return 1

    enviar(mensagem, remetente=remetente, senha_app=senha_app)
    print(f"E-mail enviado para: {mensagem['To']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
