from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from db import save_chat, get_chat_history, register_user, login_user, get_all_users, delete_user, get_regions
from rag import search_welfare_rag, build_index, rebuild_index
from llm import ask_gemini
from apscheduler.schedulers.background import BackgroundScheduler
import uuid
from datetime import datetime
from config import FLASK_SECRET_KEY, FLASK_DEBUG


app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# 세션 쿠키 설정
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # HTTPS 배포 시 True
app.config['SESSION_COOKIE_HTTPONLY'] = True

CORS(app, supports_credentials=True)

# 주간 벡터 인덱스 재구축 배치
def weekly_data_pipeline():
    print("\n[배치 스케줄러] 벡터 인덱스 재구축 시작...")
    try:
        rebuild_index()
        print("[배치 스케줄러] ChromaDB 벡터 인덱스 재구축 완료.\n")
    except Exception as e:
        print(f" [배치 에러] 벡터 인덱스 재구축 중 오류 발생: {e}\n")

scheduler = BackgroundScheduler()

# 매주 월요일 03:00
job = scheduler.add_job(weekly_data_pipeline, 'cron', day_of_week='mon', hour=3, minute=0)
scheduler.start()

if job.next_run_time:
    next_run = job.next_run_time
    now = datetime.now(next_run.tzinfo)
    time_remaining = next_run - now
    
    days = time_remaining.days
    hours = time_remaining.seconds // 3600
    minutes = (time_remaining.seconds % 3600) // 60
    
    print("\n  [스케줄러 디버깅 모니터링]")
    print(f"-> 다음 인덱스 재구축 예정일: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"-> 현재 남은 시간: {days}일 {hours}시간 {minutes}분 후에 인덱스가 재구축됩니다.")
    print("==================================================================\n")
else:
    print("\n [스케줄러 디버깅] 다음 예약된 작업 시간을 찾을 수 없습니다.\n")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# 새로고침 시 로그인 상태 복구
@app.route("/check-session", methods=["GET"])
def check_session():
    if "user_id" in session:
        return jsonify({
            "success": True,
            "username": session.get("username"),
            "role": session.get("role"),
            "region": session.get("region", "")
        })
    return jsonify({"success": False, "message": "로그인 정보가 없습니다."})

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    region = data.get("region", "").strip()
    if not username or not password:
        return jsonify({"success": False, "message": "아이디와 비밀번호를 입력하세요."})
    success = register_user(username, password, region)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "이미 사용 중인 아이디입니다."})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    user = login_user(username, password)
    print(f"[DEBUG] login_user 결과: {user}")
    if user:
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["region"] = user["region"] or ""
        return jsonify({"success": True, "username": user["username"], "role": user["role"], "region": user["region"] or ""})
    else:
        return jsonify({"success": False, "message": "아이디 또는 비밀번호가 틀렸습니다."})

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    data = request.json
    user_message = data.get("message", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    region = session.get("region", "")
    user_id = session.get("user_id")
    other_region_keywords = ["타지역", "다른 지역", "전국", "전체", "전국적으로"]
    use_region = region and region.strip() and not any(kw in user_message for kw in other_region_keywords)
    chat_history = get_chat_history(session_id)
    save_chat(session_id, "user", user_message, user_id)
    db_results = search_welfare_rag(user_message, region=region if use_region else "")
    print(f"\n[조회 결과] 검색된 정책 수: {len(db_results)}개")
    for idx, r in enumerate(db_results, 1):
        print(f"  {idx}. {r.get('servNm', '')} ({r.get('ctpvNm', '')} {r.get('sggNm', '')})")
    reply = ask_gemini(user_message, db_results, chat_history)
    save_chat(session_id, "bot", reply, user_id)
    
    return jsonify({"reply": reply, "session_id": session_id})

# 시도별 시군구 목록 (회원가입/지역 수정 드롭다운용)
_regions_cache = None

@app.route("/regions", methods=["GET"])
def regions():
    global _regions_cache
    if _regions_cache is None:
        _regions_cache = get_regions()
    return jsonify(_regions_cache)

@app.route("/update-region", methods=["POST"])
def update_region():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    
    data = request.json
    new_region = data.get("region", "").strip()
    user_id = session.get("user_id")
    
    sql = "UPDATE users SET region = %s WHERE id = %s"
    try:
        from db import get_connection
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (new_region, user_id))
                conn.commit()
        
        session["region"] = new_region
        return jsonify({"success": True, "region": new_region})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/admin/users", methods=["GET"])
def admin_users():
    print(f"[DEBUG] session role: {session.get('role')}, type: {type(session.get('role'))}")
    if int(session.get("role", 0)) != 2:
        return jsonify({"error": "권한 없음"}), 403
    users = get_all_users()
    return jsonify({"users": users})

@app.route("/admin/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    if int(session.get("role", 0)) != 2:
        return jsonify({"error": "권한 없음"}), 403
    delete_user(user_id)
    return jsonify({"success": True})


@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    print("벡터 인덱스 확인 중...")
    build_index()
    app.run(host="0.0.0.0", port=5000, debug=FLASK_DEBUG)