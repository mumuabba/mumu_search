import pandas as pd
import json
from datetime import datetime

def convert():
    print("🍳 엑셀을 웹사이트용 JSON 캐시로 변환 시작...")
    df = pd.read_excel("data.xlsx")
    
    # 화면 출력용 수집날짜 추가
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    df['수집날짜'] = now_str
    
    # 무무 탐색기(스트림릿)가 즉시 읽을 수 있는 형태로 저장
    records = df.to_dict(orient="records")
    with open("pet_data_cache.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
        
    print("✅ 캐시 파일(pet_data_cache.json) 굽기 완료!")

if __name__ == "__main__":
    convert()