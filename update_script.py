import requests
import json
import os
from datetime import datetime

# 1. 설정 (인증키는 깃허브 Secrets에서 가져옵니다)
AUTH_KEY = os.environ.get("AUTH_KEY")
BASE_URL = "http://openapi.foodsafetykorea.go.kr/api"
SERVICE_ID = "I2710"  # 동물동반 가능 업소 정보 서비스 ID

def fetch_pet_friendly_data():
    all_data = []
    start_idx = 1
    end_idx = 1000  # 한 번에 가져올 데이터 양
    
    print(f"[{datetime.now()}] 데이터 수집을 시작합니다...")

    while True:
        # API 호출 주소 생성
        url = f"{BASE_URL}/{AUTH_KEY}/{SERVICE_ID}/json/{start_idx}/{end_idx}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            # 데이터 존재 여부 확인
            if SERVICE_ID in data and "row" in data[SERVICE_ID]:
                rows = data[SERVICE_ID]["row"]
                
                for item in rows:
                    # 💡 [핵심 필터] 영업상태가 '영업/정상'인 경우만 수집합니다.
                    # 행정 지연으로 인한 폐업지 누락을 최소화하기 위한 1차 필터링입니다.
                    state = item.get('TRD_STATE_NM', '')
                    
                    if state == '영업/정상':
                        all_data.append({
                            '업소명': item.get('BPLC_NM'),
                            '상세주소': item.get('RDN_WH_ADDR') or item.get('ADDR'),
                            '전화번호': item.get('TELNO'),
                            '영업상태': state,
                            '수집날짜': datetime.now().strftime("%Y-%m-%d")
                        })
                
                # 다음 페이지 확인
                if len(rows) < 1000:
                    break
                start_idx += 1000
                end_idx += 1000
            else:
                break
                
        except Exception as e:
            print(f"오류 발생: {e}")
            break

    # 2. 결과 저장 (앱에서 사용할 캐시 파일 생성)
    if all_data:
        with open("pet_data_cache.json", "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        print(f"성공: 총 {len(all_data)}개의 영업 중인 업소를 저장했습니다.")
    else:
        print("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    fetch_pet_friendly_data()
