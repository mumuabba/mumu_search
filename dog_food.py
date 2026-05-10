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

# 2. 우측 상단 메뉴 및 깃허브 아이콘 숨김 CSS
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

# [유틸리티] 카카오맵 검색 링크 생성 함수
def create_kakao_link(row):
    base_url = "https://map.kakao.com/link/search/"
    addr = str(row.get('상세주소', ''))
    parts = addr.split()
    # 주소에서 시/군 단위를 추출해 검색 정확도를 높임
    city = parts[1] if len(parts) > 1 else (parts[0] if parts else "")
    query = f"{city} {row.get('업소명', '')}"
    return f"{base_url}{urllib.parse.quote(query)}"

@st.cache_data
def load_data():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return pd.DataFrame(json.load(f))
        except:
            return pd.DataFrame()
    return pd.DataFrame()

df = load_data()

# 3. 메인 서비스 로직
if not df.empty:
    # 지역 분류 함수
    def get_broad_region(addr):
        parts = str(addr).split()
        return parts[0] if len(parts) > 0 else "미분류"
    
    df['지역'] = df['상세주소'].apply(get_broad_region)
    # 카카오맵 링크 생성
    df['카카오맵'] = df.apply(create_kakao_link, axis=1)

    # 헤더 섹션
    st.markdown("### 🐶 무무 탐색기 : 전국 동반 식당")
    st.caption("업소명을 클릭하면 카카오맵으로 연결됩니다. 🗺️")
    
    # 마지막 업데이트 시간 표시
    last_update = df['수집날짜'].iloc[0] if '수집날짜' in df.columns else "정보 없음"
    st.info(f"⏱️ **최종 정보 갱신 일자:** {last_update} (매일 새벽 1시 자동 갱신)")
    st.write("---")

    # 1단계: 광역 지역 선택
    st.markdown("#### 📍 1. 광역 지역 선택")
    broad_regions = sorted([r for r in df["지역"].unique() if r not in ["미분류", "nan", "None"]])
    selected_broad = st.pills("광역 선택", broad_regions, selection_mode="single", label_visibility="collapsed")
    
    if not selected_broad:
        # 지역 미선택 시 무무 사진 (회전 보정 포함)
        if os.path.exists("mumu.jpg"):
            try:
                img = Image.open("mumu.jpg").rotate(-90, expand=True)
                st.image(img, width=250)
            except:
                st.write("🐶")
        st.info("위의 **지역 버튼**을 클릭하여 탐색을 시작하세요! 🐾")
    else:
        st.write("---")
        # 2단계: 상세 지역 선택
        st.markdown(f"#### 📍 2. {selected_broad} 상세 지역")
        broad_df = df[df["지역"] == selected_broad].copy()
        
        def get_city_safe(addr):
            parts = str(addr).split()
            return parts[1] if len(parts) > 1 else "기타"
        
        city_list = sorted(list(set(broad_df["상세주소"].apply(get_city_safe).values)))
        selected_city = st.pills("상세 지역 선택", ["전체"] + city_list, selection_mode="single", label_visibility="collapsed")

        if selected_city:
            final_df = broad_df if selected_city == "전체" else broad_df[broad_df["상세주소"].apply(get_city_safe) == selected_city]
            
            st.success(f"🔍 검색 결과: {len(final_df):,}건 (업소명 클릭 시 지도 이동)")
            
            # 테이블 설정: 에러 방지를 위해 가장 안정적인 LinkColumn 방식 사용
            st.dataframe(
                final_df[['업소명', '상세주소', '카카오맵']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "업소명": st.column_config.LinkColumn(
                        "업소명 (클릭 시 카카오맵)",
                        # url_path 대신 가장 호환성 높은 방식으로 처리
                        display_text=None 
                    ),
                    "상세주소": "상세 주소",
                    "카카오맵": None  # 링크용 데이터이므로 표에서는 숨김
                }
            )

# 4. 하단 안내 및 책임 한계 고지 (변동 없음)
st.divider()
st.markdown(f"""
    <div style="font-size: 0.85rem; color: #555; text-align: center; line-height: 1.8; background-color: #f8f9fa; padding: 25px; border-radius: 12px; border: 1px solid #eee;">
        <p style="font-size: 1rem; color: #222;"><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 <b>반려동물을 가족으로 키우는 반려인의 마음으로, 전국의 동반 가능 식당 정보를 보다 쉽고 편리하게 확인하기 위한 단순 정보 제공 목적으로 제작되었습니다.</b><br>
        식품의약품안전처에서 제공하는 Open-API를 활용한 정보 서비스임을 밝힙니다.<br><br>
        데이터는 <b>매일 새벽 1시</b>에 자동으로 최신화됩니다.<br>
        <span style="color: #d32f2f;"><b>정확한 정보 확인을 위해 방문 전 반드시 해당 업소에 유선으로 영업 여부를 확인해 주시기 바랍니다.</b></span><br><br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved. | 출처: 식품의약품안전처 식품안전나라
    </div>
""", unsafe_allow_html=True)
