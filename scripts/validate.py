#!/usr/bin/env python3
"""Valida um JSON no molde classificados-prova/v1 sem dependências.

    python scripts/validate.py prova.json

Sai com código 1 se houver erros. Também aceita a exportação de um simulado
({"questions": [...]}) e uma lista de simulados, como a plataforma.
"""
import json
import sys

CATEGORIES = ['tecnologia', 'programacao', 'certificacoes', 'idiomas', 'concursos', 'vestibular', 'escolar',
              'negocios', 'saude', 'direito', 'exatas', 'humanas', 'ciencias', 'outros']


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
        if data.get('format') != 'classificados-prova/v1':
            err('format', f'esperado "classificados-prova/v1", veio {data.get("format")!r}')
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
    print(f'\n{len(errors)} erro(s): corrija antes de importar.' if errors else '\nOK: pronto para importar.')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
