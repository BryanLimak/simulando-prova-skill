---
name: classificados-prova
description: Gera o JSON de uma prova (um agrupador com um ou mais simulados de questões de múltipla escolha) no molde "classificados-prova/v1", pronto para importar na plataforma Classificados. Use sempre que a pessoa pedir para criar uma prova, simulado, questionário, lista de exercícios ou banco de questões para importar, ou para converter um material (apostila, PDF, anotações, lista de perguntas) nesse formato.
---

# Skill: gerar o JSON de uma prova (classificados-prova/v1)

Você monta o arquivo JSON de uma **prova**. Uma prova é um agrupador com **N simulados**; cada simulado tem suas próprias questões de múltipla escolha, nota mínima e tempo limite. A plataforma importa esse JSON de uma vez só.

## Fluxo

1. **Entenda o pedido.** Descubra (pergunte só o que não dá para inferir): tema, público/nível, quantos simulados, quantas questões por simulado, idioma (padrão: português do Brasil), se pode haver questões com mais de uma resposta correta, e se há material de referência para extrair as questões.
   - Se a pessoa só disse "crie uma prova de X", use o padrão: **3 simulados de 20 questões**, 4 alternativas, uma correta, dificuldade crescente entre os simulados.
2. **Escreva as questões** com qualidade de prova real: enunciado claro e autossuficiente, alternativas plausíveis e do mesmo tamanho, distratores que testam erros comuns, sem "todas as anteriores" ou "nenhuma das anteriores", sem pistas gramaticais, sem repetir questões entre simulados. Varie a posição da alternativa correta.
3. **Explique cada resposta** no campo `explanation` (1 a 3 frases dizendo por que a correta está certa e, quando ajudar, por que a mais tentadora está errada).
4. **Entregue só o JSON** (em um bloco de código `json` ou como arquivo `.json`). Nada de texto antes ou depois, nem comentários dentro do JSON.
5. **Revise antes de entregar** usando o checklist no fim.

## Molde (copie a estrutura exatamente)

```json
{
  "format": "classificados-prova/v1",
  "prova": {
    "title": "Título da prova",
    "description": "Para quem é, o que cobre, fonte (opcional)",
    "category": "certificacoes",
    "icon": "ABC"
  },
  "simulados": [
    {
      "title": "Simulado 1 · Fundamentos",
      "description": "Opcional",
      "pass_score": 70,
      "time_limit_min": 60,
      "questions": [
        {
          "text": "Enunciado da questão?",
          "explanation": "Por que a alternativa correta está certa.",
          "alternatives": [
            { "text": "Alternativa A", "is_correct": true },
            { "text": "Alternativa B" },
            { "text": "Alternativa C" },
            { "text": "Alternativa D" }
          ]
        }
      ]
    }
  ]
}
```

## Campos

| Campo | Obrigatório | Regras |
|---|---|---|
| `format` | sim | sempre `"classificados-prova/v1"` |
| `prova.title` | sim | 2 a 160 caracteres |
| `prova.description` | não | até 3000 caracteres |
| `prova.category` | não | um dos slugs: `tecnologia`, `programacao`, `certificacoes`, `idiomas`, `concursos`, `vestibular`, `escolar`, `negocios`, `saude`, `direito`, `exatas`, `humanas`, `ciencias`, `outros`. Se não souber, omita. |
| `prova.icon` | não | até 4 letras maiúsculas (ex.: `"ENEM"`, `"OAB"`); se omitir, a plataforma usa as iniciais do título |
| `simulados` | sim | lista com 1 a 50 simulados, na ordem em que devem aparecer |
| `simulados[].title` | sim | 2 a 160 caracteres; use nomes que ajudem a escolher (ex.: "Simulado 2 · Intermediário") |
| `simulados[].description` | não | até 3000 caracteres |
| `simulados[].pass_score` | não | nota mínima em %, 1 a 100 (padrão 70) |
| `simulados[].time_limit_min` | não | minutos para o modo "simulado real", 1 a 600; `null` ou omitido = sem limite |
| `simulados[].questions` | sim | 1 a 1000 questões |
| `questions[].text` | sim | enunciado; pode ter quebras de linha e trechos de código (preservados) |
| `questions[].explanation` | recomendado | explicação exibida depois de responder |
| `questions[].alternatives` | sim | 2 a 8 alternativas; **pelo menos uma** com `"is_correct": true`; mais de uma correta vira questão de múltipla escolha (a pessoa precisa marcar todas) |
| `alternatives[].text` | sim | texto da alternativa (não repita a letra "A)", a plataforma numera) |
| `alternatives[].is_correct` | não | `true` só nas corretas; nas outras omita ou use `false` |

## Boas práticas de conteúdo

- Cobertura: distribua as questões pelos subtemas do assunto; se há um edital ou programa, siga a proporção dele.
- Dificuldade: misture fácil/médio/difícil; se há vários simulados, deixe o primeiro mais básico e o último mais exigente, e diga isso no título ou na descrição.
- Para idiomas, escreva enunciados e alternativas no idioma estudado quando for o caso (a plataforma tem tradução automática inglês → português para quem precisar).
- Para programação, coloque o código no enunciado entre linhas em branco e mantenha a indentação; nunca ponha código em alternativas quando a diferença for só um caractere invisível.
- Se o pedido vier com material (apostila, PDF, texto), extraia as questões com fidelidade ao material e não invente fatos que não estão lá.
- Pedidos grandes (ex.: 10 simulados de 50 questões) podem ser entregues em partes: cada parte é um JSON válido com `simulados` parciais; a pessoa importa todas na mesma prova.

## Checklist final (faça antes de responder)

- [ ] `format` é exatamente `classificados-prova/v1`
- [ ] Há pelo menos 1 simulado, e cada simulado tem pelo menos 1 questão
- [ ] Cada questão tem 2 a 8 alternativas e pelo menos uma `is_correct: true`
- [ ] Nenhuma questão repetida (nem entre simulados)
- [ ] As corretas não estão sempre na mesma posição
- [ ] O JSON é válido (aspas duplas, sem vírgula sobrando, sem comentários)
- [ ] A resposta contém apenas o JSON
