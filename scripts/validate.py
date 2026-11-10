#!/usr/bin/env python3
"""Valida um JSON no molde simulando-prova/v1 sem dependências.

    python scripts/validate.py prova.json

Sai com código 1 se houver erros. Também aceita a exportação de um simulado
({"questions": [...]}) e uma lista de simulados, como a plataforma.
"""
import json
import re
import sys

CATEGORIES = ['tecnologia', 'programacao', 'certificacoes', 'idiomas', 'concursos', 'vestibular', 'escolar',
              'negocios', 'saude', 'direito', 'exatas', 'humanas', 'ciencias', 'outros']
# Letras citadas: {{B}} na explicação (a plataforma troca pela letra da tela quando embaralha)
TOKEN_RE = re.compile(r'\{\{\s*([A-Za-z])\s*\}\}')
PLAIN_REF_RE = re.compile(r'(?:[Aa]lternativas?|[Ll]etras?|[Oo]p[çc](?:ão|ões)|[Oo]ptions?|[Aa]nswers?|[Rr]espostas?)\s*:?\s+[A-H](?!\w)')
CITES_OTHER_RE = re.compile(r'(?<!\w)[A-H]\s+(?:e|and|ou|or)\s+[A-H](?!\w)')
ABOVE_RE = re.compile(r'\b(?:todas|nenhuma)\s+(?:as|das)\s+(?:anteriores|acima)\b|\b(?:all|none)\s+of\s+the\s+above\b', re.I)

# Quantas respostas o enunciado pede: "(Choose two.)", "Choose 3 answers", "Escolha 4", "Which three...", "Quais duas..."
NUMBERS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
           'um': 1, 'uma': 1, 'dois': 2, 'duas': 2, 'três': 3, 'tres': 3, 'quatro': 4, 'cinco': 5, 'seis': 6,
           'sete': 7, 'oito': 8, 'dos': 2, 'cuatro': 4}
NUM = r'([1-8]|' + '|'.join(sorted(NUMBERS, key=len, reverse=True)) + r')'
ASK_VERB_RE = re.compile(
    r'\b(?:choose|select|pick|mark|escolha|selecione|marque|assinale|elija|seleccione|escoja)\s+'
    r'(?:exactly\s+|exatamente\s+|the\s+)?' + NUM +
    r'(?:\s+(?:correct\s+|corretas?\s+)?(?:answers?|options?|responses?|choices?|respostas?|alternativas?|op[çc](?:ões|ão)|opciones))?'
    r'\s*(?:[.):\]]|$)', re.I | re.M)
COMBINED_RE = re.compile(r',|\s(?:and|e|y|&)\s', re.I)
ASK_WHICH_RE = re.compile(
    r'\b(?:which|what)\s+(?:are\s+(?:the\s+)?)?' + NUM + r'\b|\bquais\s+(?:são\s+(?:as\s+|os\s+)?)?' + NUM + r'\b', re.I)


def asked_answers(text, alts):
    """Número de respostas que o enunciado pede, ou None se ele não diz."""
    if not isinstance(text, str):
        return None
    found = [m.group(1) for m in ASK_VERB_RE.finditer(text)]
    if found:
        word = found[-1]
    else:
        m = ASK_WHICH_RE.search(text)
        word = (m.group(1) or m.group(2)) if m else None
        if word is None or word.lower() in ('one', 'um', 'uma', '1'):
            return None
        # "Which two types...?" com alternativas que já trazem os itens juntos ("X and Y") é resposta única
        texts = [a.get('text') for a in alts if isinstance(a, dict)]
        if texts and all(isinstance(t, str) and COMBINED_RE.search(t) for t in texts):
            return None
    return int(word) if word.isdigit() else NUMBERS[word.lower()]


def main() -> int:
    if len(sys.argv) < 2:
        print('Uso: python scripts/validate.py prova.json')
        return 2
    try:
        with open(sys.argv[1], encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        print(f'JSON inválido: {exc}')
        return 1

    errors, warnings = [], []
    err = lambda path, msg: errors.append(f'{path}: {msg}')  # noqa: E731
    warn = lambda path, msg: warnings.append(f'{path}: {msg}')  # noqa: E731

    if isinstance(data, dict) and isinstance(data.get('simulados'), list):
        if data.get('format') not in ('simulando-prova/v1', 'classificados-prova/v1'):
            err('format', f'esperado "simulando-prova/v1", veio {data.get("format")!r}')
        p = data.get('prova') or {}
        if 'title' in p and (not isinstance(p['title'], str) or not 2 <= len(p['title'].strip()) <= 160):
            err('prova.title', 'use 2 a 160 caracteres')
        if 'title' not in p:
            warn('prova.title', 'sem título: a plataforma usa o título do primeiro simulado')
        if p.get('category') is not None and p['category'] not in CATEGORIES:
            err('prova.category', f'categoria desconhecida "{p["category"]}" (aceitas: {", ".join(CATEGORIES)})')
        if p.get('icon') is not None and (not isinstance(p['icon'], str) or len(p['icon']) > 4):
            err('prova.icon', 'até 4 caracteres')
        simulados = data['simulados']
    elif isinstance(data, dict) and isinstance(data.get('questions'), list):
        warn('raiz', 'formato de um simulado só; a plataforma cria uma prova com ele')
        exam = data.get('exam') or {}
        simulados = [{**exam, 'questions': data['questions']}]
    elif isinstance(data, list):
        warn('raiz', 'lista de simulados sem dados da prova')
        simulados = data
    else:
        err('raiz', 'esperado um objeto com "simulados" (ver SKILL.md)')
        simulados = []

    if not simulados:
        err('simulados', 'precisa de pelo menos 1 simulado')
    if len(simulados) > 50:
        err('simulados', 'máximo de 50 simulados')

    seen, total, multi, positions = {}, 0, 0, {}
    gaps = []
    for si, sim in enumerate(simulados):
        sp = f'simulados[{si}]'
        if not isinstance(sim, dict):
            err(sp, 'não é um objeto')
            continue
        if 'title' in sim and (not isinstance(sim['title'], str) or not 2 <= len(sim['title'].strip()) <= 160):
            err(f'{sp}.title', 'use 2 a 160 caracteres')
        ps = sim.get('pass_score')
        if ps is not None and (not isinstance(ps, int) or isinstance(ps, bool) or not 1 <= ps <= 100):
            err(f'{sp}.pass_score', 'inteiro entre 1 e 100')
        tl = sim.get('time_limit_min')
        if tl is not None and (not isinstance(tl, int) or isinstance(tl, bool) or not 1 <= tl <= 600):
            err(f'{sp}.time_limit_min', 'inteiro entre 1 e 600 ou null')
        qs = sim.get('questions')
        if not isinstance(qs, list) or not qs:
            err(f'{sp}.questions', 'precisa de pelo menos 1 questão')
            continue
        if len(qs) > 1000:
            err(f'{sp}.questions', 'máximo de 1000 questões')
        for qi, q in enumerate(qs):
            qp = f'{sp}.questions[{qi}]'
            total += 1
            if not isinstance(q, dict):
                err(qp, 'não é um objeto')
                continue
            text = q.get('text')
            if not isinstance(text, str) or not text.strip():
                err(f'{qp}.text', 'enunciado vazio')
            else:
                key = ' '.join(text.strip().lower().split())
                if key in seen:
                    warn(qp, f'enunciado repetido (igual a {seen[key]})')
                else:
                    seen[key] = qp
            if q.get('explanation') is not None and not isinstance(q['explanation'], str):
                err(f'{qp}.explanation', 'deve ser texto ou null')
            alts = q.get('alternatives')
            if not isinstance(alts, list):
                err(f'{qp}.alternatives', 'precisa de uma lista de alternativas')
                continue
            if len(alts) < 2:
                err(f'{qp}.alternatives', 'pelo menos 2 alternativas')
            if len(alts) > 8:
                err(f'{qp}.alternatives', 'no máximo 8 alternativas')
            correct = 0
            for ai, a in enumerate(alts):
                ap = f'{qp}.alternatives[{ai}]'
                if not isinstance(a, dict):
                    err(ap, 'não é um objeto')
                    continue
                if not isinstance(a.get('text'), str) or not a['text'].strip():
                    err(f'{ap}.text', 'texto vazio')
                if 'is_correct' in a and not isinstance(a['is_correct'], bool):
                    err(f'{ap}.is_correct', 'deve ser true/false')
                if a.get('is_correct') is True:
                    correct += 1
                    positions[ai] = positions.get(ai, 0) + 1
            if correct == 0:
                err(f'{qp}.alternatives', 'nenhuma alternativa marcada com "is_correct": true')
            if correct > 1:
                multi += 1
            n = len(alts)
            asked = asked_answers(text, alts)
            if asked is not None and (asked != correct or asked > n):
                where = f'Simulado {si + 1}, questão {qi + 1}'
                if asked > n:
                    gaps.append(f'{where}: pede {asked}, mas a questão tem só {n} alternativa(s) ({correct} marcada(s) como correta(s))')
                else:
                    gaps.append(f'{where}: pede {asked}, a fonte marca {correct}')
            expl = q.get('explanation')
            if isinstance(expl, str):
                for m in TOKEN_RE.finditer(expl):
                    i = ord(m.group(1).upper()) - 65
                    if i >= n or i > 7:
                        last = chr(64 + min(n, 8))
                        err(f'{qp}.explanation', f'cita {m.group(0)}, mas a questão tem {n} alternativas (de {{{{A}}}} a {{{{{last}}}}})')
                if PLAIN_REF_RE.search(expl):
                    warn(f'{qp}.explanation', 'cite alternativas pela letra entre chaves, como {{B}}: a letra acompanha o embaralhamento')
            if isinstance(text, str) and TOKEN_RE.search(text):
                warn(f'{qp}.text', '{{B}} só é trocado na explicação; no enunciado fica como está')
            for ai, a in enumerate(alts):
                if isinstance(a, dict) and isinstance(a.get('text'), str):
                    t = a['text']
                    if CITES_OTHER_RE.search(t) or ABOVE_RE.search(t) or TOKEN_RE.search(t):
                        warn(f'{qp}.alternatives[{ai}].text', 'alternativa que cita outras ("A e B", "todas as anteriores") fica errada quando as alternativas são embaralhadas')

    if total >= 8 and positions and max(positions.values()) / total > 0.7:
        warn('alternativas', 'a resposta correta está quase sempre na mesma posição; varie')

    print(f'Simulados: {len(simulados)} · Questões: {total} · Com mais de uma correta: {multi}')
    for si, sim in enumerate(simulados):
        if isinstance(sim, dict) and isinstance(sim.get('questions'), list):
            extra = (f', {sim["time_limit_min"]} min' if sim.get('time_limit_min') else '') + (f', mínimo {sim["pass_score"]}%' if sim.get('pass_score') else '')
            print(f'  {si + 1}. {sim.get("title") or "(sem título)"} — {len(sim["questions"])} questão(ões){extra}')
    for w in warnings:
        print('  aviso: ' + w)
    for e in errors:
        print('  ERRO: ' + e)
    if gaps:
        print(f'\n⚠️  {len(gaps)} questão(ões) em que o número de respostas pedido no enunciado não bate com as corretas.')
        print('    Não complete nem remova corretas por conta própria: revise no material original.')
        for g in gaps:
            print('  - ' + g)
    print(f'\n{len(errors)} erro(s): corrija antes de importar.' if errors else '\nOK: pronto para importar.')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
