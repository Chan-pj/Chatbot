# 복복이 (WelBot) — 복지 정책 안내 AI 챗봇

사용자의 나이·가구·소득·관심사·거주 지역을 바탕으로 **맞춤형 복지 정책을 추천**해 주는 RAG 기반 챗봇입니다.
공공데이터포털의 중앙부처·지자체 복지서비스 데이터 약 5,000건을 벡터 DB에 임베딩해 두고, 질문과 의미적으로 가까운 정책을 찾아 LLM이 카드 형태로 답변합니다.

<p align="center">
  <img src="docs/screenshots/login.png" width="48%" />
  <img src="docs/screenshots/chat.png" width="48%" />
</p>

## 주요 기능

- **RAG 기반 정책 검색** — Sentence-Transformers 임베딩 + ChromaDB 코사인 유사도 검색 (top-10)
- **LLM 답변 생성** — Groq API(`openai/gpt-oss-20b`)로 검색 결과를 근거로 JSON 카드 답변 생성, 복지로 신청 링크 제공
- **지역 맞춤 검색** — 내 시군구 · 시도 공통 · 전국 정책을 그룹별로 검색해 섞고, 다른 시군구 전용 정책은 제외. 최상위 결과 대비 거리 기준으로 관련 없는 정책은 걸러냄 ("전국/타지역" 키워드 입력 시 전체 검색)
- **회원 / 세션 관리** — 회원가입, 로그인, 지역 정보 수정(DB 기반 시/도 · 시군구 선택), 대화 기록 저장
- **관리자 페이지** — 회원 목록 조회 및 탈퇴 처리
- **자동 갱신 배치** — APScheduler로 매주 월요일 03:00 벡터 인덱스 재구축
- **UI** — 즐겨찾기, 다크 모드, 모바일 반응형

## 기술 스택

| 구분 | 사용 기술 |
| --- | --- |
| Backend | Python, Flask, APScheduler |
| Database | MySQL / MariaDB, ChromaDB (Vector DB) |
| AI | Sentence-Transformers, Groq API (GPT-OSS 20B) |
| Frontend | HTML, CSS, Vanilla JS |
| Data | 공공데이터포털 복지서비스 API |

## 동작 흐름

```
사용자 질문
   │
   ▼
[rag.py]   질문 임베딩 → ChromaDB에서 시군구/시도/전국 그룹별 유사 정책 검색 후 병합
   │
   ▼
[llm.py]   검색 결과 + 최근 대화를 컨텍스트로 Groq API 호출 → JSON 카드 답변
   │
   ▼
[script.js] 카드 UI 렌더링
```

## 프로젝트 구조

```
├── app.py            # Flask 서버 · 라우팅 · 주간 배치 스케줄러
├── db.py             # MySQL 접근 계층 (회원, 대화 기록)
├── rag.py            # 임베딩 · ChromaDB 인덱스 구축/검색
├── llm.py            # Groq API 호출 · 프롬프트 · JSON 파싱
├── config.py         # 환경변수(.env) 로드
├── importPublic.py   # 중앙부처 복지서비스 데이터 수집
├── importLocal.py    # 지자체 복지서비스 데이터 수집
├── check.py          # Groq 사용 가능 모델 확인용 스크립트
├── schema.sql        # DB 테이블 스키마
├── index.html · script.js · style.css · media.css
└── .env.example      # 환경변수 템플릿
```

## 실행 방법

```bash
# 1. 가상환경 & 패키지 설치
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env           # 이후 .env 에 DB 정보와 API 키 입력

# 3. DB 스키마 생성
mysql -u root -p < schema.sql

# 4. 복지 데이터 수집 (최초 1회, 공공데이터포털 API 키 필요)
python importPublic.py
python importLocal.py

# 5. 서버 실행 (최초 실행 시 벡터 인덱스 자동 생성)
python app.py
```

브라우저에서 `http://localhost:5000` 접속.

## 환경변수

| 이름 | 설명 |
| --- | --- |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 접속 정보 |
| `GROQ_API_KEY` | [Groq](https://console.groq.com/keys) API 키 |
| `WELFARE_API_KEY` | [공공데이터포털](https://www.data.go.kr) 복지서비스 API 인증키 |
| `FLASK_SECRET_KEY` | Flask 세션 서명 키 |
| `FLASK_DEBUG` | `true` 시 디버그 모드 |
