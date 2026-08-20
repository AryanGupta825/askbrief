# Hiring Brief Parser

Turns a free-text hiring brief (JD, Slack message, voice transcript, WhatsApp
message — English or Hinglish) into a structured criteria object for
downstream search/matching.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env and add your GOOGLE_API_KEY
```

Get a free Gemini API key at https://aistudio.google.com/apikey.

## Usage

**Library**
```python
from parser import parse_brief
result = parse_brief("need 2 senior backend people, Kafka mandatory, 5-8 yrs")
```

**CLI**
```bash
python -m parser --input briefs/F01.txt --out out/F01.json
```

**HTTP**
```bash
uvicorn parser.api:app --reload
curl -X POST localhost:8000/parse -H "Content-Type: application/json" \
     -d '{"text": "need 2 senior backend people, Kafka mandatory, 5-8 yrs"}'
```

## Running against all five briefs

```bash
for f in briefs/F0*.txt; do
  id=$(basename "$f" .txt)
  python -m parser --input "$f" --out "out/${id}.json"
done
```

## Verification

```bash
python eval.py
```
Checks the five committed outputs against source-grounded, hand-derived
expectations (not tautological "did it run" checks) — including correction
handling (F04), calibrated nulls on a near-empty brief (F03), and the
must-have/preferred distinction on a code-mixed brief (F05). Exits non-zero
on any failure.

## Token cost

Every call appends `{brief_id, total_tokens}` to `out/token_usage.jsonl`.
`parser.average_token_cost()` returns the running average.

## Project layout

```
parser/         core implementation + CLI + FastAPI adapters
prompts/        versioned prompt templates (extract_v1.txt)
briefs/         the five input briefs, verbatim
out/            parser output JSON + token usage log
eval.py         verification harness
NOTES.md        design rationale (schema, hardest brief, fragility, hours)
```

See `NOTES.md` for the reasoning behind schema and prompt design decisions.
