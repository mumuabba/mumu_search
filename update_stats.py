import pandas as pd
import json
import os

def update_comparison():
    # 1. 방금 다운로드된 엑셀 로드
    df = pd.read_excel("data.xlsx")
    new_count = len(df)
    
    # 2. 어제 기록해둔 메모지(stats.json) 읽기
    old_count = new_count
    if os.path.exists("stats.json"):
        try:
            with open("stats.json", "r", encoding="utf-8") as f:
                stats = json.load(f)
                old_count = stats.get("total_count", new_count)
        except: pass
    
    # 3. 증감 계산
    diff = new_count - old_count
    
    # 4. 오늘의 최신 결과를 새 메모지로 덮어쓰기
    with open("stats.json", "w", encoding="utf-8") as f:
        json.dump({"total_count": new_count, "diff": diff}, f, ensure_ascii=False)
        
    print(f"📊 통계 갱신 완료: 총 {new_count:,}개 (전일대비: {diff:+}개)")

if __name__ == "__main__":
    update_comparison()