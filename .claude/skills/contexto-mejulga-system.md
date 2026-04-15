# Contexto — mejulga-system

## O que é
Pipeline automatizado de criação e publicação de conteúdo
para o perfil @dra.julga no Instagram.

## Persona do perfil
Dra. Julga — psicóloga satírica fictícia que comenta
comportamentos humanos com ironia inteligente e acolhimento.
Não é uma psicóloga real. É um personagem.

## Objetivo
Publicar conteúdo diário de forma automatizada:
- 3 posts por dia (08h, 12h, 18h horário Brasília)
- Formato principal: carrossel (slides)
- 7 categorias em rotação diária

## Público-alvo
Brasileiros entre 20–40 anos que:
- Reconhecem seus próprios comportamentos no conteúdo
- Apreciam humor inteligente sem crueldade
- Compartilham posts que "falam sobre elas/eles"

## Plataforma
Instagram — foco em carrosséis e reels.
Meta Graph API para publicação automatizada.

## Stack técnica
- Python (geração de slides e publicação)
- GitHub Actions (agendamento e automação)
- Anthropic API (geração de conteúdo via Claude)
- PIL/Pillow (renderização de slides)
- Meta Graph API + ImgBB (publicação)
- Telegram Bot (notificações e controle manual)

## Repositório
zklab-bot/mejulga-system

## Status
Em desenvolvimento ativo — pipeline de carrossel funcionando,
integração Telegram configurada, HeyGen/vídeo desprioritizado.