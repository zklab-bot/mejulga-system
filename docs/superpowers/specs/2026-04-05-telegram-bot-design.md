# Telegram Bot — Canal de Comando e Relatórios

## Objetivo
Canal bidirecional via Telegram para monitorar e controlar o bot da Dra. Julga.
Notificações automáticas em tempo real + 10 comandos para operar o sistema remotamente.

## Arquitetura

```
GitHub Actions ──► notify.py ──────────────────► Telegram (dono)
                                                       │
                                           dono envia /forcar_post amor
                                                       │
                                        Telegram ──► Railway FastAPI
                                                       │
                                          /telegram endpoint (novo)
                                                       │
                                       telegram_handler.py processa
                                                       │
                             ┌─────────────────────────┤
                             │                         │
                        lê/escreve               GitHub API
                   engagement_state.json      (workflow_dispatch)
```

**Fluxo de notificação (GitHub Actions → você):**
1. Step do workflow chama `notify.py`
2. `notify.py` faz POST para `api.telegram.org/bot{TOKEN}/sendMessage`
3. Mensagem chega no seu Telegram

**Fluxo de comando (você → Railway):**
1. Você envia `/comando` no Telegram
2. Telegram faz POST para `https://mejulga.railway.app/telegram`
3. `telegram_handler.py` valida chat_id (só responde ao dono)
4. Processa comando: lê `engagement_state.json` ou chama GitHub API
5. Responde via Telegram API

## Componentes

### 1. `content-engine/notify.py`
Módulo standalone chamado dos GitHub Actions. Sem servidor.

Funções:
- `send(text)` — envia mensagem genérica
- `send_post_published(categoria, titulo, hora, media_id)` — post publicado
- `send_post_failed(categoria, hora, erro)` — post falhou
- `send_post_skipped(categoria)` — dedup ativado
- `send_voting_comment(media_id)` — comentário de votação postado
- `send_daily_report(state)` — relatório das 22h

### 2. `content-engine/webhook/telegram_handler.py`
Processa comandos recebidos. Chamado pelo endpoint do servidor.

Comandos:
| Comando | Implementação |
|---|---|
| `/help` | Retorna texto estático com todos os comandos |
| `/status` | Lê `engagement_state.json` + calcula próximo cron |
| `/relatorio` | Lê histórico de `posts_published` dos últimos 7 dias |
| `/forcar_post [cat]` | Chama GitHub API → `workflow_dispatch` no `daily_post.yml` |
| `/proximos` | Calcula próximos horários do dia baseado nos crons definidos |
| `/ultimo` | Último item de `posts_published` no state |
| `/pausar` | GitHub API → desativa `daily_post.yml` |
| `/retomar` | GitHub API → reativa `daily_post.yml` |
| `/preview [cat]` | GitHub API → `workflow_dispatch` com flag `--sem_audio --preview` |
| `/erros` | Lê lista `errors` do `engagement_state.json` |

### 3. `content-engine/webhook/server.py` (extensão)
Adiciona endpoint:
```
POST /telegram
```
- Valida `X-Telegram-Bot-Api-Secret-Token` header
- Verifica `chat_id == TELEGRAM_CHAT_ID` (só o dono)
- Chama `telegram_handler.handle(update)`
- Retorna `{"ok": true}`

### 4. `.github/workflows/daily_post.yml` (extensão)
Adiciona steps de notificação após cada evento:
- Após publicar: `python -m notify send_post_published ...`
- Após falhar: `python -m notify send_post_failed ...`
- Após dedup: `python -m notify send_post_skipped ...`
- Após comentário: `python -m notify send_voting_comment ...`

### 5. `.github/workflows/daily_report.yml` (novo)
Cron: `0 1 * * *` (22h BRT)
Gera e envia relatório diário consolidado via `notify.send_daily_report`.

## Notificações automáticas

| Evento | Formato da mensagem |
|---|---|
| Post publicado | `✅ *O Fantasma do Grupo* postado!\n📂 social • 🕘 09h04` |
| Post falhou | `❌ Falha ao postar\n📂 trabalho • 🕛 12h01\n⚠️ [motivo do erro]` |
| Post pulado | `⏭️ Post pulado — social já publicado hoje` |
| Votação postada | `💬 Votação postada em [media_id]` |
| Relatório diário | Resumo estruturado (ver abaixo) |

**Formato do relatório diário:**
```
📊 RELATÓRIO — 05/04/2026

📸 Posts publicados: 4/5
  ✅ 09h04 — social (O Fantasma do Grupo)
  ✅ 12h03 — trabalho (O Ocupado Profissional)
  ✅ 18h01 — dopamina (Viciado em Notificação)
  ✅ 20h02 — vida_adulta (A Geladeira Vazia)
  ❌ 22h00 — dinheiro (falhou — erro API)

💬 Comentários respondidos: 7
🌱 Comentários de crescimento: 3
👥 Follows realizados: 12

⚠️ Erros: 1
  • 22h00 — post_carrossel: [motivo]
```

## Segurança
- Endpoint `/telegram` valida `X-Telegram-Bot-Api-Secret-Token` (definido no setWebhook)
- Todos os comandos verificam `chat_id == TELEGRAM_CHAT_ID` — mensagens de outros usuários são ignoradas silenciosamente
- Token e chat_id como secrets (nunca em código)

## Variáveis de ambiente necessárias

| Variável | Onde usar | Para quê |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | GitHub Actions + Railway | Enviar e receber mensagens |
| `TELEGRAM_CHAT_ID` | GitHub Actions + Railway | Identificar o dono |
| `TELEGRAM_SECRET` | Railway | Validar webhook do Telegram |
| `GITHUB_PAT` | Railway | Acionar workflows via API |

## Rastreamento de erros
Adicionar lista `errors` ao `engagement_state.json`:
```json
"errors": [
  {
    "timestamp": "2026-04-05T22:00:00",
    "context": "post_carrossel",
    "message": "403 Forbidden"
  }
]
```
Mantém os últimos 20 erros. Usado pelo `/erros` e pelo relatório diário.

## Guia de setup manual

### Passo 1 — Criar o bot no Telegram
1. Abra o Telegram e procure **@BotFather**
2. Envie `/newbot`
3. Escolha um nome: `Dra. Julga Monitor`
4. Escolha um username: `drajulga_monitor_bot` (ou similar)
5. Guarde o token: `123456:ABCdef...`

### Passo 2 — Descobrir seu Chat ID
1. Inicie uma conversa com o bot que você criou (envie qualquer mensagem)
2. Acesse: `https://api.telegram.org/bot{SEU_TOKEN}/getUpdates`
3. Copie o valor de `result[0].message.chat.id` — esse é seu `TELEGRAM_CHAT_ID`

### Passo 3 — Adicionar secrets no GitHub
No repositório → Settings → Secrets → Actions → New secret:
- `TELEGRAM_BOT_TOKEN` = token do BotFather
- `TELEGRAM_CHAT_ID` = seu chat ID

### Passo 4 — Adicionar variáveis no Railway
No painel Railway → seu serviço → Variables:
- `TELEGRAM_BOT_TOKEN` = mesmo token
- `TELEGRAM_CHAT_ID` = mesmo chat ID
- `TELEGRAM_SECRET` = qualquer string aleatória (ex: `julga_secret_2026`)
- `GITHUB_PAT` = Personal Access Token do GitHub (ver passo 5)

### Passo 5 — Criar GitHub PAT
1. GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Nome: `mejulga-telegram-bot`
3. Repositório: apenas `mejulga-system`
4. Permissões: `Actions: Read and Write`
5. Gerar e copiar — adicionar como `GITHUB_PAT` no Railway

### Passo 6 — Registrar webhook do Telegram (após deploy)
Após o Railway fazer o deploy com as novas variáveis, execute uma vez:
```
https://api.telegram.org/bot{TOKEN}/setWebhook
  ?url=https://mejulga-system-production.up.railway.app/telegram
  &secret_token={TELEGRAM_SECRET}
```
Abra essa URL no navegador. Deve retornar `{"ok":true}`.

## Arquivos modificados/criados
- **Criar:** `content-engine/notify.py`
- **Criar:** `content-engine/webhook/telegram_handler.py`
- **Modificar:** `content-engine/webhook/server.py`
- **Modificar:** `.github/workflows/daily_post.yml`
- **Criar:** `.github/workflows/daily_report.yml`
- **Modificar:** `content-engine/engagement/shared/state.py` (adicionar suporte a `errors`)
