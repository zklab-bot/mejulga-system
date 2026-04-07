# Feedback Loop — Dra. Julga

## Objetivo

Após cada post publicado, enviar uma votação de qualidade via Telegram ao dono. As notas coletadas ajustam automaticamente os pesos do sorteio de variações de veredicto (A/B/C) na próxima geração.

## Contexto

O sistema ainda tem poucos seguidores, então métricas do Instagram (likes, saves) não são confiáveis. A solução é coleta humana: o dono avalia cada post e o sistema aprende com as avaliações.

## Fluxo completo

```
Post publicado (daily_post.yml)
  → feedback.py send_rating_request (novo step no workflow)
      → Telegram: mensagem com 5 botões inline ao TELEGRAM_CHAT_ID
          → Dono toca botão
              → Telegram envia callback_query ao webhook /telegram
                  → telegram_handler.py handle_callback
                      → feedback.py store_rating salva nota no engagement_state.json
                          → na próxima geração, _sorteio_veredicto() lê notas e recalcula pesos
```

## Dados armazenados

Nova chave `"post_details"` no `engagement_state.json`:

```json
"post_details": {
  "2026-04-07_amor": {
    "media_id": "123456789",
    "tipo_veredicto": "A",
    "titulo": "O Ocupado Profissional",
    "crime": "abandono afetivo por excesso de agenda",
    "categoria": "amor",
    "nota": null
  }
}
```

- Chave: `"YYYY-MM-DD_categoria"` (mesma usada em `posts_published`)
- `nota`: `null` até o dono votar, depois `1`–`5`
- Sem limite de entradas (o arquivo já é commitado pelo workflow)

## Mensagem Telegram

```
📊 Novo post publicado!
"O Ocupado Profissional" — amor · Variação A
Crime: abandono afetivo por excesso de agenda

Como foi esse veredicto?
```

Botões inline (uma linha):
`[⭐] [⭐⭐] [⭐⭐⭐] [⭐⭐⭐⭐] [⭐⭐⭐⭐⭐]`

Callback data: `rate:2026-04-07_amor:1` … `rate:2026-04-07_amor:5`

Após o dono tocar um botão, o bot edita a mensagem para:
```
✅ Nota registrada: ⭐⭐⭐⭐ para "O Ocupado Profissional"
```

## Algoritmo de ajuste de pesos

Pesos base: `A=60, B=25, C=15`

### Condição de ativação
Só recalcula quando **cada variação tem ≥ 3 notas**. Antes disso, usa pesos base.

### Cálculo
1. Para cada variação X, calcula `média_X` usando as **últimas 10 notas** de X
2. Calcula `média_global` = média de todas as notas (todas as variações, últimas 10 cada)
3. `peso_raw(X) = max(5, round(peso_base(X) × média_X / média_global))`
4. Normaliza para somar 100: `peso_final(X) = round(peso_raw(X) × 100 / sum(pesos_raw))`
5. Ajuste de arredondamento: adiciona/subtrai 1 da variação com maior peso_raw para garantir soma exata de 100

### Garantias
- Nenhuma variação cai abaixo de 5% — todas continuam aparecendo
- Se dados insuficientes (< 3 notas por variação), volta aos pesos base
- Pesos sempre somam exatamente 100

### Exemplo
Notas: A=[4,5,4], B=[2,2,3], C=[3,3,3]
```
média_A=4.33  média_B=2.33  média_C=3.0  média_global=3.22
peso_raw_A = max(5, round(60 × 4.33/3.22)) = max(5, 81) = 81
peso_raw_B = max(5, round(25 × 2.33/3.22)) = max(5, 18) = 18
peso_raw_C = max(5, round(15 × 3.0/3.22))  = max(5, 14) = 14
soma = 113
peso_final_A = round(81×100/113) = 72
peso_final_B = round(18×100/113) = 16
peso_final_C = round(14×100/113) = 12
```

## Arquivos modificados

### Criar: `content-engine/engagement/feedback.py`

Dois comandos CLI:

```
python -m engagement.feedback send_rating_request \
  --chave 2026-04-07_amor \
  --media_id 123456 \
  --tipo_veredicto A \
  --titulo "O Ocupado Profissional" \
  --crime "abandono afetivo por excesso de agenda" \
  --categoria amor

python -m engagement.feedback store_rating \
  --chave 2026-04-07_amor \
  --nota 4
```

Internamente:
- `send_rating_request`: salva detalhes no state + envia mensagem Telegram com inline keyboard
- `store_rating`: atualiza `nota` no state

### Modificar: `content-engine/engagement/shared/state.py`

Adicionar `"post_details": {}` ao `DEFAULT_STATE`.

### Modificar: `content-engine/webhook/telegram_handler.py`

Adicionar handler de `callback_query` na função `handle()`:

```python
callback = update.get("callback_query", {})
if callback:
    handle_callback(callback)
    return
```

Nova função `handle_callback(callback)`:
- Extrai `data` do callback (formato `rate:chave:nota`)
- Chama `feedback.store_rating(chave, nota)`
- Edita a mensagem original via `answerCallbackQuery` + `editMessageText`

### Modificar: `content-engine/generate_reels.py`

`_sorteio_veredicto()` passa a:
1. Ler `post_details` do state
2. Calcular pesos dinâmicos via `_calcular_pesos_veredicto(post_details)`
3. Usar esses pesos em `random.choices`

Nova função pura `_calcular_pesos_veredicto(post_details: dict) -> list[int]`:
- Retorna `[60, 25, 15]` se dados insuficientes
- Retorna pesos ajustados caso contrário
- Testável sem I/O

### Modificar: `.github/workflows/daily_post.yml`

Novo step após "Registrar post publicado":

```yaml
- name: Enviar votacao no Telegram
  if: steps.dedup.outputs.skip != 'true' && steps.publicar.outputs.media_id != ''
  run: |
    cd content-engine
    HOJE=$(date -u +"%Y-%m-%d")
    CAT="${{ steps.categoria.outputs.categoria }}"
    CHAVE="${HOJE}_${CAT}"
    TIPO=$(CAT="$CAT" python3 -c "import json,glob,os; from datetime import datetime; h=datetime.utcnow().strftime('%Y-%m-%d'); c=os.environ['CAT']; f=glob.glob('generated/reels/'+h+'_'+c+'_reels.json'); print(json.load(open(f[0])).get('tipo_veredicto','A') if f else 'A')")
    TITULO=$(CAT="$CAT" python3 -c "import json,glob,os; from datetime import datetime; h=datetime.utcnow().strftime('%Y-%m-%d'); c=os.environ['CAT']; f=glob.glob('generated/reels/'+h+'_'+c+'_reels.json'); print(json.load(open(f[0])).get('titulo',c) if f else c)")
    CRIME=$(CAT="$CAT" python3 -c "import json,glob,os; from datetime import datetime; h=datetime.utcnow().strftime('%Y-%m-%d'); c=os.environ['CAT']; f=glob.glob('generated/reels/'+h+'_'+c+'_reels.json'); print(json.load(open(f[0])).get('crime','') if f else '')")
    python -m engagement.feedback send_rating_request \
      --chave "$CHAVE" \
      --media_id ${{ steps.publicar.outputs.media_id }} \
      --tipo_veredicto "$TIPO" \
      --titulo "$TITULO" \
      --crime "$CRIME" \
      --categoria "$CAT"
```

## Critérios de sucesso

1. Após post publicado, mensagem chega no Telegram com 5 botões
2. Ao tocar um botão, a mensagem é editada com confirmação e nota salva no state
3. Com ≥ 3 notas por variação, `_sorteio_veredicto()` usa pesos ajustados
4. `_calcular_pesos_veredicto` é testável unitariamente com fixtures de post_details
5. Se Telegram falhar (token ausente, timeout), o workflow não quebra — step é non-fatal
