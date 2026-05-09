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

CACHE_FILE = "pet_data_cache.json"

# [보안] Secrets 호출
try:
    auth_key = st.secrets["AUTH_KEY"]
except:
    st.error("설정(Secrets)에서 AUTH_KEY를 찾을 수 없습니다.")
    st.stop()

# [유틸리티] 네이버 지도 링크
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

# 2. 사용자 인터페이스 (키보드 안 뜨는 Pills UI)
if not df.empty:
    df['지도보기'] = df.apply(create_naver_link, axis=1)
    def get_broad_region(addr):
        parts = str(addr).split()
        return parts[0] if len(parts) > 0 else "미분류"
    df['지역'] = df['상세주소'].apply(get_broad_region)

    # [수정] 지역 선택창을 사진보다 위로 올렸습니다 (화면 튐 방지)
    st.markdown("#### 📍 어디로 가시나요?")
    broad_regions = sorted([r for r in df["지역"].unique() if r not in ["미분류", "nan", "None"]])
    
    # [핵심] st.pills 사용 - 자판이 절대 안 뜨고 박스 형태로 깔끔함
    selected_broad = st.pills(
        "1. 광역 선택", 
        broad_regions, 
        selection_mode="single",
        label_visibility="collapsed"
    )
    
    selected_city = "전체"
    if selected_broad:
        st.write("---")
        broad_df = df[df["지역"] == selected_broad].copy()
        def get_city_safe(addr):
            parts = str(addr).split()
            return parts[1] if len(parts) > 1 else "기타"
        city_list = sorted(list(set(broad_df["상세주소"].apply(get_city_safe).values)))
        
        st.markdown(f"#### 📍 {selected_broad} 상세 지역")
        selected_city = st.pills(
            "2. 상세 지역 선택", 
            ["전체"] + city_list, 
            selection_mode="single",
            label_visibility="collapsed"
        )

        # 결과 출력 섹션
        if selected_city:
            # 헤더(사진)를 결과 위에 배치
            col_img, col_txt = st.columns([0.3, 0.7])
            with col_img:
                if os.path.exists("mumu.jpg"):
                    try:
                        img = Image.open("mumu.jpg")
                        rotated_img = img.rotate(-90, expand=True) 
                        st.image(rotated_img, width=100)
                    except: st.write("🐶")
            with col_txt:
                st.markdown("### 무무 탐색기")
                st.caption(f"{selected_broad} {selected_city if selected_city != '전체' else ''} 맛집")

            if selected_city == "전체":
                final_df = broad_df
            else:
                final_df = broad_df[broad_df["상세주소"].apply(get_city_safe) == selected_city]
            
            st.success(f"🔍 검색 결과: {len(final_df):,}건")
            st.dataframe(
                final_df[['업소명', '업종', '상세주소', '지도보기']],
                use_container_width=True,
                column_config={"지도보기": st.column_config.LinkColumn("네이버 지도", display_text="보기 🔗")},
                hide_index=True
            )
    else:
        # 아무것도 선택 안 했을 때 무무 사진 크게 보여주기
        st.write("---")
        if os.path.exists("mumu.jpg"):
            img = Image.open("mumu.jpg").rotate(-90, expand=True)
            st.image(img, width=200)
        st.info("지역 버튼을 누르면 무무가 맛집을 찾아드려요! 🐾")

# 5. 하단 안내문구 (불변)
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
