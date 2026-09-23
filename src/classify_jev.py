"""Offline Jev enrichment for source-grounded DPWH budget records.

Jev never changes amounts, source pages, offices, or parser hierarchy. It only adds
structured, confidence-aware clarity and project-type signals after extraction.
"""
import argparse
import concurrent.futures
import json
import urllib.error
import urllib.request
from pathlib import Path

from .budget_guard import estimated_cost
from .config import JEV_BUDGET_USD, JEV_DRY_RUN, JEV_MODEL, TYPESAFE_API_KEY
from .db import connect

API_URL = 'https://api.typesafe.ai/v1/systemone'
MIN_CONFIDENCE = 0.80


def questions():
    return {
        'project_type': {
            'type': 'choice',
            'instructions': 'Choose the best plain project category from the source fields. Do not invent a project purpose.',
            'criteria': {
                'road': 'Road, highway, pavement, or transport-route work.',
                'bridge': 'Bridge or flyover work.',
                'flood_control': 'Flood control, river, drainage, or slope protection work.',
                'water_system': 'Water supply, irrigation, sewer, or sanitation work.',
                'public_building': 'A public building, facility, or national building program.',
                'other': 'A different or unclear public-works category.'
            }
        },
        'location_clarity': {
            'type': 'choice',
            'instructions': 'Classify whether the source fields state a useful location. Do not infer a missing city, province, or district.',
            'criteria': {
                'clear': 'A city, municipality, province, district, or specific local office is stated.',
                'region_only': 'Only a region-level location is stated.',
                'unclear': 'No useful location is stated.'
            }
        },
        'title_specificity': {
            'type': 'choice',
            'instructions': 'Classify whether the title tells a citizen what is being funded.',
            'criteria': {
                'specific': 'It names a concrete project, asset, or purpose.',
                'broad': 'It is a generic allocation or does not explain the work.'
            }
        },
        'manual_review': {
            'type': 'noul',
            'instructions': 'Should a person check the official source because the title or location is unclear? This is a data-clarity decision, never a corruption or wrongdoing judgment.',
            'criteria': {
                'true': 'The wording is too unclear for a citizen to understand the project or location.',
                'false': 'The wording is clear enough for a citizen to understand.'
            }
        }
    }


def state_for(row):
    return {
        'project_title': row['project_title'],
        'implementing_office': row['implementing_office'],
        'region': row['region'],
        'province': row['province'],
        'city_municipality': row['city_municipality'],
        'amount_pesos': int(row['amount'] or 0),
        'source_page': row['source_page'],
    }


def ask_jev(row):
    payload = {'model': JEV_MODEL, 'state': state_for(row), 'questions': questions()}
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {TYPESAFE_API_KEY}', 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Jev API returned HTTP {error.code}') from error


def public_label(answers):
    location = answers['location_clarity']
    title = answers['title_specificity']
    manual_probability = answers['manual_review']['noul']
    if location['choice'] == 'unclear' and location['confidence'] >= MIN_CONFIDENCE:
        return 'Unclear Location'
    if title['choice'] == 'broad' and title['confidence'] >= MIN_CONFIDENCE:
        return 'Broad Project Title'
    if manual_probability >= 0.80:
        return 'Needs Manual Review'
    return ''


def write_decision(con, row, response):
    answers = response['answers']
    label = public_label(answers)
    project_type = answers['project_type']
    location = answers['location_clarity']
    title = answers['title_specificity']
    usage = response['usage']
    con.execute(
        '''INSERT OR REPLACE INTO jev_decisions
        (project_id, model, project_type_choice, project_type_confidence, location_choice,
         location_confidence, title_choice, title_confidence, manual_review_probability,
         public_label, response_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (row['id'], response['model'], project_type['choice'], project_type['confidence'],
         location['choice'], location['confidence'], title['choice'], title['confidence'],
         answers['manual_review']['noul'], label, json.dumps(response, ensure_ascii=False)),
    )
    # Jev may enrich only its designated fields. Source facts stay parser-owned.
    con.execute(
        '''UPDATE projects SET project_type=?, location_clarity=?, title_specificity=?,
           needs_manual_review_score=?, review_label=?, review_reason=?, updated_at=CURRENT_TIMESTAMP
           WHERE id=?''',
        (project_type['choice'] if project_type['confidence'] >= MIN_CONFIDENCE else row['project_type'],
         location['choice'] if location['confidence'] >= MIN_CONFIDENCE else row['location_clarity'],
         title['choice'] if title['confidence'] >= MIN_CONFIDENCE else row['title_specificity'],
         answers['manual_review']['noul'], label,
         'Jev offline data-clarity decision. Check the official source page.' if label else '', row['id']),
    )
    con.execute(
        'INSERT INTO jev_usage (project_id, model, input_tokens, output_tokens, estimated_cost_usd) VALUES (?, ?, ?, ?, ?)',
        (row['id'], response['model'], usage['input_tokens'], usage['output_tokens'], estimated_cost(usage['input_tokens'])),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True)
    parser.add_argument('--limit', type=int, default=25)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--leaf-only', action='store_true', help='Classify only public project and office records.')
    args = parser.parse_args()
    if JEV_DRY_RUN:
        raise SystemExit('JEV_DRY_RUN is true. Set it to false only for an owner-approved offline run.')
    if not TYPESAFE_API_KEY:
        raise SystemExit('TYPESAFE_API_KEY is missing from the local .env file.')
    con = connect(Path(args.db))
    where_leaf = ' AND is_leaf = 1' if args.leaf_only else ''
    rows = con.execute(f'''SELECT * FROM projects WHERE id NOT IN
                        (SELECT project_id FROM jev_decisions){where_leaf} ORDER BY source_pdf_page, id LIMIT ?''', (args.limit,)).fetchall()
    already_spent = con.execute('SELECT COALESCE(SUM(estimated_cost_usd), 0) FROM jev_usage').fetchone()[0]
    # Conservative guard: do not start a batch that could exceed the local $1 cap.
    max_per_row = estimated_cost(1_500)
    allowed = max(0, int((JEV_BUDGET_USD - already_spent) / max_per_row))
    rows = rows[:allowed]
    if not rows:
        print(json.dumps({'processed': 0, 'reason': 'no_unclassified_rows_or_budget_guard'}))
        return
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as pool:
        pending = {pool.submit(ask_jev, row): row for row in rows}
        for future in concurrent.futures.as_completed(pending):
            row = pending[future]
            results.append((row, future.result()))
    for row, response in results:
        write_decision(con, row, response)
    con.commit()
    usage = con.execute('''SELECT COUNT(*) AS calls, COALESCE(SUM(input_tokens), 0) AS input_tokens,
                           COALESCE(SUM(output_tokens), 0) AS output_tokens,
                           COALESCE(SUM(estimated_cost_usd), 0) AS cost FROM jev_usage''').fetchone()
    labels = dict(con.execute('SELECT public_label, COUNT(*) FROM jev_decisions GROUP BY public_label').fetchall())
    print(json.dumps({'processed': len(results), 'model': results[0][1]['model'], 'total_calls': usage['calls'],
                      'input_tokens': usage['input_tokens'], 'output_tokens': usage['output_tokens'],
                      'estimated_cost_usd': usage['cost'], 'labels': labels}, indent=2))


if __name__ == '__main__':
    main()

