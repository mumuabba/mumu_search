import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from PIL import Image

# 1. 페이지 설정 및 보안 UI 숨김
st.set_page_config(
    page_title="무무 탐색기 - mumuabba",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

hide_style = """
    <style>
    .viewerBadge_container__1QS1n { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .block-container { padding-top: 2rem; }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

CACHE_FILE = "pet_data_cache.json"

# [유틸리티] 카카오맵 검색 링크 생성 (네이버에서 카카오로 변경)
def create_kakao_link(row):
    base_url = "https://map.kakao.com/link/search/"
    addr = str(row.get('상세주소', ''))
    parts = addr.split()
    # "강원도 원주 시청로" -> "원주" 추출해서 검색 정확도 높임
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

# 3. 메인 로직
if not df.empty:
    def get_broad_region(addr):
        parts = str(addr).split()
        return parts[0] if len(parts) > 0 else "미분류"
    
    df['지역'] = df['상세주소'].apply(get_broad_region)
    # 카카오맵 링크 생성
    df['카카오맵'] = df.apply(create_kakao_link, axis=1)

    st.markdown("### 🐶 무무 탐색기 : 전국 동반 식당")
    st.caption("업소명을 클릭하면 카카오맵으로 연결됩니다. 🗺️")
    
    last_update = df['수집날짜'].iloc[0] if '수집날짜' in df.columns else "정보 없음"
    st.info(f"⏱️ **업데이트:** {last_update}")
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
            except: st.write("🐶")
        st.info("지역을 선택해 주세요!")
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
            
            st.success(f"🔍 {len(final_df):,}건 검색됨 (이름 클릭 시 지도 이동)")
            
            # 테이블 설정: 업소명 클릭 시 카카오맵 연결
            st.dataframe(
                final_df[['업소명', '상세주소', '카카오맵']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "업소명": st.column_config.LinkColumn(
                        "업소명 (카카오맵 연결)", 
                        url_path="카카오맵" 
                    ),
                    "상세주소": "주소",
                    "카카오맵": None 
                }
            )

# 하단 고지
st.divider()
st.markdown(f"""
    <div style="font-size: 0.85rem; color: #555; text-align: center; line-height: 1.8; background-color: #f8f9fa; padding: 25px; border-radius: 12px; border: 1px solid #eee;">
        <p style="font-size: 1rem; color: #222;"><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 <b>반려동물과 함께하는 행복한 일상을 위해 만든 정보 제공 서비스입니다.</b><br>
        <span style="color: #d32f2f;"><b>정확한 정보 확인을 위해 방문 전 반드시 해당 업소에 유선으로 영업 여부를 확인해 주시기 바랍니다.</b></span><br><br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved. | 출처: 식품의약품안전처
    </div>
""", unsafe_allow_html=True)
