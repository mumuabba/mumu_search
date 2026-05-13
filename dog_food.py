import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
import time  # 💡 NameError 해결을 위해 time 라이브러리를 명시적으로 추가!
from PIL import Image

# 1. 페이지 설정 및 보안 UI 숨김
st.set_page_config(
    page_title="무무 탐색기 - 식품의약품안전처 등록 반려동물 동반 음식점",
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

def get_file_mtime(file_path):
    if os.path.exists(file_path):
        return os.path.getmtime(file_path)
    return 0

@st.cache_data(ttl=600)
def load_data(mtime):
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return pd.DataFrame(json.load(f))
        except: return pd.DataFrame()
    return pd.DataFrame()

current_mtime = get_file_mtime(CACHE_FILE)
df = load_data(current_mtime)

if not df.empty:
    # 🎯 무적의 방어 코드: 원본 엑셀의 컬럼명이 바뀌어도 웹 앱이 오류 없이 인식하도록 강제 변환
    if '업소주소' in df.columns:
        df = df.rename(columns={'업소주소': '상세주소'})
    elif 'siteAddr' in df.columns:
        df = df.rename(columns={'siteAddr': '상세주소'})
        
    if 'bsshNm' in df.columns and '업소명' not in df.columns:
        df = df.rename(columns={'bsshNm': '업소명'})

    def get_region(addr):
        addr_str = str(addr).strip()
        if not addr_str or addr_str == 'nan': return "미분류"
        return addr_str.split()[0]

    df['지역'] = df['상세주소'].apply(get_region)
    df['카카오맵'] = df.apply(create_kakao_link, axis=1)

    st.markdown('<p class="main-title">🐶 무무 탐색기</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">식품의약품안전처에 등록된 반려동물 동반 음식점 검색기</p>', unsafe_allow_html=True)
    
    if '수집날짜' in df.columns:
        last_update = df['수집날짜'].dropna().iloc[0] if not df['수집날짜'].dropna().empty else "정보 없음"
    else:
        last_update = "정보 없음"
        
    # 💡 로봇이 새벽마다 작성한 stats.json 장부를 읽어와 전체 개수와 증감 지표 연동
    total_count = len(df)
    diff_count = 0
    
    if os.path.exists("stats.json"):
        try:
            with open("stats.json", "r", encoding="utf-8") as f:
                stats = json.load(f)
                diff_count = stats.get("diff", 0)
        except: pass

    # 상단을 2분할하여 대시보드 형태로 출력
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.info(f"⏱️ **최신 데이터 갱신:**\n{last_update}")
        
    with col2:
        st.metric(
            label="🍽️ 식약처 등록 동반 가능 업소", 
            value=f"{total_count:,}개", 
            delta=f"{diff_count}개"
        )

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

# 4. 하단 안내 고지 및 범용 카운터
st.write("---")

counter_url = "https://api.visitorbadge.io/api/visitors?path=mumuabba-mumu-search&label=Mumu%20Friends&countColor=%234dabff"

st.markdown(
    f"""
    <div class="counter-wrapper">
        <img src="{counter_url}" alt="Hits" style="display: inline-block;">
    </div>
    """, 
    unsafe_allow_html=True
)

st.markdown(f"""
    <div style="font-size: 0.85rem; color: #555; text-align: center; line-height: 1.8; background-color: rgba(128, 128, 128, 0.05); padding: 25px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.1);">
        <p style="font-size: 1rem; color: inherit;"><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 <b>반려동물을 가족으로 키우는 반려인의 마음으로, 전국의 동반 가능 식당 정보를 보다 쉽고 편리하게 확인하기 위한 단순 정보 제공 목적으로 제작되었습니다.</b><br>
        식품의약품안전처에서 제공하는 공공데이터를 기반으로 하며, <b>데이터는 운영자가 주기적으로 업데이트합니다.</b><br><br>
        <span style="color: #d32f2f;"><b>정확한 정보 확인을 위해 방문 전 반드시 해당 업소에 유선으로 영업 여부를 확인해 주시기 바랍니다.</b></span><br><br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved. | 출처: 식품의약품안전처 식품안전나라
    </div>
""", unsafe_allow_html=True)
