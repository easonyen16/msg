import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
import requests
import io

# --- 設定 ---
CSV_URL = "https://msg.nogi46.me/analysis.csv"
date_format = "%Y-%m-%d %H:%M:%S"

# --- 讀取資料 ---
@st.cache_data
def load_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(CSV_URL, headers=headers)
    response.raise_for_status()
    df = pd.read_csv(io.BytesIO(response.content), names=["time", "user", "member", "status"], header=None)
    df["time"] = pd.to_datetime(df["time"], format=date_format)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ 無法載入資料：{e}")
    st.stop()

# --- 側邊欄：時間範圍 ---
st.sidebar.title("📅 選擇時間範圍")
today = df["time"].max().normalize()
time_filter = st.sidebar.radio("範圍", ["全部", "最近一個月", "最近一週"])

if time_filter == "最近一週":
    df = df[df["time"] >= today - timedelta(days=7)]
elif time_filter == "最近一個月":
    df = df[df["time"] >= today - timedelta(days=30)]

st.title("📊 Access Log 分析工具")
st.caption("資料筆數：{} 筆".format(len(df)))

# --- 額外選項 ---
st.sidebar.title("⚙️ 顯示選項")
log_scale = st.sidebar.checkbox("使用對數刻度 (Log scale)", value=False)
show_top_n = st.sidebar.checkbox("只顯示前/後 N 名", value=True)
rank_order = st.sidebar.radio("顯示排序", ["前 N 名", "後 N 名"])
top_n = st.sidebar.slider("N 名數量", min_value=5, max_value=50, value=10)

# --- 每日趨勢 ---
df_day = df.copy()
df_day["date"] = df_day["time"].dt.date
count_by_day = df_day.groupby("date").size().reset_index(name="count")
fig_day = px.line(count_by_day, x="date", y="count", title="每日存取次數趨勢")
st.plotly_chart(fig_day, use_container_width=True)

# --- 每小時分布 ---
df["hour"] = df["time"].dt.hour
count_by_hour = df.groupby("hour").size().reset_index(name="count")
fig_hour = px.bar(count_by_hour, x="hour", y="count", title="每小時存取分布（0~23時）", text="count")
fig_hour.update_traces(textposition='outside')
st.plotly_chart(fig_hour, use_container_width=True)

# --- 使用者統計 ---
count_by_user = df["user"].value_counts().reset_index()
count_by_user.columns = ["使用者", "次數"]
if show_top_n:
    if rank_order == "前 N 名":
        count_by_user = count_by_user.head(top_n)
    else:
        count_by_user = count_by_user.tail(top_n)
fig_user = px.bar(count_by_user, x="使用者", y="次數", title="使用者存取次數", text="次數", log_y=log_scale)
fig_user.update_traces(textposition="outside")
st.plotly_chart(fig_user, use_container_width=True)

# --- 成員統計 ---
count_by_member = df["member"].value_counts().reset_index()
count_by_member.columns = ["成員", "次數"]
if show_top_n:
    if rank_order == "前 N 名":
        count_by_member = count_by_member.head(top_n)
    else:
        count_by_member = count_by_member.tail(top_n)
fig_member = px.bar(count_by_member, x="成員", y="次數", title="成員被查詢次數", text="次數", log_y=log_scale)
fig_member.update_traces(textposition="outside")
st.plotly_chart(fig_member, use_container_width=True)

# --- 狀態統計 ---
count_by_status = df["status"].value_counts().reset_index()
count_by_status.columns = ["狀態", "次數"]
fig_status = px.pie(count_by_status, names="狀態", values="次數", title="狀態統計", hole=0.3)
fig_status.update_traces(textinfo="label+percent+value")
st.plotly_chart(fig_status, use_container_width=True)

# --- 原始資料表格（可搜尋與過濾） ---
st.subheader("🔍 原始紀錄")
search_user = st.text_input("搜尋使用者：")
search_member = st.text_input("搜尋成員：")
selected_status = st.multiselect("篩選狀態：", options=df["status"].unique().tolist(), default=df["status"].unique().tolist())

filtered_df = df.copy()
if search_user:
    filtered_df = filtered_df[filtered_df["user"].str.contains(search_user)]
if search_member:
    filtered_df = filtered_df[filtered_df["member"].str.contains(search_member)]
if selected_status:
    filtered_df = filtered_df[filtered_df["status"].isin(selected_status)]

st.dataframe(filtered_df.sort_values("time", ascending=False), use_container_width=True)
