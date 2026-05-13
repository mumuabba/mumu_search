import requests
import urllib3

# SSL 경고 숨기기
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_excel():
    print("🚀 식약처(식품안전나라) 최신 엑셀 수집 시작...")
    url = "https://www.foodsafetykorea.go.kr/portal/petKorea/downloadExcel.do"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.foodsafetykorea.go.kr/portal/petKorea.do"
    }
    
    try:
        response = requests.post(url, headers=headers, verify=False)
        if response.status_code == 200 and len(response.content) > 1000:
            with open("data.xlsx", "wb") as f:
                f.write(response.content)
            print("✅ 최신 data.xlsx 다운로드 완벽 성공!")
        else:
            print(f"❌ 다운로드 실패 (상태코드: {response.status_code})")
            raise Exception("다운로드 파일 용량 부족 또는 서버 에러")
    except Exception as e:
        print(f"❌ 크롤링 중 에러 발생: {e}")
        raise e

if __name__ == "__main__":
    download_excel()