import requests
import json
import os
from datetime import datetime
import time

auth_key = os.environ.get("AUTH_KEY")
CACHE_FILE = "pet_data_cache.json"

def auto_sync_all():
    service_id = "I1200"
    parsed_list = []
    start_idx = 1
    page_size = 1000 
    
    print(f"🚀 {datetime.now()} - 전국 식당 전수 조사 시작!")

    while True:
        url = f"http://openapi.foodsafetykorea.go.kr/api/{auth_key}/{service_id}/json/{start_idx}/{start_idx + page_size - 1}"
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            rows = data.get(service_id, {}).get('row', [])
            
            if not rows: break
            
            for r in rows:
                if r.get("PET_OUTIN_YN") == "Y" or r.get("ANSIM_PET_YN") == "Y":
                    parsed_list.append({
                        "업소명": r.get("BSSH_NM"),
                        "상세주소": r.get("LOCP_ADDR"),
                        "수집날짜": datetime.now().strftime("%Y-%m-%d")
                    })
            
            if start_idx % 10000 == 1:
                print(f"📊 {start_idx}번째 데이터 분석 중... (발견: {len(parsed_list)}개)")
            
            start_idx += page_size
            time.sleep(0.1)
        except Exception as e:
            print(f"⚠️ 오류 발생: {e}")
            time.sleep(5)
            continue
    
    # 최소 검증 장치 (수집 데이터가 너무 적으면 저장 안 함)
    if len(parsed_list) > 100: 
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(parsed_list, f, ensure_ascii=False, indent=4)
        print(f"🎉 총 {len(parsed_list)}개 저장 완료.")

if __name__ == "__main__":
    auto_sync_all()