# NOTES

**Schema, and why.** `role_title/family/seniority`, `experience{min,max}`,
`must_have_skills` / `preferred_skills` (kept separate, not one array with
flags), `location{cities,work_mode}`, `domain`, `compensation{min,max}`,
`headcount`, `exclusions`, and a `confidence` map (per top-level field:
`explicit` / `inferred` / `not_stated`). The `confidence` field is the main
design decision: the brief's Parser A vs B comparison is really asking
"do you fill gaps or stay silent?" — the answer is both, tagged, so a
downstream system can decide whether to trust an inferred `work_mode` the
same as an explicit one. I left out any narrative/summary field and any
"culture fit"-style speculative field — nothing downstream needs prose.
`compensation` and `experience` are numeric min/max objects, not strings,
because search needs to filter on them.

**Structured output.** Gemini's `responseMimeType: application/json` plus a
schema-shaped prompt in `prompts/extract_v1.txt` (not inline — versioned so
prompt changes are diffable and reviewable separately from code). I
rejected function-calling/tool-use for this because a single JSON-mode
generation is one call, cheaper, and sufficient — no multi-turn tool loop is
needed for a single extraction. I also rejected asking the model to
"explain its reasoning" in the same call; that inflates tokens for no
downstream value, so confidence is a structured field, not free prose.

**Hardest brief.** F04 (voice transcript) — it self-corrects mid-sentence
("said five... actually seven") and expresses location indifference rather
than a location. The prompt explicitly instructs "use the latest stated
value only" for corrections, and treats "I don't care where they sit" as an
inferred remote-leaning work_mode. I'm least confident about the boundary
between "reasonably inferred" and "invented" here — a stricter reading
would leave work_mode null since "don't care" isn't quite "remote."

**Where it's fragile.** No retry/backoff on transient Gemini errors — a
timeout just fails the brief. No handling for briefs that name two roles at
once (out of scope per the floor schema, which assumes one role per brief).
Currency is hardcoded to INR; a brief quoting USD would be extracted wrong.
With another 5 hours: add one retry with backoff, a second brief-quality
check ("does this brief describe more than one role?") before extraction,
and a small golden-set regression file so eval.py can flag drift across
prompt versions, not just correctness on these five.

**Hours spent:** ~4.5 hours (schema/prompt design ~1h, core+adapters ~1.5h,
eval.py ~1h, briefs/testing/write-up ~1h). LLM calls themselves were not
run against live Gemini in this environment — the pipeline was verified
end-to-end with mocked model responses (see commit history); token-cost
tracking is wired up and will populate `out/token_usage.jsonl` on first
real run.
