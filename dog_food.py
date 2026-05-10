import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from PIL import Image

# 1. 페이지 설정
st.set_page_config(page_title="무무 탐색기 - mumuabba", layout="wide")

CACHE_FILE = "pet_data_cache.json"

# [유틸리티] 네이버 지도 링크 생성
def create_naver_link(row):
    base_url = "https://map.naver.com/v5/search/"
    addr = str(row.get('상세주소', ''))
    parts = addr.split()
    city = parts[1] if len(parts) > 1 else (parts[0] if parts else "")
    query = f"{city} {row.get('업소명', '')}"
    return f"{base_url}{urllib.parse.quote(query)}"

@st.cache_data
def load_data():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return pd.DataFrame(json.load(f))
        except: return pd.DataFrame()
    return pd.DataFrame()

df = load_data()

# 2. 사용자 인터페이스
if not df.empty:
    df['지도보기'] = df.apply(create_naver_link, axis=1)
    def get_broad_region(addr):
        parts = str(addr).split()
        return parts[0] if len(parts) > 0 else "미분류"
    df['지역'] = df['상세주소'].apply(get_broad_region)

    # 헤더 섹션
    st.markdown("### 🐶 무무 탐색기 : 전국 동반 식당")
    st.caption("반려동물을 사랑하는 마음으로 만든 정보 제공 서비스") # 수정된 부분
    
    # 마지막 업데이트 시간 표시
    last_update = df['수집날짜'].iloc[0] if '수집날짜' in df.columns else "정보 없음"
    st.info(f"⏱️ **최종 정보 갱신 일자:** {last_update} (매일 새벽 1시 자동 갱신)")
    st.write("---")

    # 지역 선택 필터
    st.markdown("#### 📍 1. 광역 지역 선택")
    broad_regions = sorted([r for r in df["지역"].unique() if r not in ["미분류", "nan", "None"]])
    selected_broad = st.pills("광역 선택", broad_regions, selection_mode="single", label_visibility="collapsed")
    
    if not selected_broad:
        if os.path.exists("mumu.jpg"):
            try:
                img = Image.open("mumu.jpg").rotate(-90, expand=True)
                st.image(img, width=250)
            except:
                st.write("🐶")
        st.info("위의 **지역 버튼**을 클릭하여 탐색을 시작하세요! 🐾")
    else:
        st.write("---")
        st.markdown(f"#### 📍 2. {selected_broad} 상세 지역")
        broad_df = df[df["지역"] == selected_broad].copy()
        def get_city_safe(addr):
            parts = str(addr).split()
            return parts[1] if len(parts) > 1 else "기타"
        city_list = sorted(list(set(broad_df["상세주소"].apply(get_city_safe).values)))
        selected_city = st.pills("상세 지역 선택", ["전체"] + city_list, selection_mode="single", label_visibility="collapsed")

        if selected_city:
            final_df = broad_df if selected_city == "전체" else broad_df[broad_df["상세주소"].apply(get_city_safe) == selected_city]
            st.success(f"🔍 검색 결과: {len(final_df):,}건")
            st.dataframe(
                final_df[['업소명', '상세주소', '지도보기']],
                use_container_width=True,
                hide_index=True,
                column_config={"지도보기": st.column_config.LinkColumn("네이버 지도", display_text="보기 🔗")}
            )

# 4. 하단 안내문구 (예전 버전 복구)
st.divider()
st.markdown(f"""
    <div style="font-size: 0.85rem; color: #555; text-align: center; line-height: 1.8; background-color: #f8f9fa; padding: 25px; border-radius: 12px; border: 1px solid #eee;">
        <p style="font-size: 1rem; color: #222;"><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 <b>반려동물을 가족으로 키우는 반려인의 마음으로, 전국의 동반 가능 식당 정보를 보다 쉽고 편리하게 확인하기 위한 단순 정보 제공 목적으로 제작되었습니다.</b><br>
        공공데이터법에 의거하여 <b>식품의약품안전처</b>에서 제공하는 Open-API를 활용한 정보 서비스임을 밝힙니다.<br><br>
        데이터는 <b>매일 새벽 1시</b>에 자동으로 최신화됩니다.<br>
        <span style="color: #d32f2f;"><b>정확한 정보 확인을 위해 방문 전 반드시 해당 업소에 유선으로 영업 여부를 확인해 주시기 바랍니다.</b></span><br>
        본 서비스의 정보를 활용한 결과로 발생하는 사항에 대해 운영자는 법적 책임을 지지 않습니다.<br><br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved. | 출처: 식품의약품안전처 식품안전나라
    </div>
""", unsafe_allow_html=True)
