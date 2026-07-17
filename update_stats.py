import json
import os
from datetime import datetime, timedelta, timezone

import pandas as pd

# GitHub Actions 러너는 UTC로 동작한다. 표시용 시각은 여기서 KST로 확정해서
# 저장한다. (예전에는 화면에서 +9시간을 더했는데, 로컬에서 돌리면 9시간이
# 두 번 더해지는 문제가 있었다.)
KST = timezone(timedelta(hours=9))


def update_comparison():
    df = pd.read_excel("data.xlsx")
    new_count = len(df)

    old_count = new_count
    if os.path.exists("stats.json"):
        try:
            with open("stats.json", "r", encoding="utf-8") as f:
                old_count = json.load(f).get("total_count", new_count)
        except Exception:
            pass

    diff = new_count - old_count

    stats = {
        "total_count": new_count,
        "diff": diff,
        "updated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
    }
    with open("stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False)

    print(f"📊 통계 갱신 완료: 총 {new_count:,}개 (전일대비: {diff:+}개)")


if __name__ == "__main__":
    update_comparison()
