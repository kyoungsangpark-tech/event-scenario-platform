"""
이벤트 우선순위 스코어링 모듈
- trust(출처신뢰도) · tone(감정강도) · topic(중요도) 가중 합산
- 토픽 다양성을 보장하며 Top 3 선별
"""

TOPIC_WEIGHT = {
    "geopolitics": 1.0,
    "energy":      0.9,
    "economy":     0.85,
    "finance":     0.8,
    "tech_policy": 0.7,
}


def score_event(event: dict) -> float:
    """임팩트 스코어 (0.0 ~ 1.0) = trust*0.4 + tone*0.3 + topic*0.3"""
    trust  = event.get("trust_score", 0.5)
    tone   = min(abs(event.get("tone", 0)) / 10.0, 1.0)
    weight = TOPIC_WEIGHT.get(event.get("topic", ""), 0.5)
    return round(trust * 0.4 + tone * 0.3 + weight * 0.3, 4)


def rank_events(events: list[dict], top_n: int = 20) -> list[dict]:
    """스코어 부여 후 내림차순 정렬"""
    for e in events:
        e["impact_score"] = score_event(e)
    return sorted(events, key=lambda e: e["impact_score"], reverse=True)[:top_n]


def select_top3(events: list[dict]) -> list[dict]:
    """토픽 다양성 보장하며 Top 3 선별"""
    ranked, selected, used = rank_events(events), [], []
    for e in ranked:
        if e.get("topic") not in used:
            selected.append(e)
            used.append(e["topic"])
        if len(selected) == 3:
            break
    # 다양성 확보 실패 시 스코어 순 보충
    for e in ranked:
        if len(selected) == 3:
            break
        if e not in selected:
            selected.append(e)
    return selected
