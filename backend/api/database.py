"""
Supabase DB 연동 모듈
- Events / Scenarios / Feedback CRUD
- URL 중복 방지, 매일 업데이트 관리
"""

import os
import json
import logging
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)


def db() -> Client:
    """읽기 전용 (anon 키)"""
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])


def db_admin() -> Client:
    """쓰기 권한 (service_role 키 - 서버사이드만 사용)"""
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# ── Events ─────────────────────────────────────────────

def upsert_event(event: dict) -> dict | None:
    """URL 기준 중복 방지 저장"""
    existing = db().table("events").select("id").eq("url", event.get("url", "")).execute()
    if existing.data:
        return existing.data[0]
    row = {k: event.get(k) for k in
           ["title", "url", "source", "topic", "impact_score", "trust_score", "tone", "published_at"]}
    res = db_admin().table("events").insert(row).execute()
    return res.data[0] if res.data else None


def get_active_events() -> list[dict]:
    return db().table("events").select("*").eq("is_active", True)\
               .order("impact_score", desc=True).execute().data or []


# ── Scenarios ──────────────────────────────────────────

def save_scenario(event_id: int, data: dict) -> dict | None:
    sc = data.get("scenarios", [])
    row = {
        "event_id":      event_id,
        "event_summary": data.get("event_summary", ""),
        "scenario_a":    json.dumps(sc[0]) if len(sc) > 0 else None,
        "scenario_b":    json.dumps(sc[1]) if len(sc) > 1 else None,
        "scenario_c":    json.dumps(sc[2]) if len(sc) > 2 else None,
        "raw_json":      json.dumps(data, ensure_ascii=False),
        "is_published":  True,
        "generated_at":  datetime.now().isoformat(),
    }
    res = db_admin().table("scenarios").insert(row).execute()
    return res.data[0] if res.data else None


def update_scenario(scenario_id: int, data: dict) -> None:
    sc = data.get("scenarios", [])
    db_admin().table("scenarios").update({
        "scenario_a":   json.dumps(sc[0]) if len(sc) > 0 else None,
        "scenario_b":   json.dumps(sc[1]) if len(sc) > 1 else None,
        "scenario_c":   json.dumps(sc[2]) if len(sc) > 2 else None,
        "raw_json":     json.dumps(data, ensure_ascii=False),
        "updated_at":   datetime.now().isoformat(),
        "update_count": data.get("update_count", 0) + 1,
    }).eq("id", scenario_id).execute()


def get_scenario_by_event(event_id: int) -> dict | None:
    res = db().table("scenarios").select("*").eq("event_id", event_id)\
              .order("generated_at", desc=True).limit(1).execute()
    return res.data[0] if res.data else None


def get_published(limit: int = 10) -> list[dict]:
    return db().table("scenarios")\
               .select("*, events(title, topic, impact_score)")\
               .eq("is_published", True)\
               .order("generated_at", desc=True)\
               .limit(limit).execute().data or []


# ── Feedback ───────────────────────────────────────────

def save_feedback(scenario_id: int, rating: int, comment: str = "") -> None:
    db_admin().table("user_feedback").insert({
        "scenario_id": scenario_id,
        "rating":      rating,
        "comment":     comment,
        "created_at":  datetime.now().isoformat(),
    }).execute()
