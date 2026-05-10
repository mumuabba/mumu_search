import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from PIL import Image

# 1. 페이지 설정 및 보안 UI 숨김
st.set_page_config(
    page_title="무무 탐색기 - 반려동물 동반 음식점 검색기",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# 2. 우측 상단 메뉴 숨김 및 모바일 최적화 CSS
hide_style = """
    <style>
    .viewerBadge_container__1QS1n { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .block-container { padding: 1.5rem 1rem; }
    
    .main-title { font-size: 1.8rem; font-weight: bold; margin-bottom: 0.2rem; }
    .main-subtitle { font-size: 1rem; color: #888; margin-bottom: 1.5rem; }
    
    table { width: 100%; border-collapse: collapse; margin-top: 10px; table-layout: fixed; color: inherit; }
    th { background-color: rgba(128, 128, 128, 0.15); text-align: left; padding: 10px; font-size: 0.85rem; border-bottom: 2px solid rgba(128, 128, 128, 0.3); }
    td { padding: 12px 8px; border-bottom: 1px solid rgba(128, 128, 128, 0.1); font-size: 0.88rem; word-break: break-all; vertical-align: middle; background-color: transparent; }
    a { text-decoration: none; color: #4dabff; font-weight: bold; }
    .counter-wrapper { text-align: center; padding: 15px 0; }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

CACHE_FILE = "pet_data_cache.json"

# 카카오맵 링크 생성 (성훈님의 엑셀 필드명 '상세주소' 기준)
def create_kakao_link(row):
    base_url = "https://map.kakao.com/link/search/"
    query = f"{row.get('업소명', '')}"
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

if not df.empty:
    # 💡 엑셀 데이터의 구조를 반영하여 필드 설정
    # 변환 코드(convert_to_json.py)에서 이미 '지역' 필드를 생성하므로 그대로 사용합니다.
    df['카카오맵'] = df.apply(create_kakao_link, axis=1)

    st.markdown('<p class="main-title">🐶 무무 탐색기</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">반려동물 동반 음식점 검색기</p>', unsafe_allow_html=True)
    
    # 💡 GitHub Action이 기록한 변환 시간 표시
    last_update = df['수집날짜'].iloc[0] if '수집날짜' in df.columns else "정보 없음"
    st.info(f"⏱️ **데이터 최종 업데이트:** {last_update}")

    # 1단계: 광역 지역 선택 (성훈님 엑셀의 '지역' 컬럼 활용)
    broad_regions = sorted([r for r in df["지역"].unique() if r not in ["미분류", "nan", "None"]])
    selected_broad = st.pills("광역 선택", broad_regions, selection_mode="single", label_visibility="collapsed")
    
    if not selected_broad:
        if os.path.exists("mumu.jpg"):
            try:
                img = Image.open("mumu.jpg").rotate(-90, expand=True)
                st.image(img, width=200)
            except: st.write("🐶")
        st.info("탐색할 지역을 선택해 주세요!")
    else:
        # 2단계: 상세 지역 선택
        broad_df = df[df["지역"] == selected_broad].copy()
        
        def get_city_safe(addr):
            parts = str(addr).split()
            return parts[1] if len(parts) > 1 else "기타"
        
        city_list = sorted(list(set(broad_df["상세주소"].apply(get_city_safe).values)))
        selected_city = st.pills("상세 지역 선택", ["전체"] + city_list, selection_mode="single", label_visibility="collapsed")

        if selected_city:
            final_df = broad_df if selected_city == "전체" else broad_df[broad_df["상세주소"].apply(get_city_safe) == selected_city]
            st.success(f"🔍 {len(final_df):,}건 검색됨 (이름 클릭 시 지도 이동)")
            
            def shorten_address(addr, broad, city):
                addr_str = str(addr)
                remove_target = f"{broad} {city}" if city != "전체" else broad
                return addr_str.replace(remove_target, "").strip()

            def make_clickable(name, link):
                return f'<a href="{link}" target="_blank">{name}</a>'

            display_df = final_df.copy()
            display_df['표시주소'] = display_df.apply(lambda x: shorten_address(x['상세주소'], selected_broad, selected_city), axis=1)
            display_df['업소명'] = display_df.apply(lambda x: make_clickable(x['업소명'], x['카카오맵']), axis=1)

            table_html = f"""
            <table>
                <thead>
                    <tr>
                        <th style="width: 45%;">업소명</th>
                        <th style="width: 55%;">상세 주소</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f"<tr><td>{row['업소명']}</td><td>{row['표시주소']}</td></tr>" for _, row in display_df.iterrows()])}
                </tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)

# 4. 하단 카운터 및 안내 고지
st.write("---")

st.markdown(
    """
    <div class="counter-wrapper">
        <img src="https://komarev.com/ghpvc/?username=mumuabba-search&color=4dabff&style=flat-square&label=Mumu%20Friends" alt="Hits">
    </div>
    """, 
    unsafe_allow_html=True
)

st.markdown(f"""
    <div style="font-size: 0.85rem; color: #555; text-align: center; line-height: 1.8; background-color: rgba(128, 128, 128, 0.05); padding: 25px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.1);">
        <p style="font-size: 1rem; color: inherit;"><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 <b>반려동물을 가족으로 키우는 반려인의 마음으로, 전국의 동반 가능 식당 정보를 보다 쉽고 편리하게 확인하기 위한 단순 정보 제공 목적으로 제작되었습니다.</b><br>
        수동으로 관리되는 엑셀 데이터를 바탕으로 최신 정보를 제공합니다.<br><br>
        데이터는 <b>관리자가 엑셀 파일을 업데이트할 때마다</b> 즉시 반영됩니다.<br>
        <span style="color: #d32f2f;"><b>정확한 정보 확인을 위해 방문 전 반드시 해당 업소에 유선으로 영업 여부를 확인해 주시기 바랍니다.</b></span><br><br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved. | 데이터 출처: 사용자 관리 데이터
    </div>
""", unsafe_allow_html=True)
