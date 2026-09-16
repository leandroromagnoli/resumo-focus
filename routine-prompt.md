Você está executando a Routine de resumo semanal do Focus.

O download do PDF e a extração do texto já foram feitos por um GitHub Action mais cedo (segunda 9h15 BRT). Os arquivos 'data/focus_AAAA-MM-DD.{pdf, txt} já estão commitados em 'main' quando a Routine inicia. Sua tarefa é ler o '.txt' mais recente, gerar um resumo em HTML com a logo da Análise Macro e publicá-lo no repositório - é essa publicação que dispara o envio do e-mail.

## Passos

1. **Localize o '.txt' mais recente.** Liste 'data/focus_*.txt' e pegue o de data mais alta. Se não houver nenhum, pare sem commitar o HTML - o Action não rodou.

2. **Verifique o frescor.** Extraia a data do nome e compare com hoje:
- 0 a 3 dias: está fresco, siga.
- 4 a 7 dias: siga, mas escreva '[REVISAR]' no início do assunto.
- Mais de 7 dias: pare sem commitar o HTML.

3. **Sanity check do texto.** Confirme: pelo menos 2000 caracteres e a presença das palavras 'IPCA', 'Selic', 'PIB'. Se falhar, o layout do pdf pode ter mudado - pare sem commitar o HTML.

4. **Leia o texto.** e escreva o conteúdo do resumo:
- **Resumo executivo** em até 200 palavras, em prosa corrida. Comece pelas medianas das principais variáveis (IPCA do ano, Selic fim de ano, PIB, câmbio). Cite literalmente entre aspas quando houver número-chave.
- **Três principais revisões da semana** em bullets no formato:
'Variável (ano): anterior -> atual. Hipótese: motivo.'
- Nunca invente número. Se não houver hipótese sólida, escreva "sem hipótese clara - pode ser ruído amostral".

5. **Monte o HTML** do e-mail em 'output/focus/focus_AAAA-MM-DD.html', com esta estrutura:
- No '<head>', uma tag '<meta name="assunto" content="...">' com o assunto exato que o e-mail deve usar ('Resumo Focus - AAAA-MM-DD', com '[REVISAR]' na frente quando aplicável, conforme o passo 2). É assim que o assunto chega até o workflow de envio - sem essa tag, o assunto cai no padrão sem o prefixo.
- No topo, a logo da Análise Macro, carregada desta URL: 'https://analisemacro.com.br/wp-content/uploads/dlm_uploads/2021/10/logo_am.png'
- Um título 'Focus - AAAA-MM-DD'
- O resumo executivo em parágrafo e as três revisões em lista.
- Use as cores da marca: azul '#282f6b' nos títulos.

6. **Inspecione** o HTML gerado: a tag '<meta name="assunto">' está presente e com o assunto correto (incluindo '[REVISAR]' quando aplicável), a logo aparece, as medianas batem com o '.txt', há ao menos uma citação literal entre aspas.

7. **Publique o HTML.** Faça 'git add output/focus/focus_AAAA-MM-DD.html', commit e 'git push' para 'main'. É esse push que dispara o Action 'focus-enviar.yml', responsável pelo envio do e-mail - a Routine não envia e-mail diretamente. O assunto usado pelo envio vem da tag '<meta name="assunto">' gravada no passo 5 (com '[REVISAR]' na frente quando aplicável, conforme o passo 2); sem essa tag, o assunto cairia no padrão sem o prefixo. Destinatário, remetente e senha de app ficam nos Secrets do repositório ('FOCUS_EMAIL_DEST', 'FOCUS_SMTP_USER', 'FOCUS_SMTP_PASSWORD') - nunca no arquivo HTML nem em qualquer outro arquivo commitado.

## Falhas

Em qualquer cenário abaixo, pare sem commitar o HTML. O motivo aparece no transcript da Routine.

- Nenhum '.txt' em 'data/' (Action não rodou).
- '.txt' com mais de 7 dias (Action quebrado).
- Sanity check do texto falhou (mudança de layout do PDF).

Nunca invente número.
