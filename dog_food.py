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

# 2. 데이터 로드 로직 (API 동기화 생략/파일 우선)
df = None
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            df = pd.DataFrame(cache_data)
    except:
        st.error("데이터 파일을 읽는 중 오류가 발생했습니다.")

# 3. 사용자 인터페이스 (지역 선택 시에만 출력)
if df is not None and not df.empty:
    df['지도보기'] = df.apply(create_naver_link, axis=1)
    df['지역'] = df['상세주소'].apply(lambda x: str(x).split()[0] if str(x).split() else "미분류")

    st.sidebar.header("📍 지역 필터")
    broad_regions = sorted(df["지역"].unique())
    
    # [수정] 초기값을 "선택하세요"로 설정
    selected_broad = st.sidebar.selectbox("1. 광역 선택", ["지역을 선택하세요"] + broad_regions, index=0)
    
    if selected_broad == "지역을 선택하세요":
        # 초기 화면 메시지
        st.write("---")
        st.info("👈 왼쪽 사이드바에서 **지역을 선택**하시면 반려동물 동반 가능 식당 리스트가 나타납니다!")
        st.success("무무와 함께 행복한 나들이를 계획해 보세요! 🐾")
    else:
        broad_df = df[df["지역"] == selected_broad].copy()
        city_list = sorted(list(set(broad_df["상세주소"].apply(lambda x: str(x).split()[1] if len(str(x).split()) > 1 else "전체"))))
        selected_city = st.sidebar.selectbox("2. 상세 지역 선택", ["전체"] + city_list)
        
        final_df = broad_df if selected_city == "전체" else broad_df[broad_df["상세주소"].str.contains(selected_city, na=False)]
        
        st.subheader(f"📍 {selected_broad} {selected_city if selected_city != '전체' else ''} 검색 결과 ({len(final_df):,}건)")
        st.caption("💡 표를 오른쪽으로 밀면 네이버 지도 링크를 확인할 수 있습니다.")

        # 테이블 표시
        st.dataframe(
            final_df[['업소명', '업종', '상세주소', '지도보기']],
            use_container_width=True,
            column_config={
                "지도보기": st.column_config.LinkColumn("네이버 지도", display_text="보기 🔗")
            },
            hide_index=True
        )

# 5. 하단 공고
st.divider()
st.markdown(f"""
    <div style="font-size: 0.8rem; color: #555; text-align: center; line-height: 1.6; background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee;">
        <p><b>[ 안내 및 책임 한계 고지 ]</b></p>
        본 서비스는 <b>반려동물과 함께하는 행복한 일상을 위해 제작된 단순 정보 제공용 비영리 사이트</b>입니다.<br>
        실시간 영업 상황은 반영이 어려우니 <b>방문 전 반드시 유선으로 확인</b>해 주시기 바랍니다.<br>
        ⓒ 2026. <b>mumuabba</b>. All rights reserved. | 출처: 식약처 식품안전나라
    </div>
""", unsafe_allow_html=True)
