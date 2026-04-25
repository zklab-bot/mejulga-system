# Skill 05 — Estrutura de Slides

## REGRA CRÍTICA — Hook dos slides 1 e 2

O slide 1 é o único motivo pelo qual alguém continua o carrossel.
Se não parar o scroll em 2 segundos, o caso foi arquivado.

**Slide 1 (cena 1) — Hook Principal:**
- Máximo 10 palavras no texto_slide
- Formato obrigatório: observação provocativa, sem contexto, sem resolução
- Proibido: mencionar processo, nome do crime, "Dra. Julga"
- Tom: flagrante. O leitor se reconhece imediatamente.
- Exemplos bons:
  - "Você mandou áudio de 3 min. Recebeu: 'rsrs'."
  - "Há quanto tempo você lê mensagem normal como ameaça?"
  - "Ela disse que estava bem. Você interrogou por 40 minutos."
- Exemplos ruins (proibidos):
  - "Processo AMO-003/26 em andamento." ← é metadado, não hook
  - "A Dra. Julga registrou o caso." ← não gera tensão
  - Qualquer frase que explique o que vai acontecer

**Slide 2 (cena 2) — Hook Secundário:**
- Aprofunda a ferida aberta no slide 1
- Nunca resolve, nunca explica
- Deve fazer o leitor pensar "isso é sobre mim"
- Máximo 12 palavras
- Tom: diagnóstico frio, sem julgamento explícito
- Exemplos bons:
  - "Sentir conexão e ter conexão não são a mesma coisa."
  - "Você não leu a mensagem errado. Você leu o que queria."
  - "Isso tem um nome. E você já sabe qual é."

---

Todo carrossel tem exatamente 7 slides. Cada slide tem uma função única.
Nunca comprimir duas funções em um slide. Nunca pular um slide.

---

## Slide 1 — Hook Principal (Capa)

**Função:** Parar o scroll E criar razão para swipe.
**Regra:** Máx. 12 palavras. Cria tensão aberta que só se resolve no Slide 6.
**Proibido:** Revelar o veredicto. Explicar o crime completamente. Fechar o loop.
**Referência:** Usar um template dos Grupos V, L ou C das Regras de Hook.

## Regra do Slide Visual

`texto` = narração falada (pode ser longa, fluida, conversacional).
`texto_slide` = versão visual para o card — condensada, sem conectivos, quebrável em linhas.

**Para narações curtas (≤ 7 palavras):** o slide PODE ser idêntico — a frase já é visual.
**Para narações longas (> 7 palavras):** o slide DEVE condensar. Nunca copiar.

❌ texto: "No fim do dia, você agenda uma reunião para discutir o que ficou pendente."
❌ slide: "No fim do dia, você agenda uma reunião para discutir o que ficou pendente."

✅ texto: "No fim do dia, você agenda uma reunião para discutir o que ficou pendente."
✅ slide: "Pendências do dia:\nagendou uma reunião\npara discuti-las."

---

## Slide 2 — Hook Secundário

**Função:** Aprofundar a tensão aberta no Slide 1. Não resolvê-la.
**Regra:** Adiciona uma camada ao crime. Revela um detalhe que piora a situação.
**Proibido:** Resolver a tensão do Slide 1. Apresentar o veredicto.
**Tom:** Mesmo tom clínico do Slide 1, mais específico.

## Slide 3 — Prova 1

**Função:** Primeira prova concreta e observável do crime.
**Regra:** Comportamento específico, reconhecível, sem julgamento.
**Label:** "REGISTRO DE OCORRÊNCIA Nº 1" ou "A ACUSAÇÃO"

## Slide 4 — Prova 2

**Função:** Segunda prova. Deve ser diferente da primeira em tipo ou contexto.
**Regra:** Aumenta a gravidade progressivamente.
**Label:** "REGISTRO DE OCORRÊNCIA Nº 2" ou "A PROVA"

## Slide 5 — Prova 3 (Agravante)

**Função:** Terceira prova — a mais devastadora. O momento de maior reconhecimento.
**Regra:** Deve ser a prova mais específica e reconhecível das três.
**Label:** "REGISTRO DE OCORRÊNCIA Nº 3" ou "O AGRAVANTE"

## Slide 6 — Veredicto

**Função:** Uma linha. Sem explicação. Sem piedade.
**Regra:** Máx. 8 palavras. Tipo A, B ou C conforme Código de Julgamento.
**Formato:** "VEREDICTO\n[texto]\nSem apelação." ou "VEREDICTO\n[texto]\nReincidente."

## Slide 7 — CTA

**Função:** Direcionar para mejulga.com.br
**Regra:** Uma frase curta da Dra. Julga + URL.
**Formato fixo:** "Veja seu processo.\nmejulga.com.br"

---

## REGRA DE QUANTIDADE

O roteiro DEVE ter exatamente 5 cenas válidas de conteúdo
(cenas 1–5), mais opcionalmente a cena de CTA (cena 6).

- Cenas 1–5: conteúdo narrativo (hook, prova, agravante, etc.)
- Cena de veredicto narrativo NÃO deve ser incluída como cena numerada
- O veredicto vai APENAS no campo frase_printavel do JSON raiz
- Nunca gere texto com "VEREDICTO" no campo texto_slide de nenhuma cena

Se o roteiro tiver menos de 5 cenas de conteúdo, expanda:
- Adicione mais uma prova específica
- Ou adicione um contexto agravante extra
- Nunca deixe menos de 5 cenas válidas
