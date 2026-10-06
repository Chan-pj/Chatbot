import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import xml.etree.ElementTree as ET
import pymysql
from config import WELFARE_API_KEY, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

API_KEY    = WELFARE_API_KEY
LIST_URL   = "http://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfarelistV001"
DETAIL_URL = "http://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfaredetailedV001"

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
        "serviceKey" : API_KEY,
        "callTp"     : "L",
        "pageNo"     : "1",
        "numOfRows"  : "500",
        "srchKeyCode": "003",
    }
    response = requests.get(LIST_URL, params=params)

    if response.status_code != 200:
        print(f"목록조회 실패: {response.status_code}")
        return []

    root  = ET.fromstring(response.text)
    count = 0
    serv_ids = []

    for item in root.iter("servList"):
        serv_id = item.findtext("servId")
        serv_ids.append(serv_id)

        cursor.execute("""
            INSERT INTO servList (
                servId, servNm, jurMnofNm, jurOrgNm,
                servDgst, servDtlLink, sprtCycNm, srvPvsnNm,
                onapPsbltYn, rprsCtadr, inqNum,
                lifeArray, intrsThemaArray, trgterIndvdlArray, svcfrstRegTs
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                servNm     = VALUES(servNm),
                updated_at = NOW()
        """, (
            serv_id,
            item.findtext("servNm"),
            item.findtext("jurMnofNm"),
            item.findtext("jurOrgNm"),
            item.findtext("servDgst"),
            item.findtext("servDtlLink"),
            item.findtext("sprtCycNm"),
            item.findtext("srvPvsnNm"),
            item.findtext("onapPsbltYn"),
            item.findtext("rprsCtadr"),
            item.findtext("inqNum") or 0,
            item.findtext("lifeArray"),
            item.findtext("intrsThemaArray"),
            item.findtext("trgterIndvdlArray"),
            item.findtext("svcfrstRegTs"),
        ))
        count += 1

    conn.commit()
    print(f"목록 {count}건 저장 완료")
    return serv_ids


def fetch_detail(serv_id):
    params = {
        "serviceKey": API_KEY,
        "callTp"    : "D",
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
            crtrYr, rprsCtadr, wlfareInfoOutlCn,
            sprtCycNm, srvPvsnNm, lifeArray,
            trgterIndvdlArray, intrsThemaArray
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            tgtrDtlCn        = VALUES(tgtrDtlCn),
            slctCritCn       = VALUES(slctCritCn),
            alwServCn        = VALUES(alwServCn),
            wlfareInfoOutlCn = VALUES(wlfareInfoOutlCn),
            crtrYr           = VALUES(crtrYr),
            updated_at       = NOW()
    """, (
        serv_id,
        dtl.findtext("servNm") or "",
        dtl.findtext("jurMnofNm") or "",
        dtl.findtext("tgtrDtlCn") or "",
        dtl.findtext("slctCritCn") or "",
        dtl.findtext("alwServCn") or "",
        dtl.findtext("crtrYr") or "",
        dtl.findtext("rprsCtadr") or "",
        dtl.findtext("wlfareInfoOutlCn") or "",
        dtl.findtext("sprtCycNm") or "",
        dtl.findtext("srvPvsnNm") or "",
        dtl.findtext("lifeArray") or "",
        dtl.findtext("trgterIndvdlArray") or "",
        dtl.findtext("intrsThemaArray") or "",
    ))

    for item in root.iter("applmetList"):
        cursor.execute("""
            INSERT IGNORE INTO applmetList
                (servId, servSeCode, servSeDetailNm, servSeDetailLink)
            VALUES (%s, %s, %s, %s)
        """, (
            serv_id,
            item.findtext("servSeCode"),
            item.findtext("servSeDetailNm"),
            item.findtext("servSeDetailLink"),
        ))

    for item in root.iter("inqplCtadrList"):
        cursor.execute("""
            INSERT IGNORE INTO inqplCtadrList
                (servId, servSeCode, servSeDetailNm, servSeDetailLink)
            VALUES (%s, %s, %s, %s)
        """, (
            serv_id,
            item.findtext("servSeCode"),
            item.findtext("servSeDetailNm"),
            item.findtext("servSeDetailLink"),
        ))

    for item in root.iter("inqplHmpgReldList"):
        cursor.execute("""
            INSERT IGNORE INTO inqplHmpgReldList
                (servId, servSeCode, servSeDetailNm, servSeDetailLink)
            VALUES (%s, %s, %s, %s)
        """, (
            serv_id,
            item.findtext("servSeCode"),
            item.findtext("servSeDetailNm"),
            item.findtext("servSeDetailLink"),
        ))

    for item in root.iter("basfrmList"):
        cursor.execute("""
            INSERT IGNORE INTO basfrmList
                (servId, servSeCode, servSeDetailNm, servSeDetailLink)
            VALUES (%s, %s, %s, %s)
        """, (
            serv_id,
            item.findtext("servSeCode"),
            item.findtext("servSeDetailNm"),
            item.findtext("servSeDetailLink"),
        ))

    for item in root.iter("baslawList"):
        cursor.execute("""
            INSERT IGNORE INTO baslawList
                (servId, servSeCode, servSeDetailNm)
            VALUES (%s, %s, %s)
        """, (
            serv_id,
            item.findtext("servSeCode"),
            item.findtext("servSeDetailNm"),
        ))

    conn.commit()
    return True


if __name__ == "__main__":
    # 1단계: 목록조회
    print("목록조회 시작...")
    fetch_list()

    # 2단계: 상세조회 (미완료 건만)
    cursor.execute("""
        SELECT s.servId FROM servList s
        LEFT JOIN servDetail d ON s.servId = d.servId
        WHERE d.servId IS NULL
        AND s.source = 'central'
    """)
    serv_ids = [row[0] for row in cursor.fetchall()]

    print(f"미완료 {len(serv_ids)}건 상세조회 시작...")
    for i, serv_id in enumerate(serv_ids):
        print(f"{i+1}/{len(serv_ids)} - {serv_id}")
        ok = fetch_detail(serv_id)
        if not ok:
            break

    cursor.close()
    conn.close()
    print("완료")