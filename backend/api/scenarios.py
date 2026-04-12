"""
AI 시나리오 생성 엔진 (Anthropic Claude)
- 이벤트 → 3개 시나리오 자동 생성
- 기존 시나리오 매일 업데이트
- JSON 강제 출력으로 파싱 오류 방지
"""

import os
import json
import logging
import anthropic

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# 비용 절감 원하면 "claude-haiku-4-5-20251001" 으로 변경
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """
You are a senior geopolitical risk analyst.

Given a world event, generate EXACTLY 3 mutually exclusive scenarios
for how it may unfold over the next 1–3 months.

Rules:
- Never "predict". Present POSSIBLE scenarios only.
- Each scenario must be logically distinct and plausible.
- Respond ONLY with valid JSON — no extra text, no markdown, no code blocks.

Output format:
{
  "event_summary": "one-sentence summary",
  "scenarios": [
    {
      "id": "A",
      "name": "Scenario name",
      "probability_label": "Low | Medium | High",
      "trigger": "What must happen for this to occur",
      "event_chain": ["step 1", "step 2", "step 3"],
      "market_impact": {
        "oil": "+10% / -5% / stable",
        "gold": "...",
        "usd": "...",
        "equities": "..."
      },
      "reasoning": "2–3 sentence explanation"
    }
  ],
  "causal_links": [
    {"from": "event A", "to": "event B", "confidence": 0.85}
  ]
}
"""


def _parse_json(text: str) -> dict:
    """응답에서 JSON 추출 (코드블록 포함 대응)"""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def generate(event: dict) -> dict | None:
    """단일 이벤트 → 3개 시나리오 생성"""
    prompt = f"""
Event : {event.get('title', '')}
Source: {event.get('source', '')}
Topic : {event.get('topic', '')}
Date  : {event.get('published_at', '')}

Generate 3 scenarios. Return ONLY valid JSON.
"""
    try:
        res = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        result = _parse_json(res.content[0].text)
        result["event_title"] = event.get("title", "")
        result["event_topic"] = event.get("topic", "")
        logger.info(f"생성 완료: {event.get('title','')[:50]}")
        return result
    except Exception as e:
        logger.error(f"생성 오류: {e}")
        return None


def update(existing: dict, new_event: dict) -> dict | None:
    """새 신호를 반영해 기존 시나리오 업데이트"""
    prompt = f"""
ORIGINAL EVENT    : {existing.get('event_title', '')}
ORIGINAL SCENARIOS: {json.dumps(existing.get('scenarios', []), indent=2)}

NEW DEVELOPMENT: {new_event.get('title', '')} ({new_event.get('published_at', '')})

Update the 3 scenarios. Adjust probability_label and reasoning accordingly.
Keep the same JSON format. Return ONLY valid JSON.
"""
    try:
        res = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        updated = _parse_json(res.content[0].text)
        updated["updated_by"] = new_event.get("title", "")
        return updated
    except Exception as e:
        logger.error(f"업데이트 오류: {e}")
        return None


def generate_batch(events: list[dict]) -> list[dict]:
    """Top 3 이벤트 일괄 시나리오 생성"""
    results = []
    for e in events[:3]:
        s = generate(e)
        if s:
            s["source_event"] = e
            results.append(s)
    logger.info(f"총 {len(results)}개 시나리오 생성")
    return results
