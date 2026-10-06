import os
import chromadb
from sentence_transformers import SentenceTransformer
from db import get_connection

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name="welfare_policies")
model = SentenceTransformer("jhgan/ko-sroberta-multitask")

def extract_keywords(text):
    return text.strip()

# 지역 검색 시 그룹별 최소 포함 개수 (시군구 / 시도 공통 / 전국)
QUOTA_LOCAL, QUOTA_SIDO, QUOTA_NATIONAL = 3, 2, 2
# 최상위 결과 거리 대비 허용 배율 (이보다 멀면 관련 없는 정책으로 보고 제외)
RELEVANCE_RATIO = 1.5
# 거리 기준으로 너무 적게 남을 때 보장할 최소 결과 수
MIN_RESULTS = 5
SIDO_POOL_SIZE = 50

def _query(query_embedding, n_results, where=None):
    results = collection.query(query_embeddings=query_embedding, n_results=n_results, where=where)
    metadatas = results['metadatas'][0] if results['metadatas'] else []
    distances = results['distances'][0] if results['distances'] else []
    return list(zip(distances, metadatas))

def _matches_sgg(sgg_nm, tokens):
    # '강남' 처럼 시/군/구 접미사 없이 저장된 이전 입력값도 매칭
    return any(t == sgg_nm or (len(t) >= 2 and t == sgg_nm[:-1]) for t in tokens)

def _is_sido_wide(sgg_nm):
    # 시/군/구 단위가 아닌 항목(빈 값, '-', 교육청 등)은 시도 전체 대상
    return not sgg_nm or not sgg_nm.endswith(("시", "군", "구"))

def search_welfare_rag(query, top_k=7, region=""):
    if collection.count() == 0:
        build_index()

    keywords = extract_keywords(query)
    query_embedding = model.encode([keywords]).tolist()

    parts = region.split() if region else []
    if not parts:
        return [m for _, m in _query(query_embedding, top_k)]

    sido, sgg_tokens = parts[0], parts[1:]
    try:
        national = _query(query_embedding, top_k, {"ctpvNm": ""})
        sido_pool = _query(query_embedding, SIDO_POOL_SIZE, {"ctpvNm": sido})
    except Exception as e:
        print(f"[DEBUG] 지역 필터 오류: {e}")
        return [m for _, m in _query(query_embedding, top_k)]

    # 다른 시군구 전용 정책은 신청 대상이 아니므로 제외
    local = [(d, m) for d, m in sido_pool if m["sggNm"] and _matches_sgg(m["sggNm"], sgg_tokens)]
    sido_wide = [(d, m) for d, m in sido_pool if _is_sido_wide(m["sggNm"])]

    all_candidates = local + sido_wide + national
    if not all_candidates:
        return []
    cutoff = min(d for d, _ in all_candidates) * RELEVANCE_RATIO

    groups = (("시군구", local, QUOTA_LOCAL), ("시도", sido_wide, QUOTA_SIDO), ("전국", national, QUOTA_NATIONAL))
    picked, seen = [], set()
    def add(label, d, m, limit=cutoff):
        if len(picked) < top_k and d <= limit and m["servNm"] not in seen:
            seen.add(m["servNm"])
            picked.append((label, m))

    for label, group, quota in groups:
        for d, m in group[:quota]:
            add(label, d, m)
    rest = sorted(((d, label, m) for label, group, _ in groups for d, m in group), key=lambda x: x[0])
    for d, label, m in rest:
        add(label, d, m)
    for d, label, m in rest:
        if len(picked) >= MIN_RESULTS:
            break
        add(label, d, m, limit=float("inf"))

    counts = {label: sum(1 for l, _ in picked if l == label) for label, _, _ in groups}
    print(f"[DEBUG] {region} 검색 결과: " + " / ".join(f"{k} {v}개" for k, v in counts.items()))
    return [m for _, m in picked]

def build_index():
    if collection.count() > 0:
        print(f"[ChromaDB] 벡터 인덱스 이미 존재 ({collection.count()}개), 스킵합니다.")
        return
    print("[ChromaDB] 벡터 인덱스 구축을 시작합니다...")
    sql = """
        SELECT s.servId, s.servNm, s.servDgst, s.jurOrgNm,
               s.servDtlLink, s.onapPsbltYn, s.is_hidden_gem,
               s.ctpvNm, s.sggNm,
               d.tgtrDtlCn, d.alwServCn, d.slctCritCn, d.aplyMtdCn
        FROM servList s
        LEFT JOIN servDetail d ON s.servId = d.servId
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()

                ids, documents, metadatas = [], [], []

                for r in rows:
                    text_content = " ".join(filter(None, [
                        r.get('servNm', ''),
                        r.get('servDgst', ''),
                        r.get('tgtrDtlCn', ''),
                        r.get('ctpvNm', ''),
                        r.get('sggNm', '')
                    ]))
                    ids.append(str(r['servId']))
                    documents.append(text_content[:500])
                    metadatas.append({
                        "servNm": r.get('servNm') or '',
                        "jurOrgNm": r.get('jurOrgNm') or '',
                        "servDgst": (r.get('servDgst') or '')[:300],
                        "tgtrDtlCn": (r.get('tgtrDtlCn') or '')[:300],
                        "alwServCn": (r.get('alwServCn') or '')[:300],
                        "slctCritCn": (r.get('slctCritCn') or '')[:300],
                        "aplyMtdCn": (r.get('aplyMtdCn') or '')[:300],
                        "servDtlLink": r.get('servDtlLink') or '',
                        "onapPsbltYn": r.get('onapPsbltYn') or '',
                        "ctpvNm": (r.get('ctpvNm') or '').strip(),
                        "sggNm": (r.get('sggNm') or '').strip(),
                        "is_hidden_gem": str(r.get('is_hidden_gem') or '0')
                    })

                if documents:
                    vector_embeddings = model.encode(documents, show_progress_bar=True).tolist()
                    collection.add(ids=ids, embeddings=vector_embeddings, documents=documents, metadatas=metadatas)
                print(f"[ChromaDB] 총 {collection.count()}개의 복지 정책 인덱싱 완료!")
    except Exception as e:
        print(f"🚨 [ChromaDB 빌드 에러] {e}")

def rebuild_index():
    print("[ChromaDB] 최신 데이터 동기화를 위해 기존 인덱스를 초기화합니다...")
    global client, collection
    try:
        client.delete_collection(name="welfare_policies")
    except:
        pass
    collection = client.get_or_create_collection(name="welfare_policies")
    build_index()