import requests
import json
import os
from datetime import datetime
import time

# 깃허브 Secret에 등록한 API 키를 가져옵니다.
auth_key = os.environ.get("AUTH_KEY")
CACHE_FILE = "pet_data_cache.json"

def auto_sync_all():
    # 💡 핵심 수정: 반려동물 동반 가능 음식점 전용 서비스 ID
    service_id = "I2710" 
    parsed_list = []
    start_idx = 1
    page_size = 1000 
    
    print(f"🚀 {datetime.now()} - 반려동물 동반 식당 전수 조사 시작!")

    while True:
        # 식약처 API 호출 URL
        url = f"http://openapi.foodsafetykorea.go.kr/api/{auth_key}/{service_id}/json/{start_idx}/{start_idx + page_size - 1}"
        
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            # API 응답 구조에 맞춰 데이터 추출
            result = data.get(service_id, {})
            rows = result.get('row', [])
            
            # 더 이상 가져올 데이터가 없으면 종료
            if not rows: 
                print(f"🏁 더 이상 가져올 데이터가 없습니다. (최종 인덱스: {start_idx})")
                break
            
            for r in rows:
                # I2710 서비스는 이미 '동반 가능' 업체만 들어있으므로 별도 Y/N 체크 없이 수집
                # 만약 '영업/정상' 업체만 골라내고 싶다면 아래 필드를 확인하세요.
                status = r.get("TRD_STATE_NM", "영업/정상")
                
                if "영업" in status:
                    parsed_list.append({
                        "업소명": r.get("BSSH_NM"),
                        "상세주소": r.get("ADDR"),  # I2710은 ADDR 필드를 사용합니다.
                        "수집날짜": datetime.now().strftime("%Y-%m-%d")
                    })
            
            # 진행 상황 출력 (너무 자주 찍히지 않게 5000개 단위로)
            if start_idx % 5000 == 1:
                print(f"📊 {start_idx}번째 데이터 분석 중... (현재 발견: {len(parsed_list)}개)")
            
            start_idx += page_size
            time.sleep(0.1) # 서버 부하 방지
            
        except Exception as e:
            print(f"⚠️ 오류 발생: {e}")
            time.sleep(5)
            continue
    
    # 데이터 저장 (최소 10개 이상 발견 시 저장 - I2710은 전체 수가 상대적으로 적음)
    if len(parsed_list) > 10: 
        # 중복 제거 (업소명과 주소가 같은 경우)
        df_temp = json.dumps(parsed_list, ensure_ascii=False) # 임시 변환
        
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(parsed_list, f, ensure_ascii=False, indent=4)
        print(f"🎉 전국의 반려동물 동반 식당 총 {len(parsed_list)}개 저장 완료!")
    else:
        print("❌ 수집된 데이터가 너무 적어 파일을 업데이트하지 않았습니다.")

if __name__ == "__main__":
    auto_sync_all()
