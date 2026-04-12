"""
일일 자동 실행 스크립트
GitHub Actions에서 매일 오전 10시 KST 자동 호출

흐름:
  1. GDELT 이벤트 수집
  2. Top 3 선별
  3. DB 저장
  4. 신규 이벤트 → 시나리오 생성
  5. 기존 활성 이벤트 → 시나리오 업데이트
"""

import sys, os, json, logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env 로드 (backend/.env)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from datetime import datetime
from api.gdelt     import fetch_all_topics
from api.scoring   import select_top3, rank_events
from api.scenarios import generate_batch, update as ai_update
from api.database  import (
    upsert_event, save_scenario, update_scenario,
    get_active_events, get_scenario_by_event,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def run():
    log.info("=" * 55)
    log.info(f"▶ 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 55)

    # 1. 수집
    log.info("1) 이벤트 수집 중...")
    all_events = fetch_all_topics(days_back=1)
    if not all_events:
        log.error("이벤트 없음. 종료.")
        sys.exit(1)
    log.info(f"   수집: {len(all_events)}개")

    # 2. Top 3 선별
    log.info("2) Top 3 선별...")
    top3 = select_top3(all_events)
    for i, e in enumerate(top3, 1):
        log.info(f"   [{i}] ({e['topic']}) {e['title'][:55]}  score={e['impact_score']:.3f}")

    # 3. DB 저장
    log.info("3) DB 저장...")
    saved = []
    for e in top3:
        row = upsert_event(e)
        if row:
            e["db_id"] = row["id"]
            saved.append(e)

    # 4. 신규 시나리오 생성
    log.info("4) 신규 시나리오 생성...")
    new_events = [e for e in saved if not get_scenario_by_event(e["db_id"])]
    if new_events:
        for e, s in zip(new_events, generate_batch(new_events)):
            if s:
                save_scenario(e["db_id"], s)
                log.info(f"   저장: {e['title'][:50]}")
    else:
        log.info("   신규 없음")

    # 5. 기존 시나리오 업데이트
    log.info("5) 기존 시나리오 업데이트...")
    ranked = rank_events(all_events, top_n=30)
    count = 0
    for active in get_active_events():
        sc = get_scenario_by_event(active["id"])
        if not sc:
            continue
        trigger = next((e for e in ranked if e.get("topic") == active.get("topic")), None)
        if trigger:
            updated = ai_update(json.loads(sc["raw_json"]), trigger)
            if updated:
                update_scenario(sc["id"], updated)
                count += 1
                log.info(f"   업데이트: {active['title'][:50]}")

    log.info("=" * 55)
    log.info(f"✅ 완료 — 신규: {len(new_events)}개 / 업데이트: {count}개")
    log.info("=" * 55)


if __name__ == "__main__":
    run()
