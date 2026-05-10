import pandas as pd
import json
import os
from datetime import datetime

# 성훈님이 정하신 파일명
INPUT_FILE = 'data.xlsx' 
OUTPUT_FILE = 'pet_data_cache.json'

def convert_excel_to_json():
    try:
        # 파일 존재 여부 확인
        if not os.path.exists(INPUT_FILE):
            print(f"❌ '{INPUT_FILE}' 파일이 폴더에 없습니다. 파일명을 확인해 주세요!")
            return

        # 💡 엑셀 읽기 (엔진 명시)
        df = pd.read_excel(INPUT_FILE, engine='openpyxl')
        
        parsed_list = []
        
        for _, row in df.iterrows():
            # 성훈님 엑셀 컬럼명: 연번, 업소명, 업종, 지역, 업소주소
            parsed_list.append({
                "업소명": str(row['업소명']).strip(),
                "상세주소": str(row['업소주소']).strip(),
                "업종": str(row['업종']).strip(),
                "지역": str(row['지역']).strip(),
                "수집날짜": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

        # JSON 저장
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(parsed_list, f, ensure_ascii=False, indent=4)
        
        print(f"✅ 변환 성공! 총 {len(parsed_list)}개의 업소 정보가 JSON으로 변환되었습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    convert_excel_to_json()