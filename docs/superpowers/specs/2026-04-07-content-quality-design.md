# Qualidade de Conteúdo — Dra. Julga

## Objetivo

Reescrever o sistema de geração de carrosseis para eliminar repetição de texto, estabelecer progressão narrativa real entre cenas, e substituir o "diagnóstico clínico" por um **veredicto jurídico** com estrutura fixa — alinhando o conteúdo com a identidade da marca "Dra. Julga" (juíza, não psicóloga).

## Contexto e diagnóstico do problema

### Bug de identidade raiz
O `SYSTEM_PROMPT` atual descreve a personagem como *"psicóloga fictícia sarcástica que diagnostica"*. O nome "Julga" vem do verbo **julgar**. A personagem é uma juíza — ela condena, não diagnostica. Essa contradição faz o modelo oscilar entre três vozes distintas:

- **Voz A — Juíza-observadora** (`trabalho`): fria, forense. É a voz correta.
- **Voz B — Comentarista de meme** (`dopamina`, `dinheiro-pizza`): "Gente, ele parcelou a pizza". Quebra o arquétipo.
- **Voz C — Amiga sarcástica** (`amor`, `dinheiro 30/03`): genérica, poderia ser qualquer conta de humor.

### Falhas estruturais identificadas

**1. `texto_slide` = resumo do `texto`**
O prompt atual pede que o slide seja "autossuficiente" mas não proíbe que seja uma versão abreviada do texto narrado. Resultado: slides sem valor próprio.

Exemplo real (`trabalho`, cena 2):
- `texto`: "Mas eu te observei. Quarta-feira, 14h37. Reunião do Teams. Câmera desligada."
- `texto_slide`: "Quarta, 14h37. Reunião do Teams.\nCâmera desligada."

**2. Escalada narrativa quebrada**
Cenas 3 e 4 frequentemente estão fora de ordem de impacto — o detalhe da cena 3 é mais engraçado que o agravante da cena 4, invertendo a curva de tensão.

**3. Diagnóstico no registro errado**
Os diagnósticos atuais são jargões médicos polissilábicos ("síndrome da produtividade performática com procrastinação corporativa crônica") que:
- Contradizem o nome da marca
- São longos demais para entrega oral em 4 segundos
- São genéricos demais para virar print
- Não têm stakes (diagnóstico = coitadinho; veredicto = culpado)

**4. Abertura quebrando personagem**
Posts com "Gente, vocês checam o celular?" ou "Gente, ele parcelou a pizza" transformam a juíza em influencer.

## Arquitetura da solução

### Abordagem: few-shot com exemplos positivo e negativo

Incluir dois exemplos completos no user prompt — um ideal e um anti-exemplo explícito. O modelo aprende o padrão por demonstração, eliminando ambiguidade das regras textuais.

### Arquivo modificado
- `content-engine/generate_reels.py` — único arquivo alterado

## Design detalhado

### 1. Nova identidade no SYSTEM_PROMPT

**Remover:**
- "psicóloga fictícia sarcástica que diagnostica"
- Todo o bloco "DIAGNÓSTICO CLÍNICO ABSURDO — fórmula obrigatória"
- Exemplos de diagnóstico médico ("dopaminergência digital com recaída noturna compulsiva")

**Substituir por:**
```
Você é a Dra. Julga — juíza fictícia que conduz processos contra comportamentos absurdos
do cotidiano brasileiro. Observa, coleta provas e profere veredictos. Voz: fria, forense,
levemente entediada de já ter visto tudo. Nunca cruel.

TOM PROIBIDO:
- Nunca começar com "Gente,"
- Nunca usar jargão médico: "síndrome", "diagnóstico", "CID", "transtorno"
- Nunca falar como amiga de grupo

VOCABULÁRIO JURÍDICO (usar com parcimônia):
réu/ré, autos, prova, agravante, atenuante negado, reincidência, pena, sentença,
culpado, trânsito em julgado, sem apelação

REGRA DA ESPECIFICIDADE:
Toda cena precisa de pelo menos UM número, horário, marca, ou dado concreto.
Generalização é proibida. ❌ "fica muito no celular" ✅ "23h47. Décimo quarto vídeo."

REGRA DA ESCALADA:
Cena 3 > Cena 2 em especificidade. Cena 4 deve contradizer a desculpa implícita de Cena 2.
Cena 5 deve ser mais curta que Cena 4.

REGRA ANTI-REDUNDÂNCIA (texto vs texto_slide):
texto_slide não é resumo do texto — é um ângulo diferente do mesmo momento.
Enquanto o texto narra, o slide acusa com os substantivos-prova.
❌ Errado: texto "Quarta, 14h37, câmera desligada" → slide "14h37\nCâmera desligada"
✅ Correto: texto "Mas eu te observei. Quarta-feira, 14h37. Reunião do Teams. Câmera desligada."
            slide "Quarta, 14h37.\nProva nos autos."

REGRA DO PRINTÁVEL:
O VEREDICTO (cena 5) deve ter no máximo 20 palavras no `texto` (inclui "VEREDICTO:" e
o fechamento). O campo `frase_printavel` extrai somente o crime em ≤14 palavras.
```

### 2. Nova estrutura das 6 cenas

| Cena | Nome | Papel | Restrições |
|------|------|-------|-----------|
| 1 | Abertura do processo | Flagrante ou acusação direta — sem introdução | Nunca "Gente,"; começa com dado concreto ou "Processo X" |
| 2 | Intimação | Descrição fria da conduta com número/horário | Pelo menos 1 dado específico |
| 3 | Primeira prova | Detalhe absurdo mais específico que cena 2 | Sem conectores no início do slide ("Aí", "Mas") |
| 4 | Agravante | Prova que contradiz a desculpa implícita da cena 2 | Começa com "Agravante:" ou "Pior:" no `texto` |
| 5 | VEREDICTO | Estrutura fixa, ≤14 palavras, printável | Ver variações abaixo |
| 6 | CTA | Fixo | "Veja seu processo em mejulga.com.br" |

### 3. Três variações de veredicto em rotação

O `tipo_veredicto` é passado como parâmetro (gerado aleatoriamente pela função antes de chamar o Claude).

**Variação A — Sentença curta** (60% dos posts)
```
texto:       "VEREDICTO: Culpado por [crime específico]. [Atenuante negado / Reincidente]. Sem apelação."
texto_slide: "VEREDICTO\nCulpado por [crime em 4-6 palavras].\nSem apelação."
```
Exemplo: `Culpado por simulação laboral em ambiente remoto. Reincidente. Sem apelação.`

**Variação B — Pena absurda** (25% dos posts)
```
texto:       "VEREDICTO: Condenado a [pena criativa e específica]. Pena suspensa se [condição impossível]. Improvável."
texto_slide: "VEREDICTO\nCondenado a [pena em 4-5 palavras].\nImprovável."
```
Exemplo: `Condenado a pagar em dinheiro pelos próximos 90 dias. Pena suspensa se resistir à promoção. Improvável.`

**Variação C — Autos do processo** (15% dos posts — posts âncora/semanais)
```
texto:       "Processo [numero_processo]. Réu: você. Crime: [crime]. Provas: [2 itens das cenas]. Decisão: CULPADO."
texto_slide: "Processo [numero_processo]\nCrime: [crime]\nDecisão: CULPADO."
```
Exemplo: `Processo AMO-003/26. Réu: você. Crime: ghosting sazonal com dolo comprovado. Provas: 3 meses de silêncio, volta fingindo saudade. Decisão: CULPADO.`

### 4. Novos campos no JSON de saída

**Adicionados:**
- `numero_processo`: string no formato `"[CAT3]-[NNN]/[AA]"` (ex: `"TRA-007/26"`) — NNN é calculado contando os JSONs existentes da categoria na pasta `generated/reels/`
- `crime`: string curta — nome do crime para print, ex: `"ghosting sazonal com dolo comprovado"`
- `tipo_veredicto`: `"A"`, `"B"` ou `"C"`
- `frase_printavel`: a one-liner do veredicto, ≤14 palavras

**Removido:**
- `conclusao`: redundante — conteúdo vive em cena 5 + `frase_printavel`

**Mantidos:** `categoria`, `titulo`, `cenas`, `texto_completo`, `legenda_instagram`, `sugestao_musica`

### 5. Validação programática pós-geração

Após receber o JSON do Claude, antes de salvar:

1. **Anti-redundância**: para cada cena, se `normalizar(texto_slide) == normalizar(texto)` → rejeitar e regenerar (máx 2 tentativas)
2. **Anti-gente**: se qualquer cena começa com "Gente," → rejeitar e regenerar
3. **Anti-diagnóstico**: se "diagnóstico" ou "síndrome" aparece em qualquer cena → rejeitar e regenerar
4. **Veredicto conciso**: se cena 5 tem >20 palavras no `texto` → rejeitar e regenerar
5. Regeneração passa a razão da rejeição no prompt para o Claude corrigir

### 6. Função `gerar_roteiro` — parâmetro adicional

```python
def gerar_roteiro(categoria: str, tipo_veredicto: str = None) -> dict:
    if tipo_veredicto is None:
        tipo_veredicto = random.choices(["A", "B", "C"], weights=[60, 25, 15])[0]
```

O `tipo_veredicto` é incluído no user prompt com a instrução de qual estrutura usar.

### 7. Few-shot examples no user prompt

**Exemplo positivo** (baseado em `trabalho` — melhor post atual):
- Demonstra: abertura com flagrante temporal, escalada cena 2→3→4, veredicto curto, slides com ângulo diferente do texto

**Anti-exemplo** (baseado em `dinheiro-pizza`):
- Demonstra explicitamente o que NÃO fazer: abertura "Gente,", cenas 1/2 redundantes, slide = resumo do texto

## Arquivos modificados

- **Modificar:** `content-engine/generate_reels.py`
  - `SYSTEM_PROMPT`: reescrita completa
  - `gerar_roteiro()`: adiciona parâmetro `tipo_veredicto`, few-shot examples, validação pós-geração
  - `salvar_roteiro()`: ajusta para novos campos, remove `conclusao`

## Critérios de sucesso

1. Nenhum post gerado contém "diagnóstico", "síndrome", ou "Gente," em qualquer cena
2. `texto_slide` e `texto` são semanticamente distintos em todas as cenas
3. O VEREDICTO tem ≤14 palavras e segue a estrutura da variação sorteada
4. As cenas 2→3→4 têm progressão de especificidade/impacto crescente
5. `frase_printavel` é autossuficiente e shareável fora de contexto
