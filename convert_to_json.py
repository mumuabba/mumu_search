import json

import pandas as pd

# 앱이 반드시 필요로 하는 컬럼. 식약처가 엑셀 서식을 바꾸면 여기서 즉시 실패해야
# 깨진 데이터가 사이트로 배포되는 것을 막을 수 있다.
REQUIRED_COLUMNS = ["업소명", "업소주소"]


def convert():
    print("🍳 엑셀을 웹사이트용 JSON 캐시로 변환 시작...")
    df = pd.read_excel("data.xlsx")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise Exception(
            f"엑셀에 필수 컬럼이 없습니다: {missing} / 실제 컬럼: {list(df.columns)}"
        )
    if df.empty:
        raise Exception("엑셀에 데이터가 한 건도 없습니다.")

    # 수집 시각은 stats.json에만 기록한다. 여기에 넣으면 데이터가 그대로여도
    # 캐시 파일이 매일 달라져서 워크플로의 '변경 시에만 커밋' 방어가 무력화된다.
    records = df.to_dict(orient="records")
    with open("pet_data_cache.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)

    print(f"✅ 캐시 파일(pet_data_cache.json) 굽기 완료! ({len(records):,}건)")


if __name__ == "__main__":
    convert()
