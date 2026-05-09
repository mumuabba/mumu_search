import streamlit as st
import requests
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime
from PIL import Image

# 1. 페이지 설정
st.set_page_config(page_title="무무 탐색기 - mumuabba", layout="wide")

# [헤더 레이아웃] 무무 사진(90도 회전)과 제목
col1, col2 = st.columns([0.1, 0.9])

with col1:
    if os.path.exists("mumu.jpg"):
        try:
            img = Image.open("mumu.jpg")
            rotated_img = img.rotate(-90, expand=True) # 성훈님 요청: 오른쪽 90도 회전
            st.image(rotated_img, width=80)
        except:
            st.write("🐶")
    else:
        st.write("🐶")

with col2:
    st.markdown("## 무무 탐색기 : 전국 반려동물 동반 식당")
    st.caption("식품의약품안전처(식품안전나라) 공공데이터 Open-API 활용 서비스")

CACHE_FILE = "pet_data_cache.json"

# [보안] Streamlit Secrets에서 인증키 호출
try:
    auth_key = st.secrets["AUTH_KEY"]
except:
    st.error("설정(Secrets)에서 AUTH_KEY를 찾을 수 없습니다. .streamlit/secrets.toml을 확인해주세요.")
    st.stop()

# [유틸리티] 네이버 지도 검색 링크 생성
def create_naver_link(row):
    base_url = "https://map.naver.com/v5/search/"
    addr = str(row.get('상세주소', ''))
    parts = addr.split()
    city = parts[1] if len(parts) > 1 else (parts[0] if parts else "")
    query = f"{city} {row.get('업소명', '')}"
    return f"{base_url}{urllib.parse.quote(query)}"

# 2. 데이터 전수 동기화 로직 (API 수집 시에도 동일한 JSON 구조 유지)
def auto_sync_api():
    service_id = "I1200"
    parsed_list = []
    start_idx = 1
    
    with st.status("🔄 전국 데이터를 최신 상태로 동기화 중입니다...", expanded=True) as status:
        info_area = st.empty()
        
        while True:
            end_idx = start_idx + 999
            url = f"http://openapi.foodsafetykorea.go.kr/api/{auth_key}/{service_id}/json/{start_idx}/{end_idx}"
            
            try:
                response = requests.get(url, timeout=20)
                data = response.json()
                rows = data.get(service_id, {}).get('row', [])
                
                if not rows:
                    break
                
                for r in rows:
                    # 반려동물 동반 가능 여부 필터링
                    if r.get("PET_OUTIN_YN") == "Y" or r.get("ANSIM_PET_YN") == "Y":
                        parsed_list.append({
                            "업소명": r.get("BSSH_NM"),
                            "업종": r.get("INDUTY_NM"),
                            "전화번호": r.get("TELNO", ""), # 데이터에는 저장 (나중을 위해)
                            "상세주소": r.get("LOCP_ADDR"),
                            "수집날짜": datetime.now().strftime("%Y-%m-%d")
                        })
                
                info_area.markdown(f"🔎 **분석 중:** {start_idx + len(rows) - 1:,}개 업소 | ✅ **찾은 맛집:** {len(parsed_list):,}개")
                start_idx += 1000
            except:
                break
        
        if parsed_list:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(parsed_list, f, ensure_ascii=False, indent=4)
            status.update(label=f"✅ 업데이트 완료! 총 {len(parsed_list):,}개를 찾았습니다.", state="complete", expanded=False)
            info_area.empty()
            
    return parsed_list

# 3. 데이터 로드 및 날짜 기반 자동 업데이트 체크
df = None
current_date = datetime.now().strftime("%Y-%m-%d")

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            if cache_data:
                last_update = cache_data[0].get("수집날짜", "")
                # 파일에 기록된 날짜가 오늘과 다르면 API 자동 실행
                if last_update != current_date:
                    df = pd.DataFrame(auto_sync_api())
                    st.rerun()
                else:
                    df = pd.DataFrame(cache_data)
    except:
        df = pd.DataFrame(auto_sync_api())
else:
    df = pd.DataFrame(auto_sync_api())
    st.rerun()

# 4. 사용자 인터페이스 (필터 및 결과 테이블)
if df is not None and not df.empty:
    # 지도 링크 및 지역 정보 생성
    df['지도보기'] = df.apply(create_naver_link, axis=1)
    df['지역'] = df['상세주소'].apply(lambda x: str(x).split()[0] if str(x).split() else "미분류")

    st.sidebar.header("📍 지역 필터")
    broad_regions = sorted(df["지역"].unique())
    selected_broad = st.sidebar.selectbox("1. 광역 선택", broad_regions, index=0)
    
    broad_df = df[df["지역"] == selected_broad].copy()
    city_list = sorted(list(set(broad_df["상세주소"].apply(lambda x: str(x).split()[1] if len(str(x).split()) > 1 else "전체"))))
    selected_city = st.sidebar.selectbox("2. 상세 지역 선택", ["전체"] + city_list)

    final_df = broad_df if selected_city == "전체" else broad_df[broad_df["상세주소"].str.contains(selected_city, na=False)]

    st.subheader(f"📍 {selected_broad} {selected_city if selected_city != '전체' else ''} 결과 (총 {len(final_df)}건)")

    # [중요] 화면 테이블에는 '전화번호'를 노출하지 않습니다.
    st.dataframe(
        final_df[['업소명', '업종', '상세주소', '지도보기']],
        width='stretch',
        column_config={"지도보기": st.column_config.LinkColumn("네이버 지도", display_text="지도보기 🔗")},
        hide_index=True
    )
    
    # 배포 시에는 주석 처리 가능
    st.sidebar.divider()
    if st.sidebar.button("📡 데이터 강제 갱신"):
        auto_sync_api()
        st.rerun()

# 5. 하단 출처 표기 및 비영리 목적 안내 (성훈님 요청 반영)
st.divider()
st.markdown(f"""
    <div style="font-size: 0.85rem; color: #555; text-align: center; line-height: 1.8; background-color: #f8f9fa; padding: 25px; border-radius: 12px; border: 1px solid #eee;">
        <p style="font-size: 1rem; color: #222;"><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 <b>반려동물을 가족으로 키우는 반려인의 마음으로, 전국의 동반 가능 식당 정보를 보다 쉽고 편리하게 확인하기 위한 단순 정보 제공 목적으로 제작되었습니다.</b><br>
        공공데이터법에 의거하여 <b>식품의약품안전처</b>에서 제공하는 Open-API를 활용한 <b>비영리 목적의 사이트</b>임을 밝힙니다.<br><br>
        데이터는 매일 자정 자동으로 최신화되나, 현장의 영업 상황은 실시간 반영이 어려울 수 있습니다.<br>
        <span style="color: #d32f2f;"><b>정확한 정보 확인을 위해 방문 전 반드시 해당 업소에 유선으로 영업 여부를 확인해 주시기 바랍니다.</b></span><br>
        본 서비스의 정보를 활용한 결과로 발생하는 사항에 대해 운영자는 법적 책임을 지지 않습니다.<br><br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved. | 출처: 식품의약품안전처 식품안전나라
    </div>
""", unsafe_allow_html=True)