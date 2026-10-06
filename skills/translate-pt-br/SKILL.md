---
name: translate-pt-br
description: Translate text, docs, UI strings or code comments into natural Brazilian Portuguese (pt-BR), avoiding European Portuguese, calques and gerundismo. Use whenever the user asks to translate something to Portuguese, pt-BR, or "português".
---

# Translate to Brazilian Portuguese (pt-BR)

Goal: output that reads as if a skilled Brazilian writer wrote it originally — not a translation. Meaning first, then naturalness, then literal fidelity.

## 1. Before translating

- Identify the **text type** (UI copy, marketing, technical doc, legal/formal, casual message, code) and the **audience** (devs, general public, patients, executives). This decides register and how many English terms stay.
- If the user gave a **glossary** or style guide, it overrides everything below. Keep every term consistent across the whole text.
- If register is genuinely unclear and the text is long, ask once. For short text, pick the natural default and proceed.

## 2. Register defaults

- Address the reader as **você** (never *tu* conjugations, never *vós*). Formal/legal/medical-administrative: *o senhor / a senhora* or impersonal constructions only if the source is clearly formal.
- Casual/UI/marketing: próclise is natural ("Me avise", "Se cadastre" is acceptable in casual; prefer "Cadastre-se" in UI buttons and formal text).
- Keep sentences shorter than the English when English stacks clauses; Portuguese gets heavy fast.

## 3. Never use European Portuguese forms

| pt-PT (wrong here) | pt-BR |
|---|---|
| ficheiro | arquivo |
| ecrã | tela |
| utilizador | usuário |
| telemóvel | celular |
| rato | mouse |
| partilhar | compartilhar |
| equipa | equipe |
| registo | registro |
| facto, contacto, receção | fato, contato, recepção |
| estar a fazer | estar fazendo |
| guardar (save, in UI) | salvar |
| pequeno-almoço, autocarro, comboio | café da manhã, ônibus, trem |

Use Brazilian accentuation: ônibus, econômico, gênero, Antônio (not ó/é forms of pt-PT where they differ).

## 4. False friends and calques to avoid

- actually → *na verdade* (not "atualmente")
- eventually → *no fim, com o tempo* (not "eventualmente" = occasionally)
- realize → *perceber, se dar conta* (not "realizar")
- assume → *supor, presumir, partir do princípio* (not "assumir" unless = take on)
- pretend → *fingir*; intend → *pretender*
- support (software) → *oferecer suporte a, ser compatível com, aceitar* ("suporta" is tolerated in dev text, avoid elsewhere)
- apply (for a job) → *se candidatar*
- at the end of the day → *no fim das contas*
- make sense → *fazer sentido* is fine; "make a decision" → *tomar uma decisão*
- "o mesmo" as a pronoun ("verifique o mesmo") → use *ele/ela/isso* or restructure
- Excess possessives: "levantou sua mão" → "levantou a mão"
- Excess passive voice: prefer active or *-se* constructions
- **Gerundismo** is banned: "vou estar enviando" → "vou enviar" / "envio"

## 5. Technical and UI text

- Do **not** translate: code, identifiers, CLI commands, file paths, API names, placeholders (`{name}`, `%s`, `{{count}}`), ICU syntax keywords, HTML/Markdown tags, URLs. Translate only human-readable strings around them.
- Keep established English loanwords devs actually use: deploy, commit, pull request, branch, merge, bug, backend, frontend, framework, token, cache, log, endpoint, feature flag. Inflect naturally ("fazer o deploy", "o commit").
- Translate general UI vocabulary the Brazilian way: Save → Salvar · Cancel → Cancelar · Delete → Excluir · Settings → Configurações · Sign in → Entrar · Sign up → Cadastrar-se / Criar conta · Log out → Sair · Search → Pesquisar/Buscar · Upload → Enviar · Download → Baixar · Dashboard → Painel.
- Buttons: infinitive or imperative consistently (pick one per product; infinitive is most common: "Salvar alterações").
- Plurals in ICU/i18n: pt-BR uses `one` and `other` (0 falls under `one` in pt by CLDR — respect the existing file's rules, don't invent categories).
- Watch string length: pt-BR runs ~20–30% longer than English. If a UI string has an obvious length budget, pick the shorter natural option.
- Code comments: translate only if asked.

## 6. Formatting conventions

- Numbers: `1.234,56` (dot thousands, comma decimal).
- Currency: `R$ 1.234,56` (space after R$). Don't convert currencies unless asked; keep `US$ 50` for dollars.
- Dates: `06/10/2026` (DD/MM/AAAA); long form `6 de outubro de 2026`. Months and weekdays lowercase.
- Time: 24h, `14h30` in prose, `14:30` in UI/data.
- Units: metric; convert imperial only when the text is consumer-facing and conversion is unambiguous (keep original in parentheses if precision matters).
- Titles and headings: **sentence case** ("Como configurar o servidor"), not English Title Case.
- Quotation marks: “aspas curvas” in prose; straight quotes inside code.
- Gender agreement: resolve from context; for unknown-gender placeholders, restructure to avoid agreement ("Boas-vindas, {name}" instead of "Bem-vindo(a)") unless the product already uses another convention.

## 7. Idioms, humor, cultural references

- Replace idioms with the Brazilian equivalent, not a literal rendering ("piece of cake" → "moleza" / "fácil demais").
- Keep brand names, product names and proper nouns as-is.
- US-specific references (ZIP code, SSN, Thanksgiving): adapt only for localization tasks (CEP, CPF); for plain translation keep them and don't explain unless asked.

## 8. Output

- Return **only the translation**, in the same structure/format as the source (Markdown, JSON, YAML, subtitles keep their timing lines, etc.).
- For JSON/YAML/i18n files: translate values only, never keys; preserve ordering, escaping and trailing structure exactly.
- After the translation, add a short **Notas** section only when there was a real decision the user should know about (ambiguous term, a choice between two registers, a culturally adapted passage, a term kept in English deliberately). No notes for routine work.

## 9. Final self-check (silent)

Before returning, scan once for:
1. Any pt-PT word or *estar a + infinitivo*.
2. False friends from section 4.
3. Gerundismo and "o mesmo" as pronoun.
4. Placeholders/code/tags altered or missing (count them against the source).
5. Number/date/currency format.
6. Terminology consistency with the glossary and within the text.
7. Read it aloud mentally: would a Brazilian notice it's a translation? If yes, rewrite that sentence.

