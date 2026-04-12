# AI Event Scenario Insight Platform — 설정 가이드

> 처음 실행까지 약 20분 소요. 모두 무료 플랜으로 진행합니다.

---

## 사전 준비물

| 항목 | 링크 | 비용 |
|------|------|------|
| OpenAI 계정 | https://platform.openai.com | 무료 가입, API 사용량 과금 |
| Supabase 계정 | https://supabase.com | 무료 (500MB) |
| GitHub 계정 | https://github.com | 무료 |
| Python 3.11+ | https://python.org | 무료 |

---

## STEP 1 — OpenAI API 키 발급

1. https://platform.openai.com/api-keys 접속
2. **"Create new secret key"** 클릭
3. 이름 입력 (예: `event-platform`) → **Create**
4. 표시된 키를 복사해 안전한 곳에 보관  
   형식: `sk-proj-xxxxxxxxxxxxxxxx`

> ⚠️ 키는 한 번만 표시됩니다. 반드시 복사하세요.

**예상 비용**: 시나리오 3개 생성 기준 1회 약 $0.01~0.03 (GPT-4o)  
→ 하루 1회 실행 시 월 $0.30~0.90

---

## STEP 2 — Supabase 프로젝트 생성

1. https://supabase.com 접속 → **"Start your project"**
2. GitHub으로 로그인 → **"New project"**
3. 프로젝트 이름 입력 (예: `event-platform`)
4. 데이터베이스 비밀번호 설정 (기록해 두기)
5. 리전 선택: **Northeast Asia (Seoul)** 권장
6. **"Create new project"** → 약 1분 대기

### API 키 확인

프로젝트 생성 완료 후:

```
Settings (좌측 메뉴) → API
```

복사할 항목:
- **Project URL**: `https://xxxxxxxxxxxx.supabase.co`
- **anon / public** 키: `eyJhbGciOiJIUzI1NiIsInR5cCI6...`

### 데이터베이스 스키마 적용

```
SQL Editor (좌측 메뉴) → "New query"
```

`database/schema.sql` 파일 전체 내용을 붙여넣고 → **Run** 클릭

성공 메시지: `Success. No rows returned`

---

## STEP 3 — 로컬 환경 설정

### 패키지 설치

```bash
cd "AI event scenario insight platform"
pip install -r backend/requirements.txt
```

### 환경변수 파일 생성

```bash
cp backend/.env.example backend/.env
```

`backend/.env` 파일을 열고 실제 값으로 교체:

```env
OPENAI_API_KEY=sk-proj-여기에_실제_키_입력
SUPABASE_URL=https://여기에_프로젝트ID.supabase.co
SUPABASE_ANON_KEY=eyJ여기에_실제_anon_key_입력
```

---

## STEP 4 — API 연결 테스트

```bash
python backend/scripts/test_apis.py
```

### 정상 출력 예시

```
==================================================
  🧪 API CONNECTION TEST
==================================================

1️⃣  GDELT (키 불필요)
   ✅ PASS — 3개 수신
      · Iran sanctions tighten as US extends restrictions
      · OPEC+ agrees to further output cuts

2️⃣  OpenAI
   ✅ PASS — OK

3️⃣  Supabase
   ✅ PASS — 연결 성공

==================================================
  ✅ PASS  GDELT
  ✅ PASS  OpenAI
  ✅ PASS  Supabase

  결과: 3/3 통과
  🚀 개발 시작 가능!
```

3/3 통과 확인 후 다음 단계로 이동합니다.

---

## STEP 5 — 수동 파이프라인 실행 (첫 테스트)

```bash
python backend/scripts/daily_run.py
```

약 30~60초 후 완료. Supabase 대시보드에서 확인:

```
Table Editor → events    (수집된 이벤트 목록)
Table Editor → scenarios (생성된 시나리오 3개)
```

---

## STEP 6 — GitHub Actions 자동화 설정

### 저장소 생성

1. https://github.com/new 접속
2. 저장소 이름: `event-scenario-platform`
3. **Private** 선택 (API 키 보호)
4. **Create repository**

### 코드 업로드

```bash
git init
git add .
git commit -m "feat: initial platform setup"
git remote add origin https://github.com/YOUR_USERNAME/event-scenario-platform.git
git push -u origin main
```

### Secrets 등록

저장소 → **Settings → Secrets and variables → Actions → New repository secret**

| Secret 이름 | 값 |
|------------|-----|
| `OPENAI_API_KEY` | Step 1에서 복사한 키 |
| `SUPABASE_URL` | Step 2에서 복사한 URL |
| `SUPABASE_ANON_KEY` | Step 2에서 복사한 anon 키 |

### 자동화 확인

저장소 → **Actions** 탭 → `Daily Scenario Generation` 워크플로우 확인

수동 실행 테스트: **Run workflow** → **Run workflow** 클릭

---

## 실행 일정

| 시간 | 동작 |
|------|------|
| 매일 10:00 KST | GitHub Actions 자동 실행 |
| 실행 소요시간 | 약 2~3분 |
| 생성 결과 | Supabase에 시나리오 3개 저장/업데이트 |

---

## 트러블슈팅

### GDELT FAIL
- 일시적 네트워크 오류일 수 있음. 5분 후 재시도
- GDELT 서버 상태 확인: https://api.gdeltproject.org

### OpenAI FAIL
- API 키가 정확한지 확인 (sk-proj- 로 시작)
- 잔액 확인: https://platform.openai.com/usage
- 결제 수단 등록 필요할 수 있음

### Supabase FAIL
- URL 형식 확인: `https://xxxxxx.supabase.co` (끝에 / 없음)
- anon key가 아닌 service_role key를 입력했는지 확인
- 프로젝트가 pause 상태인지 확인 (무료 플랜은 7일 비활성 시 자동 pause)

### GitHub Actions 실패
- Secrets가 정확히 등록되었는지 확인
- Actions 로그에서 오류 메시지 확인
- 수동 실행(`workflow_dispatch`)으로 테스트

---

## 비용 요약

| 서비스 | 무료 한도 | 예상 사용량 | 월 비용 |
|--------|----------|------------|--------|
| GDELT | 무제한 | — | $0 |
| OpenAI GPT-4o | — | 30회/월 | ~$0.50 |
| Supabase | 500MB | ~1MB/월 | $0 |
| GitHub Actions | 2,000분/월 | ~90분/월 | $0 |
| Vercel (프론트) | 무제한 | — | $0 |
| **합계** | | | **~$0.50/월** |

---

## 다음 단계

모든 설정 완료 후:

1. **프론트엔드 개발**: Next.js + Vercel로 시나리오 표시 페이지 구축
2. **구독 폼 추가**: 이메일 수집 (Supabase Auth 또는 Resend)
3. **SEO 최적화**: 시나리오 페이지 정적 생성으로 검색 유입 확보
4. **유료화 전환**: 구독자 확보 후 Stripe 연동 ($9.99/월)
