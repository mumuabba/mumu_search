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

# [헤더 레이아웃] 무무 사진(90도 회전)과 제목
col1, col2 = st.columns([0.2, 0.8])

with col1:
    if os.path.exists("mumu.jpg"):
        try:
            img = Image.open("mumu.jpg")
            rotated_img = img.rotate(-90, expand=True) 
            st.image(rotated_img, width=80)
        except:
            st.write("🐶")
    else:
        st.write("🐶")

with col2:
    st.markdown("### 무무 탐색기 : 전국 반려동물 동반 식당")
    st.caption("반려동물을 사랑하는 마음으로 만든 비영리 정보 서비스")

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

# 2. 데이터 로드 로직
df = None
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            df = pd.DataFrame(cache_data)
    except:
        st.error("데이터 파일을 읽는 중 오류가 발생했습니다.")

# 3. 사용자 인터페이스 (드롭다운 최적화 UI)
if df is not None and not df.empty:
    df['지도보기'] = df.apply(create_naver_link, axis=1)
    
    def get_broad_region(addr):
        parts = str(addr).split()
        return parts[0] if len(parts) > 0 else "미분류"

    df['지역'] = df['상세주소'].apply(get_broad_region)

    with st.sidebar:
        st.header("📍 지역 필터")
        broad_regions = sorted([r for r in df["지역"].unique() if r not in ["미분류", "nan", "None"]])
        
        # [수정] 광역 선택도 상세지역처럼 드롭다운(selectbox)으로 변경하여 UI 통일
        selected_broad = st.selectbox(
            "1. 광역 선택", 
            ["지역을 선택하세요"] + broad_regions, 
            index=0
        )
        
        selected_city = "전체"
        if selected_broad != "지역을 선택하세요":
            st.write("---")
            broad_df = df[df["지역"] == selected_broad].copy()
            
            def get_city_safe(addr):
                parts = str(addr).split()
                return parts[1] if len(parts) > 1 else "기타"
                
            city_list = sorted(list(set(broad_df["상세주소"].apply(get_city_safe).values)))
            
            # 상세 지역 선택
            selected_city = st.selectbox(
                f"2. {selected_broad} 상세 지역", 
                ["전체"] + city_list,
                index=0
            )

    # 4. 결과 화면 제어
    if selected_broad == "지역을 선택하세요":
        st.write("---")
        st.info("👈 왼쪽 사이드바에서 **지역을 선택**하시면 식당 리스트가 나타납니다!")
        st.success("무무와 함께 행복한 나들이를 계획해 보세요! 🐾")
    else:
        broad_df = df[df["지역"] == selected_broad].copy()
        
        def get_city_safe(addr):
            parts = str(addr).split()
            return parts[1] if len(parts) > 1 else "기타"

        if selected_city == "전체":
            final_df = broad_df
        else:
            final_df = broad_df[broad_df["상세주소"].apply(get_city_safe) == selected_city]
        
        st.subheader(f"📍 {selected_broad} {selected_city if selected_city != '전체' else ''} 결과 ({len(final_df):,}건)")
        st.caption("💡 지도는 표를 오른쪽으로 밀어서 확인하세요.")

        # 테이블 표시
        st.dataframe(
            final_df[['업소명', '업종', '상세주소', '지도보기']],
            use_container_width=True,
            column_config={
                "지도보기": st.column_config.LinkColumn("네이버 지도", display_text="보기 🔗")
            },
            hide_index=True
        )

# 5. 하단 출처 및 안내문구 (수정 없음)
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
