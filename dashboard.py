import sqlite3

import altair as alt
import pandas as pd
import streamlit as st


DB_PATH = "farm.db"


st.set_page_config(
    page_title="FarmPulse Control Center",
    page_icon="Farm",
    layout="wide",
)


@st.cache_data(ttl=15)
def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            """
            SELECT id, moisture, temperature, weather_temp, timestamp
            FROM data
            ORDER BY timestamp ASC
            """,
            conn,
        )
    finally:
        conn.close()

    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df["weather_gap"] = df["temperature"] - df["weather_temp"]
    df["hour"] = df["timestamp"].dt.floor("H")
    df["day"] = df["timestamp"].dt.floor("D")
    return df


def metric_delta(series: pd.Series, suffix: str) -> str:
    if len(series) < 2:
        return "Waiting for prior sample"
    delta_value = series.iloc[-1] - series.iloc[-2]
    sign = "+" if delta_value >= 0 else ""
    return f"{sign}{delta_value:.1f}{suffix} vs last sample"


def status_badge(label: str, tone: str) -> str:
    palette = {
        "good": ("#e7f7eb", "#14532d"),
        "warn": ("#fff4d6", "#8a5b07"),
        "bad": ("#fee4e2", "#9f1d14"),
        "info": ("#e5f2ff", "#0f4f8a"),
    }
    background, foreground = palette[tone]
    return (
        f"<span style='display:inline-flex;align-items:center;gap:0.4rem;"
        f"padding:0.45rem 0.85rem;border-radius:999px;background:{background};"
        f"color:{foreground};font-size:0.92rem;font-weight:700;'>{label}</span>"
    )


st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 15% 10%, rgba(253, 224, 71, 0.16), transparent 22%),
            radial-gradient(circle at 85% 18%, rgba(74, 222, 128, 0.18), transparent 18%),
            radial-gradient(circle at 70% 70%, rgba(14, 165, 233, 0.10), transparent 18%),
            linear-gradient(180deg, #f7f2e7 0%, #eef5e9 45%, #f7f8f4 100%);
        color: #163026;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(245, 242, 235, 0.98), rgba(233, 240, 232, 0.98));
        border-right: 1px solid rgba(22, 48, 38, 0.08);
    }
    .block-container {
        max-width: 1320px;
        padding-top: 2rem;
        padding-bottom: 2.5rem;
    }
    .hero-card, .glass-card, .insight-card {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid rgba(22, 48, 38, 0.08);
        border-radius: 28px;
        box-shadow: 0 24px 60px rgba(22, 48, 38, 0.09);
        backdrop-filter: blur(10px);
    }
    .hero-card {
        padding: 2rem 2.1rem 1.7rem;
        margin-bottom: 1.3rem;
    }
    .glass-card {
        padding: 1.2rem 1.25rem;
        min-height: 182px;
    }
    .insight-card {
        padding: 1.25rem 1.3rem;
        min-height: 145px;
    }
    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.18em;
        font-size: 0.75rem;
        font-weight: 800;
        color: #5b6c73;
        margin-bottom: 0.75rem;
    }
    .hero-title {
        font-size: 3.1rem;
        line-height: 0.95;
        font-weight: 900;
        color: #123123;
        max-width: 14ch;
        margin-bottom: 0.8rem;
    }
    .hero-copy {
        font-size: 1.02rem;
        color: #455a64;
        max-width: 54rem;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.28rem;
        font-weight: 900;
        color: #17382b;
        margin-bottom: 0.75rem;
    }
    .mini-label {
        color: #5f7280;
        font-size: 0.92rem;
        margin-bottom: 0.35rem;
    }
    .mini-stat {
        font-size: 1.95rem;
        font-weight: 900;
        color: #163026;
        margin: 0.35rem 0 0.55rem;
    }
    .muted {
        color: #62757f;
        font-size: 0.95rem;
    }
    .alert-good, .alert-warn, .alert-bad, .alert-info {
        border-radius: 18px;
        padding: 0.95rem 1rem;
        border: 1px solid rgba(22, 48, 38, 0.08);
        margin-bottom: 0.7rem;
        font-weight: 650;
        line-height: 1.45;
    }
    .alert-good {
        background: #e7f7eb;
        color: #14532d;
    }
    .alert-warn {
        background: #fff4d6;
        color: #8a5b07;
    }
    .alert-bad {
        background: #fee4e2;
        color: #9f1d14;
    }
    .alert-info {
        background: #e5f2ff;
        color: #0f4f8a;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid rgba(22, 48, 38, 0.08);
        border-radius: 24px;
        box-shadow: 0 20px 45px rgba(22, 48, 38, 0.07);
        padding: 1rem;
    }
    div[data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.72);
        border-radius: 22px;
        padding: 0.25rem;
    }
    .chart-shell {
        background: rgba(255, 255, 255, 0.76);
        border: 1px solid rgba(22, 48, 38, 0.08);
        border-radius: 28px;
        padding: 1rem 1rem 0.5rem;
        box-shadow: 0 22px 48px rgba(22, 48, 38, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def build_trend_chart(dataframe: pd.DataFrame) -> alt.Chart:
    melted = dataframe.melt(
        id_vars="timestamp",
        value_vars=["moisture", "temperature", "weather_temp"],
        var_name="metric",
        value_name="value",
    )
    color_scale = alt.Scale(
        domain=["moisture", "temperature", "weather_temp"],
        range=["#2f855a", "#d97706", "#2563eb"],
    )
    return (
        alt.Chart(melted)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("timestamp:T", title="Time"),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color("metric:N", scale=color_scale, title="Series"),
            tooltip=[
                alt.Tooltip("timestamp:T", title="Timestamp"),
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("value:Q", title="Value", format=".2f"),
            ],
        )
        .properties(height=355)
        .configure_view(strokeOpacity=0)
        .configure_axis(labelColor="#5b6c73", titleColor="#32444d", gridColor="#dbe5de")
        .configure_legend(labelColor="#32444d", titleColor="#32444d", orient="bottom")
    )


def build_daily_chart(dataframe: pd.DataFrame) -> alt.Chart:
    melted = dataframe.melt(
        id_vars="day",
        value_vars=["moisture", "temperature", "weather_temp"],
        var_name="metric",
        value_name="value",
    )
    color_scale = alt.Scale(
        domain=["moisture", "temperature", "weather_temp"],
        range=["#76c893", "#f4a261", "#5dade2"],
    )
    return (
        alt.Chart(melted)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("day:T", title="Day"),
            y=alt.Y("value:Q", title="Daily average"),
            color=alt.Color("metric:N", scale=color_scale, title="Series"),
            xOffset="metric:N",
            tooltip=[
                alt.Tooltip("day:T", title="Day"),
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("value:Q", title="Average", format=".2f"),
            ],
        )
        .properties(height=355)
        .configure_view(strokeOpacity=0)
        .configure_axis(labelColor="#5b6c73", titleColor="#32444d", gridColor="#dbe5de")
        .configure_legend(labelColor="#32444d", titleColor="#32444d", orient="bottom")
    )


df = load_data()

st.sidebar.title("Mission Control")
samples = st.sidebar.slider("Samples in focus", 24, 300, 96, step=12)
show_table = st.sidebar.checkbox("Show recent feed table", value=True)
st.sidebar.markdown("### Run Order")
st.sidebar.caption("1. Start Mosquitto")
st.sidebar.caption("2. Run ingest.py")
st.sidebar.caption("3. Run sensor.py")

if df.empty:
    st.markdown(
        """
        <div class="hero-card">
            <div class="eyebrow">FarmPulse Control Center</div>
            <div class="hero-title">Your live farm dashboard is ready for its first signal.</div>
            <div class="hero-copy">
                Start the MQTT broker, run <code>ingest.py</code>, then run <code>sensor.py</code>.
                Once readings arrive, this control center will populate with live KPIs, weather context,
                trend analysis, and alerts.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info("No readings found in farm.db yet.")
    st.stop()

window_df = df.tail(samples).copy()
latest = window_df.iloc[-1]
latest_time = latest["timestamp"]
first_time = window_df["timestamp"].iloc[0]
sample_span = latest_time - first_time
sample_age = str(pd.Timestamp.now() - latest_time).split(".")[0]

if latest["moisture"] < 30:
    moisture_state = ("Irrigation Needed", "bad")
elif latest["moisture"] < 45:
    moisture_state = ("Moisture Watch", "warn")
else:
    moisture_state = ("Healthy Soil", "good")

if latest["temperature"] > 32:
    climate_state = ("Heat Stress Risk", "bad")
elif latest["temperature"] > 27:
    climate_state = ("Warm Conditions", "warn")
else:
    climate_state = ("Stable Climate", "good")

if latest["weather_gap"] > 12:
    enclosure_state = ("Strong Indoor Buffer", "info")
else:
    enclosure_state = ("Outdoor Conditions Aligned", "good")

hourly_df = (
    df.groupby("hour")[["moisture", "temperature", "weather_temp", "weather_gap"]]
    .mean()
    .tail(12)
    .reset_index()
)
daily_df = (
    df.groupby("day")[["moisture", "temperature", "weather_temp"]]
    .mean()
    .tail(10)
    .reset_index()
)

st.markdown(
    f"""
    <div class="hero-card">
        <div class="eyebrow">FarmPulse Control Center</div>
        <div class="hero-title">Live field intelligence for your local IoT weather pipeline</div>
        <div class="hero-copy">
            A single operating view for soil conditions, greenhouse heat, and outdoor weather.
            Latest reading landed at <b>{latest_time.strftime("%Y-%m-%d %I:%M:%S %p")}</b>,
            and the active view covers <b>{sample_span}</b> of farm activity.
        </div>
        {status_badge(moisture_state[0], moisture_state[1])}
        &nbsp;
        {status_badge(climate_state[0], climate_state[1])}
        &nbsp;
        {status_badge(enclosure_state[0], enclosure_state[1])}
    </div>
    """,
    unsafe_allow_html=True,
)

kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
kpi_1.metric("Soil Moisture", f"{latest['moisture']:.1f}%", metric_delta(window_df["moisture"], "%"))
kpi_2.metric(
    "Field Temperature",
    f"{latest['temperature']:.1f} C",
    metric_delta(window_df["temperature"], " C"),
)
kpi_3.metric(
    "Outdoor Weather",
    f"{latest['weather_temp']:.1f} C",
    metric_delta(window_df["weather_temp"], " C"),
)
kpi_4.metric(
    "Weather Gap",
    f"{latest['weather_gap']:.1f} C",
    metric_delta(window_df["weather_gap"], " C"),
)

info_1, info_2, info_3 = st.columns([1.1, 1.1, 1.25])

with info_1:
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="section-title">Field Snapshot</div>
            <div class="mini-label">Coverage window</div>
            <div class="mini-stat">{sample_span}</div>
            <div class="muted">
                Tracking {len(window_df)} readings from
                {first_time.strftime("%b %d %I:%M %p")} to {latest_time.strftime("%b %d %I:%M %p")}.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with info_2:
    irrigation_band = "Optimal" if latest["moisture"] >= 45 else "Monitor" if latest["moisture"] >= 30 else "Low"
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="section-title">Operations Signal</div>
            <div class="mini-label">Current irrigation band</div>
            <div class="mini-stat">{irrigation_band}</div>
            <div class="muted">
                Avg moisture in focus: {window_df["moisture"].mean():.1f}%<br>
                Avg field temp in focus: {window_df["temperature"].mean():.1f} C
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with info_3:
    st.markdown('<div class="insight-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Smart Alerts</div>', unsafe_allow_html=True)

    alerts = []
    if latest["moisture"] < 30:
        alerts.append(("bad", "Soil moisture is critically low. Irrigation should be scheduled now."))
    elif latest["moisture"] < 45:
        alerts.append(("warn", "Moisture is trending low. Watch the next few samples before sunrise."))
    else:
        alerts.append(("good", "Soil moisture is within a healthy operating zone."))

    if latest["temperature"] > 32:
        alerts.append(("bad", "Heat stress risk is elevated. Consider airflow or shade control."))
    elif latest["temperature"] > 27:
        alerts.append(("warn", "Field temperature is warm. Ventilation may help stabilize the zone."))
    else:
        alerts.append(("good", "Field temperature is stable for routine operation."))

    if latest["weather_temp"] < 5:
        alerts.append(("info", "Outdoor weather is cold. Protect sensitive plants if they are exposed."))

    for tone, message in alerts:
        st.markdown(f'<div class="alert-{tone}">{message}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

overview_tab, analysis_tab = st.tabs(["Overview", "Analysis"])

with overview_tab:
    chart_left, chart_right = st.columns([1.35, 1])
    with chart_left:
        st.markdown('<div class="chart-shell">', unsafe_allow_html=True)
        st.markdown("### Live Trend Lines")
        st.altair_chart(build_trend_chart(window_df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_right:
        st.markdown('<div class="chart-shell">', unsafe_allow_html=True)
        st.markdown("### Daily Performance")
        st.altair_chart(build_daily_chart(daily_df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if show_table:
        table_col, summary_col = st.columns([1.45, 0.9])
        with table_col:
            st.markdown("### Recent Sensor Feed")
            display_df = window_df.copy()
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(display_df.iloc[::-1], use_container_width=True, hide_index=True)

        with summary_col:
            summary_df = pd.DataFrame(
                {
                    "Metric": [
                        "Total Samples",
                        "Latest Sample Age",
                        "Avg Moisture",
                        "Avg Field Temp",
                        "Avg Weather Temp",
                        "Peak Weather Gap",
                    ],
                    "Value": [
                        len(df),
                        sample_age,
                        f"{df['moisture'].mean():.1f}%",
                        f"{df['temperature'].mean():.1f} C",
                        f"{df['weather_temp'].mean():.1f} C",
                        f"{df['weather_gap'].max():.1f} C",
                    ],
                }
            )
            st.markdown("### Farm Summary")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

with analysis_tab:
    a_col, b_col = st.columns(2)
    with a_col:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title">Hourly Rhythm</div>
                <div class="muted">
                    Over the last {len(hourly_df)} hourly buckets, moisture averaged
                    <b>{hourly_df['moisture'].mean():.1f}%</b> and field temperature averaged
                    <b>{hourly_df['temperature'].mean():.1f} C</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(
            hourly_df.assign(hour=hourly_df["hour"].dt.strftime("%Y-%m-%d %H:%M")),
            use_container_width=True,
            hide_index=True,
        )

    with b_col:
        recommendation = "Keep current irrigation cadence."
        if latest["moisture"] < 30:
            recommendation = "Increase irrigation priority and verify soil probe placement."
        elif latest["temperature"] > 32:
            recommendation = "Consider cooling or airflow improvements during warm periods."
        elif latest["weather_gap"] > 12:
            recommendation = "Indoor conditions are well buffered from the weather. Monitor energy tradeoffs."

        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title">Operator Recommendation</div>
                <div class="mini-stat">{recommendation}</div>
                <div class="muted">
                    This recommendation is based on the latest moisture, field temperature,
                    and indoor-to-outdoor gap visible in the active sample window.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        export_df = df.copy()
        export_df["timestamp"] = export_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Export full dataset as CSV",
            csv,
            file_name="farm_data_export.csv",
            mime="text/csv",
            use_container_width=True,
        )
