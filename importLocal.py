import requests
import xml.etree.ElementTree as ET
import pymysql
from config import WELFARE_API_KEY, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

API_KEY    = WELFARE_API_KEY
LIST_URL   = "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist"
DETAIL_URL = "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfaredetailed"

conn = pymysql.connect(
    host     = DB_HOST,
    port     = DB_PORT,
    user     = DB_USER,
    password = DB_PASSWORD,
    db       = DB_NAME,
    charset  = "utf8mb4"
)
cursor = conn.cursor()

def fetch_list():
    params = {
        "serviceKey": API_KEY,
        "pageNo"    : "1",
        "numOfRows" : "1",
    }
    response    = requests.get(LIST_URL, params=params)
    root        = ET.fromstring(response.text)
    total       = int(root.findtext("totalCount"))
    total_pages = (total // 500) + 1
    print(f"전체 {total}건 / {total_pages}페이지")

    serv_ids = []
    count    = 0

    for page in range(1, total_pages + 1):
        print(f"페이지 {page}/{total_pages} 처리 중...")
        params = {
            "serviceKey": API_KEY,
            "pageNo"    : str(page),
            "numOfRows" : "500",
        }
        response = requests.get(LIST_URL, params=params)

        if response.status_code == 429:
            print("호출 한도 초과 - 중단")
            break

        try:
            root = ET.fromstring(response.text)
        except Exception as e:
            print(f"XML 파싱 오류: {e}")
            continue

        for item in root.iter("servList"):
            serv_id = item.findtext("servId")
            serv_ids.append(serv_id)

            cursor.execute("""
                INSERT INTO servList (
                    servId, servNm, servDgst,
                    sprtCycNm, srvPvsnNm, inqNum,
                    lifeArray, intrsThemaArray, trgterIndvdlArray,
                    jurMnofNm, jurOrgNm,
                    ctpvNm, sggNm, source, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, 'local', NOW()
                )
                ON DUPLICATE KEY UPDATE
                    servNm=VALUES(servNm),
                    updated_at=NOW()
            """, (
                serv_id,
                item.findtext("servNm"),
                item.findtext("servDgst"),
                item.findtext("sprtCycNm"),
                item.findtext("srvPvsnNm"),
                item.findtext("inqNum") or 0,
                item.findtext("lifeNmArray"),
                item.findtext("intrsThemaNmArray"),
                item.findtext("trgterIndvdlNmArray"),
                item.findtext("bizChrDeptNm"),
                item.findtext("sggNm"),
                item.findtext("ctpvNm"),
                item.findtext("sggNm"),
            ))
            count += 1

        conn.commit()
        print(f"  {count}건 저장됨")

    print(f"목록 총 {count}건 저장 완료")
    return serv_ids


def fetch_detail(serv_id):
    params = {
        "serviceKey": API_KEY,
        "servId"    : serv_id,
    }
    response = requests.get(DETAIL_URL, params=params)

    if response.status_code == 429:
        print("호출 한도 초과 - 중단")
        return False

    if response.status_code != 200:
        print(f"실패: {serv_id} ({response.status_code})")
        return True

    try:
        root = ET.fromstring(response.text)
    except Exception as e:
        print(f"XML 파싱 오류: {serv_id} - {e}")
        return True

    dtl = root

    cursor.execute("""
        INSERT INTO servDetail (
            servId, servNm, jurMnofNm,
            tgtrDtlCn, slctCritCn, alwServCn,
            crtrYr, wlfareInfoOutlCn,
            sprtCycNm, srvPvsnNm, lifeArray,
            trgterIndvdlArray, intrsThemaArray,
            sprtTrgtCn, aplyMtdCn, aplyMtdNm,
            enfcBgngYmd, enfcEndYmd,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        ON DUPLICATE KEY UPDATE
            alwServCn  = VALUES(alwServCn),
            slctCritCn = VALUES(slctCritCn),
            sprtTrgtCn = VALUES(sprtTrgtCn),
            aplyMtdCn  = VALUES(aplyMtdCn),
            updated_at = NOW()
    """, (
        serv_id,
        dtl.findtext("servNm") or "",
        dtl.findtext("bizChrDeptNm") or "",
        dtl.findtext("sprtTrgtCn") or "",
        dtl.findtext("slctCritCn") or "",
        dtl.findtext("alwServCn") or "",
        dtl.findtext("lastModYmd") or "",
        dtl.findtext("servDgst") or "",
        dtl.findtext("sprtCycNm") or "",
        dtl.findtext("srvPvsnNm") or "",
        dtl.findtext("lifeNmArray") or "",
        dtl.findtext("trgterIndvdlNmArray") or "",
        dtl.findtext("intrsThemaNmArray") or "",
        dtl.findtext("sprtTrgtCn") or "",
        dtl.findtext("aplyMtdCn") or "",
        dtl.findtext("aplyMtdNm") or "",
        dtl.findtext("enfcBgngYmd") or "",
        dtl.findtext("enfcEndYmd") or "",
    ))

    for item in root.iter("inqplCtadrList"):
        cursor.execute("""
            INSERT IGNORE INTO inqplCtadrList
                (servId, servSeCode, servSeDetailNm, servSeDetailLink)
            VALUES (%s, %s, %s, %s)
        """, (
            serv_id,
            item.findtext("wlfareInfoDtlCd"),
            item.findtext("wlfareInfoReldNm"),
            item.findtext("wlfareInfoReldCn"),
        ))

    for item in root.iter("inqplHmpgReldList"):
        cursor.execute("""
            INSERT IGNORE INTO inqplHmpgReldList
                (servId, servSeCode, servSeDetailNm, servSeDetailLink)
            VALUES (%s, %s, %s, %s)
        """, (
            serv_id,
            item.findtext("wlfareInfoDtlCd"),
            item.findtext("wlfareInfoReldNm"),
            item.findtext("wlfareInfoReldCn"),
        ))

    for item in root.iter("baslawList"):
        cursor.execute("""
            INSERT IGNORE INTO baslawList
                (servId, servSeCode, servSeDetailNm)
            VALUES (%s, %s, %s)
        """, (
            serv_id,
            item.findtext("wlfareInfoDtlCd"),
            item.findtext("wlfareInfoReldNm"),
        ))

    for item in root.iter("basfrmList"):
        cursor.execute("""
            INSERT IGNORE INTO basfrmList
                (servId, servSeCode, servSeDetailNm, servSeDetailLink)
            VALUES (%s, %s, %s, %s)
        """, (
            serv_id,
            item.findtext("wlfareInfoDtlCd"),
            item.findtext("wlfareInfoReldNm"),
            item.findtext("wlfareInfoReldCn"),
        ))

    conn.commit()
    return True


if __name__ == "__main__":
    cursor.execute("""
        SELECT s.servId FROM servList s
        LEFT JOIN servDetail d ON s.servId = d.servId
        WHERE s.source = 'local'
        AND d.servId IS NULL
    """)
    serv_ids = [row[0] for row in cursor.fetchall()]

    print(f"지자체 상세조회 미완료 {len(serv_ids)}건 시작...")
    for i, serv_id in enumerate(serv_ids):
        print(f"{i+1}/{len(serv_ids)} - {serv_id}")
        ok = fetch_detail(serv_id)
        if not ok:
            break

    cursor.close()
    conn.close()
    print("완료")