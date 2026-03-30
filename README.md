# mejulga-system

Sistema automatizado de conteúdo, publicação e monetização do [MeJulga](https://mejulga.com.br).

## O que este sistema faz

- Gera 3 posts por dia para o Instagram via IA (Claude API)
- Publica automaticamente nos horários 12h / 18h / 21h (horário de Brasília)
- Direciona tráfego do Instagram para mejulga.com.br
- Registra performance dos posts
- Suporta monetização via Google AdSense e Stripe

## Estrutura

```
mejulga-system/
├── persona/                  # Definição da persona Dra. Julga
│   └── system_prompt.md
├── content-engine/           # Geração de conteúdo com IA
│   ├── templates/            # Templates de post por tipo
│   ├── generated/            # Posts gerados (log diário)
│   ├── generate_posts.py     # Script principal de geração
│   └── scheduler/            # Configuração de agendamento
├── posting-bot/              # Publicação automática Instagram
│   ├── post_to_instagram.py
│   └── README.md
├── funnel/                   # Melhorias no site (funil)
├── payments/
│   └── stripe/               # Integração Stripe
├── seo/                      # SEO + páginas obrigatórias
├── analytics/                # Registro de performance
└── infra/
    └── .github/workflows/    # GitHub Actions (cron jobs)
```

## Stack

| Componente | Tecnologia |
|---|---|
| Geração de conteúdo | Python + Claude API (Anthropic) |
| Agendador | GitHub Actions (cron) |
| Publicação Instagram | Meta Graph API |
| Pagamentos | Stripe |
| Analytics | JSON local + Google Analytics |

## Configuração

Ver documentação em cada subpasta.

## Status

- [x] Arquitetura definida
- [x] Persona criada (Dra. Julga)
- [x] Templates de post criados
- [ ] Content engine (gerador Python)
- [ ] GitHub Actions (scheduler)
- [ ] Meta Graph API (posting bot)
- [ ] Stripe integration
- [ ] SEO pages

---

Desenvolvido por ZK Lab | 2026
