import requests
import time
import json
from config import GROQ_API_KEY

def ask_gemini(user_message, db_results, chat_history=None):
    context = ""
    for r in db_results:
        servNm = r.get('servNm', '').strip()
        if not servNm: continue

        context += f"- 서비스명: {servNm}\n"

        def clean_text(text, max_len=150):
            if not text: return ""
            cleaned = " ".join(text.split())
            return cleaned[:max_len] + ("..." if len(cleaned) > max_len else "")

        servDgst = clean_text(r.get('servDgst', ''))
        if servDgst: context += f"   내용: {servDgst}\n"

        tgtrDtlCn = clean_text(r.get('tgtrDtlCn', ''))
        if tgtrDtlCn: context += f"   대상: {tgtrDtlCn}\n"

        alwServCn = clean_text(r.get('alwServCn', ''))
        if alwServCn: context += f"   지원내용: {alwServCn}\n"

        jurOrgNm = r.get('jurOrgNm', '').strip()
        if jurOrgNm: context += f"   기관: {jurOrgNm}\n"

        region = " ".join(filter(None, [r.get('ctpvNm', '').strip(), r.get('sggNm', '').strip().strip('-')]))
        context += f"   지역: {region if region else '전국'}\n"

        aplyMtdCn = clean_text(r.get('aplyMtdCn', ''), max_len=100)
        if aplyMtdCn: context += f"   신청방법: {aplyMtdCn}\n"

        onapPsbltYn = r.get('onapPsbltYn', '').strip()
        if onapPsbltYn: context += f"   온라인신청: {onapPsbltYn}\n"

        servDtlLink = clean_text(r.get('servDtlLink', ''), max_len=200)
        context += f"   복지로링크: {servDtlLink if servDtlLink else '없음'}\n"

        context += "\n"

    system_prompt = f"""역할: 복지 정책 안내 챗봇 복복이
규칙:
- [복지 서비스 정보] 기반으로 답변. 질문에 맞는 정책이 하나라도 있으면 반드시 JSON 카드로 답변 (예외 메시지 금지)
- 반드시 한국어, 사용자에게 보이는 문구는 존댓말
- 이전 대화 내용을 기억하고 맥락에 맞게 답변
- [복지 서비스 정보]에 관련 정책이 전혀 없을 때만 {{"type":"text","message":"죄송합니다. 관련 정책을 찾지 못했습니다."}} 로 답변
- 카드는 최대 3개. 관련 정책이 여러 개면 반드시 2~3개 포함 (1개만 출력 금지)
- link 필드는 절대 빈 문자열 금지. 복지로링크가 없으면 'https://www.bokjiro.go.kr' 사용

반드시 아래 JSON 형식으로만 응답. 다른 설명, 텍스트, 마크다운 기호 절대 금지:
{{
  "type": "cards",
  "intro": "간단한 안내 문구 (1-2문장)",
  "cards": [
    {{
      "title": "서비스명",
      "org": "기관 필드 값 (없으면 유추 가능한 기관 입력)",
      "region": "지역 필드 값을 그대로 사용",
      "desc": "내용 요약 (2-3문장)",
      "target": "지원 대상",
      "support": "지원 내용",
      "how": "신청방법 필드 요약",
      "online": "온라인신청 필드 값 (Y 또는 N)",
      "link": "복지로링크 필드 값을 그대로 사용. 없으면 'https://www.bokjiro.go.kr'",
      "keyword": "서비스명을 그대로 사용 (복지로 검색창에 입력할 키워드)"
    }}
  ]
}}

[복지 서비스 정보]
{context}"""

    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        for h in chat_history[-2:]:
            role = "user" if h["role"] == "user" else "assistant"
            messages.append({"role": role, "content": h["message"]})
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "max_tokens": 2048,
        "reasoning_effort": "low",
        "temperature": 0.2
    }

    for attempt in range(3):
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
        data = res.json()
        rh = res.headers

        if "choices" in data:
            usage = data.get("usage", {})
            print(f"\n==================== [Groq API 상태 모니터링] ====================")
            print(f"[이번 요청 토큰] 입력: {usage.get('prompt_tokens', 0)} / 출력: {usage.get('completion_tokens', 0)} / 합계: {usage.get('total_tokens', 0)}")
            print(f"------------------------------------------------------------------")
            print(f"[분당 요청 한도(RPM)] 전체: {rh.get('x-ratelimit-limit-requests', '?')}회 / 남은 횟수: {rh.get('x-ratelimit-remaining-requests', '?')}회")
            print(f"[분당 토큰 한도(TPM)] 전체: {rh.get('x-ratelimit-limit-tokens', '?')}개 / 남은 토큰: {rh.get('x-ratelimit-remaining-tokens', '?')}개")
            print(f"==================================================================\n")

            raw = data["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            try:
                json.loads(raw)
                return raw
            except:
                print(f"[JSON 파싱 실패] raw 내용: {raw[:200]}")
                return json.dumps({"type": "text", "message": raw}, ensure_ascii=False)

        elif res.status_code == 429 or data.get("error", {}).get("code") == "rate_limit_exceeded":
            print(f"\n🚨 [Rate Limit 초과 발생!] 5초 대기 후 재시도...")
            print(f"[남은 토큰] {rh.get('x-ratelimit-remaining-tokens', '?')}개 / [남은 요청] {rh.get('x-ratelimit-remaining-requests', '?')}회")
            print(f"[리셋까지] 토큰: {rh.get('x-ratelimit-reset-tokens', '?')} / 요청: {rh.get('x-ratelimit-reset-requests', '?')}")
            print(f"[전체 에러 응답] {data}")
            print(f"[HTTP 상태코드] {res.status_code}")
            time.sleep(5)
        else:
            print("Groq API 오류 발생:", data)
            return json.dumps({"type": "text", "message": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}, ensure_ascii=False)

    return json.dumps({"type": "text", "message": "요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요."}, ensure_ascii=False)