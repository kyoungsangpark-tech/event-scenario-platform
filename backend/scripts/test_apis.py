"""
API 연결 테스트 — 개발 시작 전 반드시 실행
실행: python backend/scripts/test_apis.py
"""

import os, sys, requests
from dotenv import load_dotenv
load_dotenv()

OK, NG, SK = "✅ PASS", "❌ FAIL", "⚠️  SKIP"
results = {}

print("\n" + "="*50)
print("  🧪 API CONNECTION TEST")
print("="*50)

# 1. GDELT
print("\n1️⃣  GDELT (키 불필요)")
try:
    r = requests.get("https://api.gdeltproject.org/api/v2/doc/doc",
                     params={"query": "global", "mode": "artlist", "maxrecords": 3, "format": "json"},
                     timeout=8)
    arts = r.json().get("articles", [])
    print(f"   {OK} — {len(arts)}개 수신")
    for a in arts[:2]:
        print(f"      · {a['title'][:55]}")
    results["GDELT"] = OK
except Exception as e:
    print(f"   {NG} — {e}")
    results["GDELT"] = NG

# 2. Anthropic Claude
print("\n2️⃣  Anthropic Claude")
key = os.getenv("ANTHROPIC_API_KEY")
if not key:
    print(f"   {SK} — .env 에 ANTHROPIC_API_KEY 없음")
    results["Claude"] = SK
else:
    try:
        import anthropic
        res = anthropic.Anthropic(api_key=key).messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "Reply with just: OK"}],
        )
        print(f"   {OK} — {res.content[0].text.strip()}")
        results["Claude"] = OK
    except Exception as e:
        print(f"   {NG} — {e}")
        results["Claude"] = NG

# 3. Supabase
print("\n3️⃣  Supabase")
url, akey = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY")
if not url or not akey:
    print(f"   {SK} — .env 에 SUPABASE_URL / SUPABASE_ANON_KEY 없음")
    results["Supabase"] = SK
else:
    try:
        from supabase import create_client
        create_client(url, akey).table("events").select("id").limit(1).execute()
        print(f"   {OK} — 연결 성공")
        results["Supabase"] = OK
    except Exception as e:
        if "does not exist" in str(e):
            print(f"   {OK} — 연결 성공 (테이블 미생성 → schema.sql 실행 필요)")
            results["Supabase"] = OK
        else:
            print(f"   {NG} — {e}")
            results["Supabase"] = NG

# 요약
print("\n" + "="*50)
passed = sum(1 for v in results.values() if OK in v)
for k, v in results.items():
    print(f"  {v}  {k}")
print(f"\n  결과: {passed}/{len(results)} 통과")
print("  🚀 개발 시작 가능!\n" if passed >= 2 else "  ⚠️  API 키를 확인하세요.\n")
sys.exit(0 if passed >= 2 else 1)
