# Engagement Bot — Dra. Julga

**Data:** 2026-04-01
**Status:** Aprovado

## Objetivo

Construir um sistema de engajamento automático para o Instagram @dra.julga que responda comentários, reposte stories com menção, aumente engajamento pós-postagem, responda DMs e execute ações de crescimento orgânico de seguidores.

## Escopo

7 funcionalidades independentes:

1. Responder comentários nos posts da Dra. Julga
2. Repostar stories onde @dra.julga for mencionada
3. Postar comentário de votação logo após cada publicação
4. Responder DMs com palavras-chave
5. Comentar em páginas de fofoca/humor (crescimento)
6. Follow/unfollow automático no nicho
7. Hashtag intelligence semanal

## Arquitetura

### Estrutura de arquivos

```
content-engine/
  engagement/
    reply_comments.py       # Responde comentários novos nos posts da Dra. Julga
    repost_stories.py       # Detecta menções em stories e reposta
    post_engagement.py      # Posta comentário de votação após publicação
    reply_dms.py            # Responde DMs com palavras-chave
    comment_growth.py       # Comenta em páginas alvo para crescimento
    follow_unfollow.py      # Follow/unfollow automático no nicho
    hashtag_intel.py        # Analisa performance de hashtags
    shared/
      meta_client.py        # Wrapper Meta Graph API (auth, rate limit, retry)
      claude_client.py      # Wrapper Claude API com prompt base da Dra. Julga
      state.py              # Leitura/escrita atômica do engagement_state.json

.github/workflows/
  engagement.yml            # Orquestra todos os scripts com schedules independentes
```

### Estado persistido

`content-engine/generated/engagement_state.json`:

```json
{
  "comments_replied": ["<comment_id>"],
  "stories_reposted": ["<media_id>"],
  "dms_replied": ["<conversation_id>"],
  "following": {"<user_id>": "<followed_at_iso>"},
  "hashtag_report": {}
}
```

Commitado automaticamente ao final de cada job via `git push` — mesmo padrão dos slides gerados.

## Comportamento de cada script

### `reply_comments.py`
- Busca últimos posts do @dra.julga via `/me/media`
- Para cada post, lista comentários novos não respondidos
- Gera resposta via Claude no tom da Dra. Julga
- Posta como reply no comentário
- Registra IDs respondidos no `engagement_state.json`
- **Limite:** 10 respostas por execução

### `repost_stories.py`
- Consulta `/me/mentioned_media` para menções em stories
- Filtra apenas stories (não feed)
- Reposta via `/me/stories` com `source_media_id` da menção original
- Registra IDs repostados para evitar duplicata
- **Limite:** 5 reposts por execução

### `post_engagement.py`
- Chamado pelo `daily_post.yml` imediatamente após publicação do carrossel
- Recebe `--media_id` do post publicado e `--categoria` como argumentos
- Gera comentário de votação com emojis via Claude baseado na categoria
- Formato: `"Você é culpado? 🔴 SIM / 🟢 NÃO — vota aqui embaixo"`
- Posta como comentário no post recém-publicado

### `reply_dms.py`
- Busca conversas novas na inbox via `/me/conversations`
- Filtra mensagens com palavras-chave: `me julga`, `diagnóstico`, `teste`, `como funciona`, `mejulga`
- Gera resposta personalizada via Claude + link para mejulga.com.br
- Envia resposta via `/me/messages`
- **Limite:** 20 respostas por execução

### `comment_growth.py`
- Evolução do `instagram_comentarios.py` existente, migrado para `engagement/`
- Mesma lógica de rate limiting e cooldown por página
- `PAGINAS_ALVO` populadas com IDs de páginas de fofoca/humor BR
- **Limite:** 3 comentários por sessão, cooldown 24h por página

### `follow_unfollow.py`
- **Fase follow:** busca posts com hashtags do nicho (`#humorbrasileiro`, `#relacionamento`, `#terapia`, `#psicologia`) → segue até 20 contas novas/dia
- **Fase unfollow:** verifica contas seguidas há mais de 7 dias que não seguiram de volta → dessegue até 20/dia
- Estado de follows salvo no `engagement_state.json` com timestamp

### `hashtag_intel.py`
- Busca os últimos 20 posts do @dra.julga via API
- Coleta métricas: `like_count`, `comments_count`, `reach`
- Agrupa por hashtag e calcula score de engajamento médio
- Salva ranking em `generated/hashtag_report.json`
- Geração de relatório apenas — não altera postagens automaticamente

## Módulos compartilhados

### `shared/meta_client.py`
- Retry automático com backoff exponencial (3 tentativas)
- Trata erro `#32` (rate limit): loga e aborta graciosamente
- Trata erro `#10` (permissão negada): loga e aborta
- Trata erro `#200` (permissão não aprovada no App Review): imprime instrução clara
- Todas as chamadas passam por este wrapper

### `shared/claude_client.py`
- System prompt base da Dra. Julga injetado em todas as chamadas
- Evita duplicação de prompt nos scripts individuais
- Modelo: `claude-sonnet-4-6` (mais recente)

### `shared/state.py`
- Leitura e escrita atômica do `engagement_state.json`
- Previne race conditions entre jobs paralelos

## Schedules (GitHub Actions)

| Script | Frequência | Horário BRT |
|---|---|---|
| `reply_comments.py` | A cada 2h | 08h–22h |
| `repost_stories.py` | A cada 4h | 08h–22h |
| `reply_dms.py` | A cada 3h | 08h–22h |
| `comment_growth.py` | 1x/dia | 14h |
| `follow_unfollow.py` | 1x/dia | 10h |
| `hashtag_intel.py` | 1x/semana | Domingo 11h |
| `post_engagement.py` | Após cada publicação | Chamado por `daily_post.yml` |

Cada job é independente no `engagement.yml` — falha em um não afeta os outros.

## Limites anti-ban globais por dia

| Ação | Limite |
|---|---|
| Comentários em posts próprios (replies) | 30 |
| Comentários em páginas externas | 3 |
| Respostas de DM | 40 |
| Follows | 20 |
| Unfollows | 20 |
| Reposts de story | 10 |

## Secrets necessários

Todos já existem no repositório:
- `META_ACCESS_TOKEN`
- `INSTAGRAM_ACCOUNT_ID`
- `ANTHROPIC_API_KEY`

## Permissões Meta API necessárias

| Funcionalidade | Permissão |
|---|---|
| Responder comentários | `instagram_manage_comments` |
| Repostar stories | `instagram_manage_mentions` |
| Responder DMs | `instagram_manage_messages` |
| Follow/unfollow | `instagram_basic` + `instagram_manage_follows` |
| Hashtag intel | `instagram_basic` + `instagram_manage_insights` |

> Verificar no App Review da Meta quais permissões já estão aprovadas antes de ativar cada script.

## Integração com `daily_post.yml`

Adicionar step após `publicar_carrossel`:

```yaml
- name: Postar comentário de engajamento
  run: |
    cd content-engine
    python engagement/post_engagement.py \
      --media_id ${{ steps.publicar.outputs.media_id }} \
      --categoria ${{ steps.categoria.outputs.categoria }}
  env:
    META_ACCESS_TOKEN: ${{ secrets.META_ACCESS_TOKEN }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

O step de publicação precisa exportar o `media_id` via `$GITHUB_OUTPUT`.
