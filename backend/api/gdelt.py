"""
GDELT 이벤트 수집 모듈
- 완전 무료, 가입 불필요, 15분 간격 실시간
- 5개 토픽(지정학/에너지/경제/금융/기술) 수집
- 중복 URL 제거, 출처 신뢰도 자동 부여
"""

import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

HIGH_TRUST_SOURCES = [
    "reuters.com", "apnews.com", "bbc.com", "bloomberg.com",
    "ft.com", "wsj.com", "nytimes.com", "aljazeera.com",
]

TOPICS = {
    "geopolitics": "(sanctions OR military OR conflict OR nuclear) (iran OR russia OR china OR northkorea)",
    "energy":      "(oil OR gas OR opec) (price OR supply OR crisis OR cut)",
    "economy":     "(inflation OR recession OR fed OR rate hike) (usa OR europe OR china)",
    "finance":     "(bank OR crypto OR dollar OR market) (crisis OR collapse OR surge)",
    "tech_policy": "(AI regulation OR chip ban OR tech war) (usa OR china OR eu)",
}


def fetch_events(query: str, days_back: int = 1, max_records: int = 25) -> list[dict]:
    """GDELT API 호출 → 정규화된 이벤트 리스트"""
    start = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d%H%M%S")
    params = {
        "query":         query,
        "mode":          "artlist",
        "maxrecords":    max_records,
        "format":        "json",
        "startdatetime": start,
        "sourcelang":    "english",
        "sort":          "ToneDesc",
    }
    try:
        r = requests.get(GDELT_URL, params=params, timeout=10)
        r.raise_for_status()
        return [_normalize(a) for a in r.json().get("articles", [])]
    except Exception as e:
        logger.error(f"GDELT 오류: {e}")
        return []


def _normalize(raw: dict) -> dict:
    domain = raw.get("domain", "").lower()
    return {
        "title":        raw.get("title", ""),
        "url":          raw.get("url", ""),
        "source":       raw.get("source", ""),
        "domain":       domain,
        "published_at": raw.get("pubdate", ""),
        "tone":         float(raw.get("tone", 0)),
        "trust_score":  1.0 if any(t in domain for t in HIGH_TRUST_SOURCES) else 0.5,
        "impact_score": 0.0,
        "topic":        "",
    }


def fetch_all_topics(days_back: int = 1) -> list[dict]:
    """전체 토픽 수집 후 중복 제거"""
    all_events, seen = [], set()
    for topic, query in TOPICS.items():
        for e in fetch_events(query, days_back=days_back):
            if e["url"] not in seen:
                e["topic"] = topic
                all_events.append(e)
                seen.add(e["url"])
    logger.info(f"수집 완료: {len(all_events)}개")
    return all_events
