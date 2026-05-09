import streamlit as st
import requests
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime
from PIL import Image

# 1. 페이지 설정 (모바일 최적화 레이아웃)
st.set_page_config(page_title="무무 탐색기 - mumuabba", layout="wide")

CACHE_FILE = "pet_data_cache.json"

# [보안] Secrets 호출
try:
    auth_key = st.secrets["AUTH_KEY"]
except:
    st.error("설정(Secrets)에서 AUTH_KEY를 찾을 수 없습니다.")
    st.stop()

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

# 2. 사용자 인터페이스 (Pills UI 및 조건부 노출 로직)
if not df.empty:
    df['지도보기'] = df.apply(create_naver_link, axis=1)
    def get_broad_region(addr):
        parts = str(addr).split()
        return parts[0] if len(parts) > 0 else "미분류"
    df['지역'] = df['상세주소'].apply(get_broad_region)

    # 헤더 섹션 (고정 문구)
    st.markdown("### 🐶 무무 탐색기 : 전국 동반 식당")
    st.caption("반려동물을 사랑하는 마음으로 만든 비영리 정보 서비스")
    st.write("---")

    # [핵심] 키보드 안 뜨는 박스형 필터 (Pills)
    st.markdown("#### 📍 1. 광역 지역 선택")
    broad_regions = sorted([r for r in df["지역"].unique() if r not in ["미분류", "nan", "None"]])
    
    selected_broad = st.pills(
        "광역 선택",
        broad_regions,
        selection_mode="single",
        label_visibility="collapsed"
    )
    
    # 3. 사진 노출 및 상세 검색 로직
    if not selected_broad:
        # [초기 화면] 아무것도 선택 안했을 때만 사진 노출
        st.write("")
        if os.path.exists("mumu.jpg"):
            img = Image.open("mumu.jpg").rotate(-90, expand=True)
            st.image(img, width=250)
        st.info("위의 **지역 버튼**을 클릭하여 탐색을 시작하세요! 🐾")
    
    else:
        # 광역이 선택된 경우
        st.write("---")
        st.markdown(f"#### 📍 2. {selected_broad} 상세 지역")
        broad_df = df[df["지역"] == selected_broad].copy()
        
        def get_city_safe(addr):
            parts = str(addr).split()
            return parts[1] if len(parts) > 1 else "기타"
            
        city_list = sorted(list(set(broad_df["상세주소"].apply(get_city_safe).values)))
        
        selected_city = st.pills(
            "상세 지역 선택",
            ["전체"] + city_list,
            selection_mode="single",
            label_visibility="collapsed"
        )

        if selected_city:
            # [결과 화면] 상세 지역까지 선택 완료 시 결과 출력 (사진은 자동 제거됨)
            if selected_city == "전체":
                final_df = broad_df
            else:
                final_df = broad_df[broad_df["상세주소"].apply(get_city_safe) == selected_city]
            
            st.success(f"🔍 {selected_broad} {selected_city if selected_city != '전체' else ''} 결과: {len(final_df):,}건")
            
            # [수정] '업종' 컬럼 제외
            st.dataframe(
                final_df[['업소명', '상세주소', '지도보기']],
                use_container_width=True,
                column_config={"지도보기": st.column_config.LinkColumn("네이버 지도", display_text="보기 🔗")},
                hide_index=True
            )
        else:
            # 광역은 골랐으나 상세 지역을 아직 안 골랐을 때
            st.write("")
            st.info(f"👉 **{selected_broad}**의 어느 상세 지역을 찾으시나요?")

# 4. 하단 출처 및 안내문구 (수정 일절 없음)
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
