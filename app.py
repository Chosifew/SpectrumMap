# bug
# * 点击“显示热力图”后每次点击地图都会刷新第二张地图，我要的是点击显示热力图才更新一次
# * 只能纬度在前，复选框没有真正起到做作用。且祥云从点击“设置地图中心”后就能立即更新。
# todo
# * 添加一个zoom的输入框放在输入经纬度旁边，点击按钮后一次性更新。
# * 查阅插件HeatMapWithTime
# * 添加经纬度查阅窗口
# * 添加保存按钮
# * 删除特定数据
# * 数据导入按钮

import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
import random
from rtlsdr import RtlSdr

# 全局变量，用于存储点击事件的数据
if 'click_data' not in st.session_state:
    st.session_state['click_data'] = []

# 记录上一次点击的位置
if 'last_click' not in st.session_state:
    st.session_state['last_click'] = None

# 地图中心位置
if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [39.959965, 116.351205]

# 地图缩放等级
if 'zoom_level' not in st.session_state:
    st.session_state['zoom_level'] = 16

# 从RTL-SDR获取功率值的函数（同步阻塞版本）
def get_power_value(lat, lon):
    # 这里调用实际的RTL-SDR函数
    # 例如：return rtl_sdr.get_power(lat, lon)
    # 模拟返回一个随机功率值
    # 初始化RTL-SDR
	sdr = RtlSdr()
	sdr.sample_rate = 2.048e6  # 采样率，单位Hz
	sdr.center_freq = 103.9e6    # 中心频率，单位Hz
	sdr.freq_correction = 60   # 频率校正，单位PPM
	sdr.gain = 'auto'          # 自动增益

	# 读取样本
	sample_count = 4096
	samples = sdr.read_samples(sample_count)
	sdr.close()

	# 计算FFT
	fft_size = 512
	fft_result = np.fft.fftshift(np.fft.fft(samples, fft_size))
	fft_freqs = np.fft.fftshift(np.fft.fftfreq(fft_size, 1/sdr.sample_rate))

	# 转换为dB
	power_spectrum = 10 * np.log10(np.abs(fft_result)**2)

	# 查找具体频点的功率
	target_freq = 103.9e6  # 目标频点，单位Hz
	freq_index = np.argmin(np.abs(fft_freqs + sdr.center_freq - target_freq))
	return power_spectrum[freq_index]
    # return np.random.normal(1,1)

# 创建第一个folium地图
m1 = folium.Map(location=st.session_state['map_center'], zoom_start=st.session_state['zoom_level'])

# 显示第一个地图并捕获输出
output = st_folium(m1, width=700, height=500, key='map1')

# 检查是否有点击事件
if output and output.get('last_clicked'):
    click_lat = output['last_clicked']['lat']
    click_lon = output['last_clicked']['lng']
    
    # 检查点击是否有效（与上次点击的位置是否不同）
    if st.session_state['last_click'] is None or (abs(click_lat - st.session_state['last_click'][0]) > 0.0001 or abs(click_lon - st.session_state['last_click'][1]) > 0.0001):
        power_value = get_power_value(click_lat, click_lon)
        st.session_state['click_data'].append([click_lat, click_lon, power_value])
        st.session_state['last_click'] = (click_lat, click_lon)
        folium.Marker(
            location=[click_lat, click_lon],
            popup=f"Lat: {click_lat}, Lon: {click_lon}, Power: {power_value}"
        ).add_to(m1)

# 在页面上添加一个按钮，点击后在第二个地图上显示热力图
if st.button("显示热力图"):
    st.session_state['show_heatmap'] = True

# 创建第二个folium地图
m2 = folium.Map(location=st.session_state['map_center'], zoom_start=st.session_state['zoom_level'])

# 添加热力图层（如果按钮被点击）
if st.session_state.get('show_heatmap') and st.session_state['click_data']:
    HeatMap(st.session_state['click_data']).add_to(m2)

# 显示第二个地图
st_folium(m2, width=700, height=500, key='map2')

# 显示点击事件记录
if st.session_state['click_data']:
    st.write("点击事件记录：")
    df = pd.DataFrame(st.session_state['click_data'], columns=['lat', 'lon', 'power'])
    st.write(df)

# 添加输入框、复选框和按钮来调整地图中心位置
coordinate_format = st.checkbox('经度在前', value=False)
default_text = "示例：39.959965, 116.351205（纬度，经度）" if not coordinate_format else "示例：116.351205, 39.959965（经度，纬度）"
coordinates = st.text_input('输入经纬度', value=default_text)

if st.button("设置地图中心"):
    try:
        lat, lon = map(float, coordinates.split(','))
        if coordinate_format:
            lat, lon = lon, lat
        st.session_state['map_center'] = [lat, lon]
        m1.location = [lat, lon]
        m2.location = [lat, lon]
    except ValueError:
        st.error("请输入有效的经纬度")