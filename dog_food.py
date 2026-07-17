import streamlit as st
import pandas as pd
import html
import json
import os
import urllib.parse
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
    
    .stat-card {
        background-color: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 12px 15px;
        text-align: left;
        margin-bottom: 10px;
    }
    .stat-label { font-size: 0.8rem; color: #888; margin-bottom: 2px; }
    .stat-value { font-size: 1.2rem; font-weight: bold; color: inherit; line-height: 1.2; }
    .stat-delta { font-size: 0.75rem; font-weight: bold; margin-top: 4px; }
    .delta-up { color: #2ecc71; }
    .delta-down { color: #e74c3c; }
    .delta-none { color: #888; }
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

@st.cache_data(ttl=600)
def load_stats(mtime):
    if os.path.exists("stats.json"):
        try:
            with open("stats.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


@st.cache_data
def load_mumu_image(mtime):
    return Image.open("mumu.jpg").rotate(-90, expand=True)


current_mtime = get_file_mtime(CACHE_FILE)
df = load_data(current_mtime)
stats = load_stats(get_file_mtime("stats.json"))

if df.empty:
    st.markdown('<p class="main-title">🐶 무무 탐색기</p>', unsafe_allow_html=True)
    st.error(
        "데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.\n\n"
        "문제가 계속되면 데이터 갱신 작업이 실패한 상태일 수 있습니다."
    )
else:
    if '업소주소' in df.columns: df = df.rename(columns={'업소주소': '상세주소'})
    elif 'siteAddr' in df.columns: df = df.rename(columns={'siteAddr': '상세주소'})
    if 'bsshNm' in df.columns and '업소명' not in df.columns: df = df.rename(columns={'bsshNm': '업소명'})

    def get_region(addr):
        addr_str = str(addr).strip()
        if not addr_str or addr_str == 'nan': return "미분류"
        return addr_str.split()[0]

    df['지역'] = df['상세주소'].apply(get_region)
    df['카카오맵'] = df.apply(create_kakao_link, axis=1)

    st.markdown('<p class="main-title">🐶 무무 탐색기</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">식품의약품안전처에 등록된 반려동물 동반 음식점 검색기</p>', unsafe_allow_html=True)
    
    # 갱신 시각은 update_stats.py가 KST로 확정해 stats.json에 넣어준다.
    # ('수집날짜' 컬럼은 예전 캐시 형식이라 폴백으로만 남겨둔다.)
    last_update = stats.get("updated_at")
    if not last_update and '수집날짜' in df.columns:
        valid_dates = df['수집날짜'].dropna()
        last_update = str(valid_dates.iloc[0]) if not valid_dates.empty else None
    last_update = last_update or "정보 없음"

    total_count = len(df)
    diff_count = stats.get("diff", 0)

    delta_class = "delta-up" if diff_count > 0 else ("delta-down" if diff_count < 0 else "delta-none")
    delta_icon = "▲" if diff_count > 0 else ("▼" if diff_count < 0 else "-")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.info(f"⏱️ **최신 데이터 갱신:**\n{last_update}")
    with col2:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">식약처 등록 동반 가능 업소</div>
                <div class="stat-value">{total_count:,}개</div>
                <div class="stat-delta {delta_class}">
                    {delta_icon} {abs(diff_count)}개 <span style="font-weight:normal; color:#888;">(이전 대비)</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)

    global_search_kw = st.text_input(
        "🔍 전국 통합 매장 검색 (빠른 확인)", 
        placeholder="가고 싶은 카페, 식당 상호명이나 키워드를 입력하세요! (예: 스타벅스, 원주)"
    )

    def make_clickable(name, link):
        # 업소명에 '&'나 '<'가 들어간 상호가 실제로 존재하므로 반드시 이스케이프한다.
        return f'<a href="{html.escape(link, quote=True)}" target="_blank">{html.escape(str(name))}</a>'

    def render_table(rows):
        body = "".join(
            f"<tr><td>{r['업소명']}</td><td>{html.escape(str(r['표시주소']))}</td></tr>"
            for _, r in rows.iterrows()
        )
        return (
            '<table><thead><tr><th style="width: 45%;">업소명</th>'
            f'<th style="width: 55%;">상세 주소</th></tr></thead><tbody>{body}</tbody></table>'
        )

    if global_search_kw:
        # regex=False 필수: 검색어를 정규식으로 해석하면 '카페('처럼 괄호가 든
        # 입력에서 앱이 죽고, '(주)'는 괄호를 무시한 엉뚱한 결과를 돌려준다.
        name_hit = df['업소명'].str.contains(global_search_kw, case=False, na=False, regex=False)
        addr_hit = df['상세주소'].str.contains(global_search_kw, case=False, na=False, regex=False)
        search_df = df[name_hit | addr_hit].copy()
        st.success(f"🔍 전국에서 '{global_search_kw}' 관련 매장 **{len(search_df):,}건** 검색됨 (이름 클릭 시 지도 이동)")
        if search_df.empty:
            st.info("검색 결과가 없습니다. 다른 키워드로 찾아보세요!")
        else:
            search_df['표시주소'] = search_df['상세주소']
            search_df['업소명'] = search_df.apply(lambda x: make_clickable(x['업소명'], x['카카오맵']), axis=1)
            st.markdown(render_table(search_df), unsafe_allow_html=True)
    else:
        st.markdown('<p style="font-size: 0.85rem; color: #888; margin-bottom: 5px;">📍 지역별로 모아보기</p>', unsafe_allow_html=True)
        broad_regions = sorted([r for r in df["지역"].unique() if str(r) not in ["미분류", "nan", "None"]])
        selected_broad = st.pills("광역 선택", broad_regions, selection_mode="single", label_visibility="collapsed")
        
        if not selected_broad:
            if os.path.exists("mumu.jpg"):
                try:
                    st.image(load_mumu_image(get_file_mtime("mumu.jpg")), width=200)
                except Exception:
                    st.write("🐶")
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
                st.success(f"🔍 {selected_broad} {selected_city} ❯ {len(final_df):,}건 검색됨 (이름 클릭 시 지도 이동)")
                display_df = final_df.copy()
                # 이미 선택한 지역명은 주소에서 빼서 표를 짧게 만든다.
                prefix = selected_broad if selected_city == "전체" else f"{selected_broad} {selected_city}"
                display_df['표시주소'] = display_df['상세주소'].apply(
                    lambda addr: str(addr).replace(prefix, "").strip()
                )
                display_df['업소명'] = display_df.apply(lambda x: make_clickable(x['업소명'], x['카카오맵']), axis=1)
                st.markdown(render_table(display_df), unsafe_allow_html=True)

st.write("---")
counter_url = "https://api.visitorbadge.io/api/visitors?path=mumuabba-mumu-search&label=Mumu%20Friends&countColor=%234dabff"
st.markdown(f'<div class="counter-wrapper"><img src="{counter_url}" alt="Hits"></div>', unsafe_allow_html=True)
st.markdown(f"""
    <div style="font-size: 0.85rem; color: #555; text-align: center; line-height: 1.8; background-color: rgba(128, 128, 128, 0.05); padding: 25px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.1);">
        <p style="font-size: 1rem; color: inherit;"><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 <b>반려동물을 가족으로 키우는 반려인의 마음으로, 전국의 동반 가능 식당 정보를 보다 쉽고 편리하게 확인하기 위한 단순 정보 제공 목적으로 제작되었습니다.</b><br>
        식품의약품안전처에서 제공하는 공공데이터를 기반으로 하며, <b>데이터는 운영자가 주기적으로 업데이트합니다.</b><br><br>
        <span style="color: #d32f2f;"><b>정확한 정보 확인을 위해 방문 전 반드시 해당 업소에 유선으로 영업 여부를 확인해 주시기 바랍니다.</b></span><br><br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved. | 출처: 식품의약품안전처 식품안전나라
    </div>
""", unsafe_allow_html=True)
