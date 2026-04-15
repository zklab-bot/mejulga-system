# Processos — Fluxos de Execução

## Fluxo principal: Geração de carrossel

### Gatilho
GitHub Actions — 3x ao dia (08h, 12h, 18h Brasília)

### Passos
1. Seleciona categoria do dia (rotação de 7)
2. Claude gera roteiro completo (7 slides)
3. render_slides.py renderiza cada slide (PIL)
4. ImgBB hospeda as imagens
5. post_carrossel_instagram.py publica via Meta Graph API
6. Telegram Bot notifica com preview

### Arquivo de roteiro
- Gerado pela Anthropic API
- Formato: JSON com array de slides
- Cada slide: { titulo, corpo, cta (opcional) }

## Fluxo manual via Telegram
1. Envia comando para o bot
2. Bot aceita tema customizado
3. Pipeline roda imediatamente fora do horário padrão
4. Notificação de confirmação

## Fluxo de nova skill
1. Identifica necessidade durante sessão Claude Code
2. Cria arquivo em .claude/skills/
3. Referencia no ORCHESTRATOR.md
4. zklab-os sincroniza automaticamente via webhook

## Manutenção de templates
- Templates Canva: background fixo, não alterar dimensões
- Fonte Open Sans: obrigatória para consistência visual
- Cores: definidas no render_slides.py, alterar só lá

## Troubleshooting comum
| Problema | Causa provável | Solução |
|----------|---------------|---------|
| Slide não renderiza | Fonte não encontrada | Verificar path Open Sans |
| Post falha | Token Meta expirado | Renovar META_ACCESS_TOKEN |
| Actions não dispara | Cron mal formatado | Verificar timezone Brasília |
| ImgBB falha | Limite de upload | Verificar IMGBB_API_KEY |