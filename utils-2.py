import pandas as pd  # 👈 補上此行匯入 pandas 套件
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import utils  # 載入 utils.py 模組

# 設定網頁標題與寬版版面
st.set_page_config(
    page_title="FOG Vibration Diagnostic System", layout="wide"
)

# 主標題與副標題
st.markdown(
    "# 🔍 Fiber Optic Gyroscope (FOG) Real-Time Vibration Diagnostic System"
)
st.caption(
    "Engineering B: Real-Time Vibration Diagnostics & ISO 10816 Standard"
    " Evaluation"
)

# ---------------------------------------------------------
# 側邊欄：Data Import & Settings
# ---------------------------------------------------------
st.sidebar.header("⚙️ Data Import & Settings")

uploaded_file = st.sidebar.file_uploader(
    "Upload FOG Experimental Data (.xlsx / .csv)", type=["csv", "xlsx"]
)

sampling_rate = st.sidebar.number_input(
    "Sampling Rate (Hz)", value=10000, step=1000
)

# Sensor Scale Factor K 設定欄位
scale_factor = st.sidebar.number_input(
    "Sensor Scale Factor K (mm/s per V)", value=1.00, step=0.10
)

machine_class = st.sidebar.selectbox(
    "Select ISO 10816 Machine Class",
    [
        "Class I (Precision Instruments)",
        "Class II (Medium Machines)",
        "Class III (Large Rigid Foundation)",
        "class IV (Large Flexible Foundation)",
    ],
)

if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)

    st.sidebar.success(f"Successfully Loaded: {uploaded_file.name}")

    col_options = df.columns.tolist()
    selected_col = st.sidebar.selectbox(
        "Select Vibration Signal Column", col_options
    )

    # 1. 取得數據並清洗
    raw_signal = (
        pd.to_numeric(df[selected_col], errors="coerce").dropna().to_numpy()
    )
    cleaned_signal = utils.filter_invalid_data(raw_signal)

    if len(cleaned_signal) == 0:
      st.error("Selected column contains no valid numerical data.")
    else:
      # 2. 直流偏置消除
      corrected_signal, mean_dc = utils.remove_dc_offset(cleaned_signal)

      # 3. 帶入 Scale Factor K 進行單位轉換算
      velocity_signal = utils.apply_scale_factor(
          corrected_signal, scale_factor=scale_factor
      )

      # 4. 計算 RMS
      v_rms = utils.calculate_rms(velocity_signal)

      # 5. 比對 ISO 10816
      zone, color, desc = utils.classify_iso10816(
          v_rms, machine_class=machine_class
      )

      # 6. FFT 計算與峰值尋找
      freq, amplitude = utils.calculate_fft(velocity_signal, fs=sampling_rate)
      top_freqs, top_amps = utils.find_top_peaks(freq, amplitude, top_n=3)

      dominant_freq = top_freqs[0] if len(top_freqs) > 0 else 0.0
      peak_amp = top_amps[0] if len(top_amps) > 0 else 0.0

      st.markdown("---")

      # ---------------------------------------------------------
      # 區塊一：📌 Executive Summary & Health Diagnostics
      # ---------------------------------------------------------
      st.markdown("### 📌 Executive Summary & Health Diagnostics")

      col_card, col_metrics = st.columns([1.2, 1.8])

      with col_card:
        st.markdown(
            f"""
                    <div style="background-color: {color}; padding: 25px; border-radius: 12px; color: white; height: 100%;">
                        <h1 style="color: white; margin: 0; font-size: 38px;">{zone}</h1>
                        <br><br>
                        <p style="font-size: 16px; margin: 0; line-height: 1.4;">{desc}</p>
                    </div>
                    """,
            unsafe_allow_html=True,
        )

      with col_metrics:
        m1, m2 = st.columns(2)
        with m1:
          st.caption("RMS Velocity")
          st.markdown(f"## {v_rms:.3f}")
        with m2:
          st.caption("Dominant Frequency")
          st.markdown(f"## {dominant_freq:.1f} Hz")

        st.markdown("<br>", unsafe_allow_html=True)

        d1, d2 = st.columns(2)
        with d1:
          st.caption(f"DC Offset Corrected: {mean_dc:.4f}")
        with d2:
          st.caption(f"Peak Amplitude: {peak_amp:.4f}")

      st.markdown("---")

      # ---------------------------------------------------------
      # 區塊二：📌 Core Engineering Signal Analysis
      # ---------------------------------------------------------
      st.markdown("### 📌 Core Engineering Signal Analysis")

      fig_col1, fig_col2 = st.columns(2)

      with fig_col1:
        st.markdown(
            f"**Figure A: Time-Domain Waveform (Showing"
            f" {len(velocity_signal)} points)**"
        )
        fig_a = go.Figure()
        fig_a.add_trace(
            go.Scatter(
                y=velocity_signal,
                mode="lines",
                line=dict(color="#0066cc", width=1.2),
            )
        )
        fig_a.update_layout(
            xaxis_title=f"Sample Index (Total: {len(velocity_signal)} points)",
            yaxis_title="Amplitude",
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="white",
        )
        st.plotly_chart(fig_a, use_container_width=True)

      with fig_col2:
        st.markdown("**Figure B: FFT Frequency Spectrum**")
        fig_b = go.Figure()
        fig_b.add_trace(
            go.Scatter(
                x=freq,
                y=amplitude,
                mode="lines",
                line=dict(color="#ff0000", width=1.2),
            )
        )
        fig_b.update_layout(
            xaxis_title="Frequency (Hz)",
            yaxis_title="Magnitude",
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="white",
        )
        st.plotly_chart(fig_b, use_container_width=True)

      st.markdown("---")

      # ---------------------------------------------------------
      # 區塊三：📌 Standards Reference & Raw Data
      # ---------------------------------------------------------
      st.markdown("### 📌 Standards Reference & Raw Data")

      with st.expander(
          "📖 View Complete ISO 10816-3 Threshold Criteria (All Machine"
          " Classes)"
      ):
        st.write("""
                * **Class I (Precision Instruments)**: Zone A ≤ 0.28, Zone B ≤ 0.71, Zone C ≤ 1.80 (mm/s)
                * **Class II (Medium Machines)**: Zone A ≤ 0.71, Zone B ≤ 1.80, Zone C ≤ 4.50 (mm/s)
                * **Class III (Large Rigid Foundation)**: Zone A ≤ 1.40, Zone B ≤ 2.80, Zone C ≤ 4.50 (mm/s)
                * **Class IV (Large Flexible Foundation)**: Zone A ≤ 2.30, Zone B ≤ 4.50, Zone C ≤ 7.10 (mm/s)
                """)

      with st.expander("📊 View Uploaded Raw Dataset"):
        st.dataframe(df)

  except Exception as e:
    st.error(f"An error occurred during analysis: {e}")
else:
  st.info("👈 Please upload a data file from the sidebar to begin analysis.")