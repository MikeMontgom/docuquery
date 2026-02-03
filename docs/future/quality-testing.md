# Quality Testing Framework (Deferred to Post-MVP)

> **Status:** Archived for Phase 3 quality iteration. Do not implement until pipeline Steps 1-14 are complete.

This document defines a quality assurance framework for validating PDF processing pipeline output. The automated scoring and QualityLog table are deferred, but the **stage-by-stage checklists below are useful as manual reference** during development.

---

## Why Deferred

1. **Sequential dependency** — Can't test extraction quality until extraction code exists
2. **MVP principle** — Build working pipeline first, polish later
3. **Natural feedback loops** — Manual testing during development catches obvious issues
4. **Scope control** — Automated QA adds infrastructure (QualityLog table, scoring workflows)

**Revisit after:** Pipeline Steps 1-14 complete and working end-to-end.

---

## Pipeline Stages

| Stage | Step | Producer | What to Check |
|-------|------|----------|---------------|
| 1 | Extraction | Gemini 3 | Content completeness, GRAPHIC_INSERT accuracy |
| 2 | Break scoring | GPT-4o | Break placement, no content modification |
| 3 | Regex cleanup | Code | PAGE marker removal, ID resequencing |
| 4 | DP chunking | Code | Chunk sizes 200-1200 tokens, graphic isolation |
| 5 | Summarization | GPT-4o | Telegraphic style, 80-90% shorter |

---

## Quality Dimensions (1-5 Scale)

### Completeness
- 5: Every semantic element from source is present
- 4: Minor omissions (repeated headers, decorative elements)
- 3: Some content missing but main ideas preserved
- 2: Significant content gaps
- 1: Major sections missing

### Accuracy
- 5: Perfect fidelity to source
- 4: Minor formatting differences, no factual errors
- 3: Some transcription errors
- 2: Multiple errors affecting meaning
- 1: Unreliable output

### Structure
- 5: Logical structure perfectly preserved
- 4: Minor structural issues
- 3: Some sections misordered
- 2: Significant structural problems
- 1: Structure is broken

### Format Compliance
- 5: Perfectly follows format rules
- 4: Minor deviations
- 3: Some format violations
- 2: Multiple violations
- 1: Does not follow spec

---

## Stage-Specific Checklists

### Stage 1: Extraction (Gemini 3)
```
[ ] Every page has [PAGE X] marker
[ ] Prose text extracted verbatim (sample 3 paragraphs)
[ ] GRAPHIC_INSERT blocks have valid JSON
[ ] Coordinates in 72 DPI points (letter ~612x792)
[ ] graphic_id format: graphic_p{page}_n{sequence}
[ ] Tables flattened to prose where possible
[ ] TABLE_START only for essential grid structure
[ ] Code blocks preserved with language identifiers
[ ] UI artifacts stripped (content_copy, expand_less)
[ ] Headers/footers removed
[ ] No hallucinated content
[ ] Math uses Unicode where possible
```

### Stage 2: Break Scoring (GPT-4o)
```
[ ] Original text unchanged (diff against Stage 1)
[ ] Break IDs sequential from 1, no gaps
[ ] Scores follow rubric (25/40/60/80/100)
[ ] Score 100 for: headings, before/after GRAPHIC_INSERT
[ ] Score 60 most common for paragraph breaks
[ ] No breaks mid-sentence
[ ] No over-segmentation
```

### Stage 3: Regex Cleanup
```
[ ] All [PAGE X] markers removed
[ ] Break IDs resequenced from 1
[ ] Break scores preserved
[ ] No content accidentally removed
[ ] Source page mapping recorded
```

### Stage 4: DP Chunking
```
[ ] Every chunk 200-1200 tokens
[ ] Mean chunk size near 650 tokens
[ ] GRAPHIC_INSERT isolated as own chunks
[ ] chunk_type correct ("text" or "graphic")
[ ] Sequence numbers 1-indexed, continuous
[ ] No content lost (concatenated = cleaned text)
[ ] Splits only at break markers
[ ] Higher-score breaks preferred
[ ] source_pages populated
[ ] heading_path reflects section headings
```

### Stage 5: Summarization
```
[ ] Graphic chunks use description directly
[ ] Text summaries 80-90% shorter
[ ] Telegraphic style (noun-heavy)
[ ] Key topics captured for routing
[ ] DEFINES: flags for definitions
[ ] CONDITIONS: flags for conditionals
[ ] REFS: flags for cross-references
[ ] No hallucinated topics
```

---

## Future: Automated Quality Log

When implementing automated QA, create a `QualityLog` table in Airtable:

| Field | Type | Description |
|-------|------|-------------|
| test_date | Date | When the test ran |
| document_name | Single Line Text | Test PDF filename |
| stage | Single Select | Stage 1-5 |
| model | Single Line Text | Model used |
| completeness | Number | 1-5 score |
| accuracy | Number | 1-5 score |
| structure | Number | 1-5 score |
| format_compliance | Number | 1-5 score |
| overall | Number | Average score |
| issues_count | Number | Must-fix count |
| warnings_count | Number | Should-fix count |
| notes | Long Text | Key findings |
| blocker | Checkbox | Downstream-breaking issue |

---

## Sampling Strategy for Large Documents

Don't validate every page. Sample:
- First 2 pages (setup/formatting issues)
- 2 pages from middle (fatigue/drift)
- Last 2 pages (truncation)
- Any pages with graphics or tables

---

## Comparison Techniques

### Text Comparison (Stages 2, 3)
```bash
# Strip markers, then diff
sed 's/\[BREAK id=[0-9]* score=[0-9]*\]//g' stage1.txt > stage1_clean.txt
sed 's/\[BREAK id=[0-9]* score=[0-9]*\]//g' stage2.txt > stage2_clean.txt
diff stage1_clean.txt stage2_clean.txt
```

### Token Estimation (Stage 4)
```python
import re
def estimate_tokens(text):
    words = len(re.findall(r'\S+', text))
    return int(words * 1.3)
```
