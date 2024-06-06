import pandas as pd
import streamlit as st
import plotly.express as px

# CSV 파일 경로
csv_file_path = 'agri_certifi_data.xls'
pd.set_option('display.max_columns', None)
# CSV 파일 읽기
df = pd.read_excel(csv_file_path)
df[['시도', '읍면', '리동']] = df['주소'].str.split(' ', expand=True, n=2)

st.title('농가 관리 프로그램')

# 인증기간을 시작일과 종료일로 분리
df['인증시작'] = pd.to_datetime(df['인증기간'].str.split(' ~ ').str[0], format='%Y.%m.%d')
df['인증끝'] = pd.to_datetime(df['인증기간'].str.split(' ~ ').str[1], format='%Y.%m.%d')

시도 = st.selectbox('시도 검색', ['', '서울', '부산', '대구', '인천', '광주', '대전', '울산',
                             '경기', '강원', '충청북도', '충청남도', '세종', '전라남도', '전라북도', '경상북도',
                             '경상남도', '제주'])

상세지역 = st.text_input('상세지역 검색')
대표품목 = st.text_input('대표품목 검색')
인증분류 = st.selectbox('인증분류 검색', ['', '유기농', '무농약'])
인증기관 = st.selectbox('인증기관 검색', [''] + df['인증기관'].unique().tolist())

# 재배면적 슬라이더
면적_min, 면적_max = int(df['재배면적(제곱미터)'].min()), int(df['재배면적(제곱미터)'].max())
재배면적 = st.slider('재배면적 범위 선택(제곱미터)', 면적_min, 면적_max, (면적_min, 면적_max))

# 인증계획량 슬라이더
계획량_min, 계획량_max = int(df['인증계획량(kg)'].min()), int(df['인증계획량(kg)'].max())
인증계획량 = st.slider('인증계획량 범위 선택(kg)', 계획량_min, 계획량_max, (계획량_min, 계획량_max))

# 인증기간 슬라이더 추가
인증시작 = st.date_input('인증 시작일', value=pd.to_datetime(df['인증시작']).min(), min_value=pd.to_datetime(df['인증시작']).min(), max_value=pd.to_datetime(df['인증끝']).max())
인증끝 = st.date_input('인증 종료일', value=pd.to_datetime(df['인증끝']).max(), min_value=pd.to_datetime(df['인증시작']).min(), max_value=pd.to_datetime(df['인증끝']).max())

# 날짜 입력값을 datetime으로 변환
인증시작 = pd.to_datetime(인증시작)
인증끝 = pd.to_datetime(인증끝)

# 검색 조건에 따라 데이터프레임 필터링
filtered_df = df[
    (df['시도'].str.contains(시도, case=False, na=False)) &
    (df['주소'].str.contains(상세지역, case=False, na=False)) &
    (df['대표품목'].str.contains(대표품목, case=False, na=False)) &
    (df['인증분류'].str.contains(인증분류, case=False, na=False)) &
    (df['인증기관'].str.contains(인증기관, case=False, na=False)) &
    (df['재배면적(제곱미터)'] >= 재배면적[0]) & (df['재배면적(제곱미터)'] <= 재배면적[1]) &
    (df['인증계획량(kg)'] >= 인증계획량[0]) & (df['인증계획량(kg)'] <= 인증계획량[1]) &
    (df['인증시작'] >= 인증시작) & (df['인증끝'] <= 인증끝)
]

# 필터링된 데이터프레임 표시
st.write(filtered_df)

# 엑셀 파일로 저장
@st.cache_data
def convert_df_to_excel(df):
    return df.to_excel("filtered_data.xlsx", index=False)

if st.button('엑셀로 저장'):
    convert_df_to_excel(filtered_df)
    st.success('파일이 엑셀로 저장되었습니다.')

# 시도별 재배면적 합계 시각화
st.subheader('시도별 재배면적 합계')
area_by_region = filtered_df.groupby('시도')['재배면적(제곱미터)'].sum().reset_index()
fig_area = px.bar(area_by_region, x='시도', y='재배면적(제곱미터)', title='시도별 재배면적 합계')
st.plotly_chart(fig_area)

# 시도별 인증계획량 합계 시각화
st.subheader('시도별 인증계획량 합계')
plan_by_region = filtered_df.groupby('시도')['인증계획량(kg)'].sum().reset_index()
fig_plan = px.bar(plan_by_region, x='시도', y='인증계획량(kg)', title='시도별 인증계획량 합계')
st.plotly_chart(fig_plan)

# 지역 선택
selected_region = st.selectbox('지역 선택', filtered_df['시도'].unique())

# 선택된 지역의 원그래프 시각화
st.subheader(f'{selected_region} 지역의 인증계획량 분포 (상위 5개 품목 + 기타)')
regional_data = filtered_df[filtered_df['시도'] == selected_region]
product_plan = regional_data.groupby('대표품목')['인증계획량(kg)'].sum().reset_index()
product_plan = product_plan.sort_values(by='인증계획량(kg)', ascending=False)

if len(product_plan) > 5:
    top5_products = product_plan[:5]
    other_products = product_plan[5:]
    other_sum = pd.DataFrame([{'대표품목': '기타', '인증계획량(kg)': other_products['인증계획량(kg)'].sum()}])
    product_plan = pd.concat([top5_products, other_sum], ignore_index=True)

fig_pie = px.pie(product_plan, values='인증계획량(kg)', names='대표품목', title=f'{selected_region} 지역의 인증계획량 분포')
st.plotly_chart(fig_pie)
