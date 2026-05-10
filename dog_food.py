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

def create_kakao_link(row):
    base_url = "https://map.kakao.com/link/search/"
    query = f"{row.get('업소명', '')}"
    return f"{base_url}{urllib.parse.quote(query)}"

# 💡 파일의 수정 시간을 감지하는 함수
def get_file_mtime(file_path):
    if os.path.exists(file_path):
        return os.path.getmtime(file_path)
    return 0

# 💡 캐시 설정: 파일의 수정 시간(mtime)이 바뀌면 자동으로 새로 읽어옴
@st.cache_data(ttl=600)
def load_data(mtime):
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return pd.DataFrame(json.load(f))
        except: return pd.DataFrame()
    return pd.DataFrame()

# 데이터 로드 (파일 시간을 인자로 전달하여 캐시 갱신 유도)
current_mtime = get_file_mtime(CACHE_FILE)
df = load_data(current_mtime)

if not df.empty:
    # 지역 자동 추출
    def get_region(addr):
        addr_str = str(addr).strip()
        if not addr_str or addr_str == 'nan': return "미분류"
        return addr_str.split()[0]

    df['지역'] = df['상세주소'].apply(get_region)
    df['카카오맵'] = df.apply(create_kakao_link, axis=1)

    st.markdown('<p class="main-title">🐶 무무 탐색기</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">반려동물 동반 음식점 검색기</p>', unsafe_allow_html=True)
    
    # 상단 시간 표시
    if '수집날짜' in df.columns:
        last_update = df['수집날짜'].dropna().iloc[0] if not df['수집날짜'].dropna().empty else "정보 없음"
    else:
        last_update = "정보 없음"
    st.info(f"⏱️ **데이터 갱신:** {last_update}")

    # 1단계: 광역 지역 선택
    broad_regions = sorted([r for r in df["지역"].unique() if str(r) not in ["미분류", "nan", "None"]])
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
                remove_target = f"{broad} {city}" if selected_city != "전체" else broad
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

# 4. 하단 안내 고지
st.write("---")
st.markdown('<div class="counter-wrapper"><img src="https://komarev.com/ghpvc/?username=mumuabba-search&color=4dabff&style=flat-square&label=Mumu%20Friends" alt="Hits"></div>', unsafe_allow_html=True)

st.markdown(f"""
    <div style="font-size: 0.85rem; color: #555; text-align: center; line-height: 1.8; background-color: rgba(128, 128, 128, 0.05); padding: 25px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.1);">
        <p style="font-size: 1rem; color: inherit;"><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 <b>반려동물을 가족으로 키우는 반려인의 마음으로, 전국의 동반 가능 식당 정보를 보다 쉽고 편리하게 확인하기 위한 단순 정보 제공 목적으로 제작되었습니다.</b><br>
        식품의약품안전처에서 제공하는 Open-API를 활용한 정보 서비스임을 밝힙니다.<br><br>
        데이터는 <b>매일 새벽 1시</b>에 자동으로 최신화됩니다.<br>
        <span style="color: #d32f2f;"><b>정확한 정보 확인을 위해 방문 전 반드시 해당 업소에 유선으로 영업 여부를 확인해 주시기 바랍니다.</b></span><br><br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved. | 출처: 식품의약품안전처 식품안전나라
    </div>
""", unsafe_allow_html=True)
