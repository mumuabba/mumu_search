import os
import time

import requests

# 식약처 '반려동물 동반가능 업소현황' 페이지가 스스로 호출하는 것과 동일한 엔드포인트.
# 이 데이터에 대한 공개 API는 없으며, 엑셀 다운로드가 유일한 공식 경로다.
URL = "https://www.foodsafetykorea.go.kr/portal/petKorea/downloadExcel.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.foodsafetykorea.go.kr/portal/petKorea.do",
}

# 식약처 방화벽이 일부 IP 대역의 접속을 응답 없이 버린다(ConnectTimeout). 한국에서는
# 100% 붙지만 GitHub Actions 러너에서는 약 1/3만 성공한다. 같은 IP로 재시도해봐야
# 똑같이 막히므로, CI에서는 재시도를 1회로 줄이고 대신 러너를 여러 대 띄워
# 서로 다른 IP로 시도한다(update_data.yml의 matrix 참고).
TIMEOUT = int(os.environ.get("MUMU_TIMEOUT", "60"))
RETRIES = int(os.environ.get("MUMU_RETRIES", "3"))
BACKOFF = 5
MIN_BYTES = 1000
XLSX_MAGIC = b"PK\x03\x04"


def fetch():
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            print(f"🚀 식약처 최신 엑셀 수집 시도 {attempt}/{RETRIES}...")
            response = requests.post(URL, headers=HEADERS, timeout=TIMEOUT)

            if response.status_code != 200:
                raise Exception(f"서버 응답 코드 {response.status_code}")
            if len(response.content) < MIN_BYTES:
                raise Exception(f"파일 용량 부족 ({len(response.content)} bytes)")
            # 서버가 에러 페이지(HTML)를 200으로 내려주는 경우를 걸러낸다.
            if not response.content.startswith(XLSX_MAGIC):
                raise Exception(f"엑셀 파일이 아님 (선두 바이트: {response.content[:4]!r})")

            return response.content

        except Exception as e:
            last_error = e
            print(f"⚠️  시도 {attempt} 실패: {e}")
            if attempt < RETRIES:
                wait = BACKOFF * attempt
                print(f"   {wait}초 후 재시도...")
                time.sleep(wait)

    raise Exception(f"{RETRIES}회 모두 실패. 마지막 에러: {last_error}")


def download_excel():
    content = fetch()
    with open("data.xlsx", "wb") as f:
        f.write(content)
    print(f"✅ data.xlsx 저장 완료 ({len(content):,} bytes)")


if __name__ == "__main__":
    download_excel()
