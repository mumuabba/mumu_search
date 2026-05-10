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

# 2. 우측 상단 메뉴 숨김 및 모바일 최적화 CSS
hide_style = """
    <style>
    .viewerBadge_container__1QS1n { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .block-container { padding: 1rem 1rem; } /* 모바일 여백 최적화 */
    
    table { 
        width: 100%; 
        border-collapse: collapse; 
        margin-top: 10px; 
        table-layout: fixed; /* 컬럼 너비 고정 */
    }
    th { 
        background-color: rgba(128, 128, 128, 0.15); 
        text-align: left; 
        padding: 10px; 
        font-size: 0.85rem;
        border-bottom: 2px solid rgba(128, 128, 128, 0.3);
    }
    td { 
        padding: 12px 8px; 
        border-bottom: 1px solid rgba(128, 128, 128, 0.1); 
        font-size: 0.88rem;
        word-break: break-all; /* 긴 이름 줄바꿈 */
        vertical-align: middle;
    }
    a { 
        text-decoration: none; 
        color: #4dabff; 
        font-weight: bold; 
    }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

CACHE_FILE = "pet_data_cache.json"

def create_kakao_link(row):
    base_url = "https://map.kakao.com/link/search/"
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

if not df.empty:
    def get_broad_region(addr):
        parts = str(addr).split()
        return parts[0] if len(parts) > 0 else "미분류"
    
    df['지역'] = df['상세주소'].apply(get_broad_region)
    df['카카오맵'] = df.apply(create_kakao_link, axis=1)

    st.markdown("### 🐶 무무 탐색기")
    st.caption("이름을 클릭하면 지도로 연결됩니다. 🗺️")
    
    last_update = df['수집날짜'].iloc[0] if '수집날짜' in df.columns else "정보 없음"
    st.info(f"⏱️ **업데이트:** {last_update}")

    # 1단계: 광역 지역 선택
    broad_regions = sorted([r for r in df["지역"].unique() if r not in ["미분류", "nan", "None"]])
    selected_broad = st.pills("광역 선택", broad_regions, selection_mode="single", label_visibility="collapsed")
    
    if not selected_broad:
        if os.path.exists("mumu.jpg"):
            try:
                img = Image.open("mumu.jpg").rotate(-90, expand=True)
                st.image(img, width=200)
            except: st.write("🐶")
        st.info("지역을 선택해 주세요!")
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
            st.success(f"🔍 {len(final_df):,}건 검색됨")
            
            # 💡 [주소 다이어트 로직] 선택된 지역명을 주소에서 제거
            def shorten_address(addr, broad, city):
                addr_str = str(addr)
                # 광역/시군구 명칭 제거 (예: '강원특별자치도 원주시 ' 삭제)
                remove_target = f"{broad} {city}" if city != "전체" else broad
                return addr_str.replace(remove_target, "").strip()

            def make_clickable(name, link):
                return f'<a href="{link}" target="_blank">{name}</a>'

            display_df = final_df.copy()
            # 주소 줄이기 적용
            display_df['표시주소'] = display_df.apply(lambda x: shorten_address(x['상세주소'], selected_broad, selected_city), axis=1)
            display_df['업소명'] = display_df.apply(lambda x: make_clickable(x['업소명'], x['카카오맵']), axis=1)

            # HTML 테이블 생성 (너비 비율 조정)
            table_html = f"""
            <table>
                <thead>
                    <tr>
                        <th style="width: 45%;">업소명</th>
                        <th style="width: 55%;">상세 주소 (이하)</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f"<tr><td>{row['업소명']}</td><td>{row['표시주소']}</td></tr>" for _, row in display_df.iterrows()])}
                </tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)

# 4. 하단 고지
st.divider()
st.markdown(f"""
    <div style="font-size: 0.8rem; color: #666; text-align: center; line-height: 1.6; background-color: rgba(128, 128, 128, 0.05); padding: 20px; border-radius: 10px;">
        <p style="font-size: 0.9rem; color: inherit;"><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 반려동물 동반 식당 정보를 편리하게 확인하기 위한 단순 정보 제공 서비스입니다.<br>
        <span style="color: #d32f2f;"><b>정확한 정보 확인을 위해 방문 전 반드시 유선 문의 바랍니다.</b></span><br><br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved.
    </div>
""", unsafe_allow_html=True)
