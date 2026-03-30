# 📝 Templates de Post — Dra. Julga

Cada template tem variáveis entre `{{}}` que o gerador de conteúdo (IA) preenche automaticamente.

---

## TIPO 1 — Provocação / Pergunta

**Objetivo:** Máximo engajamento (comentários, compartilhamentos)  
**Horário:** 12h (almoço — pico de uso)

### Template 1A — Comportamento identificável
```
A Dra. Julga recebeu um novo caso hoje.

{{SITUACAO_ABSURDA_IDENTIFICAVEL}}

O diagnóstico? {{DIAGNOSTICO_IRONICO}}.

Você conhece alguém assim? 
(Não precisa falar que é você.) 🧠

{{HASHTAGS_GRUPO_A}} {{HASHTAGS_GRUPO_B}}
```

### Template 1B — Pergunta direta
```
Pergunta séria da Dra. Julga:

{{PERGUNTA_PROVOCADORA}}

Responde nos comentários — sem julgamento.
(Tá mentindo. Vai ter julgamento. É o que eu faço.) ⚖️

{{HASHTAGS_GRUPO_A}} {{HASHTAGS_GRUPO_B}}
```

### Template 1C — Estatística fictícia cômica
```
Dado novo da Dra. Julga:

{{PORCENTAGEM}}% das pessoas {{COMPORTAMENTO_IDENTIFICAVEL}}.

Os outros {{RESTO}}% estão mentindo.

Você é qual? 🫠

{{HASHTAGS_GRUPO_B}} {{HASHTAGS_GRUPO_C}}
```

---

## TIPO 2 — Julgamento Exemplo (Caso Clínico)

**Objetivo:** Mostrar o produto em ação, gerar curiosidade pelo site  
**Horário:** 18h (fim de expediente — segundo pico)

### Template 2A — Caso clínico formal
```
CASO CLÍNICO Nº {{NUMERO}}

Paciente, {{IDADE}} anos.
{{LISTA_COMPORTAMENTOS_DO_PACIENTE}}

Diagnóstico da Dra. Julga:
{{DIAGNOSTICO_SERIO_MAS_IRONICO}}

⚖️ Quer saber o que a Dra. Julga falaria sobre a SUA vida?
Link na bio. Se tiver coragem.

{{HASHTAGS_GRUPO_A}} {{HASHTAGS_GRUPO_C}}
```

### Template 2B — Veredicto rápido
```
VEREDICTO DA DRA. JULGA:

{{COMPORTAMENTO_EM_UMA_LINHA}}

👩‍⚖️ Culpado(a).

Atenuante? {{ATENUANTE_ENGRAÇADO}}.

Quer o seu? mejulga.com.br 🧠

{{HASHTAGS_GRUPO_A}} {{HASHTAGS_GRUPO_C}}
```

### Template 2C — Categoria do site
```
A Dra. Julga está analisando casos da área: {{CATEGORIA}} hoje.

{{DESCRICAO_SATIRICA_DA_CATEGORIA}}

Resultado de hoje: {{VEREDICTO_DA_CATEGORIA}}

E o seu resultado? 
mejulga.com.br — link na bio ⚖️

{{HASHTAGS_GRUPO_B}} {{HASHTAGS_GRUPO_C}}
```

---

## TIPO 3 — CTA para o Site

**Objetivo:** Conversão direta para mejulga.com.br  
**Horário:** 21h (maior tempo livre — terceiro pico)

### Template 3A — Teaser de categoria
```
{{SITUACAO_DO_DIA_A_DIA}}

Isso diz muito sobre você.

A Dra. Julga tem um diagnóstico completo esperando.

É de graça. É preciso. É constrangedor.

mejulga.com.br — link na bio 🧠

{{HASHTAGS_GRUPO_A}} {{HASHTAGS_GRUPO_C}}
```

### Template 3B — Chamada de ação direta
```
Se você:
{{ITEM_1}}
{{ITEM_2}}
{{ITEM_3}}

A Dra. Julga tem algo importante pra te dizer.

Não vai doer. Muito.

mejulga.com.br 🫠

{{HASHTAGS_GRUPO_B}} {{HASHTAGS_GRUPO_C}}
```

### Template 3C — Resultado compartilhável
```
Alguém fez o teste de {{CATEGORIA}} no MeJulga hoje.

O resultado foi: "{{RESULTADO_EXEMPLO}}"

👀 Curioso pra saber o seu?

mejulga.com.br — link na bio ⚖️

{{HASHTAGS_GRUPO_A}} {{HASHTAGS_GRUPO_C}}
```

---

## Categorias do Site (para referência nos posts)

| Emoji | Categoria | Tom sugerido no post |
|---|---|---|
| 💸 | Dinheiro | Culpa financeira, gastos impulsivos |
| 💔 | Amor | Relacionamentos, ghosting, red flags |
| 💼 | Trabalho | Procrastinação, reuniões, segunda-feira |
| 📱 | Dopamina | Vício em celular, TikTok, scroll infinito |
| 🧠 | Vida Adulta | Pagar conta, cozinhar, responsabilidades |
| 🧍 | Social | Cancelar planos, ansiedade social |
| 🧘 | Saúde Mental | Autossabotagem, procrastinação emocional |

---

## Hashtags — Pool Completo

```python
HASHTAGS = {
    "grupo_a": [
        "#MeJulga", "#DraJulga", "#PsicologiaReal", 
        "#VidaAdulta", "#Identificação"
    ],
    "grupo_b": [
        "#HumorBrasileiro", "#Viral", "#RelacionavelDemais", 
        "#Brasileirices", "#Cotidiano"
    ],
    "grupo_c": [
        "#Autoconhecimento", "#Psicologia", "#QuizOnline", 
        "#JulgamentoGratuito", "#MeJulgaCom"
    ],
    "por_categoria": {
        "dinheiro": ["#FinançasPessoais", "#Gastei", "#Pobrice"],
        "amor": ["#RelacionamentoTóxico", "#Crush", "#GhostingNãoÉCerto"],
        "trabalho": ["#HomeOffice", "#Procrastinação", "#SegundaFeira"],
        "dopamina": ["#VicioemCelular", "#TempoDeAntenna", "#ScrollInfinito"],
        "vida_adulta": ["#AdultingIsHard", "#VidaDeAdulto", "#NinguémMePreparou"],
        "social": ["#AnguloSocial", "#CancelarPlanos", "#Introvertido"],
        "saude_mental": ["#SaúdeMental", "#AutoCuidado", "#Terapia"]
    }
}
```

---

*Versão: 1.0 — Março 2026*
