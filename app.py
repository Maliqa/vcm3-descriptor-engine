import streamlit as st
import math

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(page_title="VCM-3 Smart Configurator v3.1", layout="wide")

st.title("VCM-3 Smart Configurator v3.1")
st.caption("Basic Mode (Junior) + Advanced Mode (Senior)")

# =========================================================
# MODE SELECTION
# =========================================================

st.sidebar.header("Mode Selection")

mode = st.sidebar.radio(
    "Select Mode",
    ["Basic", "Advanced"],
    index=0
)

# =========================================================
# MACHINE INPUT
# =========================================================

st.sidebar.header("Machine Information")

rpm = st.sidebar.number_input("RPM", min_value=1, value=1500)
power_kw = st.sidebar.number_input("Motor Power (kW)", min_value=0.1, value=15.0)
foundation = st.sidebar.selectbox("Foundation Type", ["Rigid", "Soft"])
variable_speed = st.sidebar.checkbox("Variable Speed?")

machine_components = st.sidebar.multiselect(
    "Machine Composition",
    ["Motor", "Gearbox", "Fan", "Pump"],
    default=["Motor"]
)

# =========================================================
# FAULT STRATEGY
# =========================================================

st.sidebar.header("Fault Strategy")

fault_unbalance = st.sidebar.checkbox("Unbalance")
fault_misalignment = st.sidebar.checkbox("Misalignment")
fault_looseness = st.sidebar.checkbox("Looseness")
fault_gear = st.sidebar.checkbox("Gear Fault")
fault_bearing = st.sidebar.checkbox("Bearing Fault")

if mode == "Advanced":
    harmonic_order = st.sidebar.selectbox("Harmonic Coverage", [2,3,4,5,6], index=2)
else:
    harmonic_order = 3

gear_teeth = 0
sideband_order = 2

if fault_gear:
    gear_teeth = st.sidebar.number_input("Gear Teeth", min_value=1, value=30)
    if mode == "Advanced":
        sideband_order = st.sidebar.selectbox("Sideband ±nX", [1,2,3], index=1)

if fault_bearing and mode == "Advanced":
    envelope_upper = st.sidebar.selectbox("Envelope Upper (Hz)", [5000,8000,10000,15000], index=1)
else:
    envelope_upper = 8000

# =========================================================
# CORE ENGINE CALCULATION
# =========================================================

one_x = rpm / 60
harmonic_target = one_x * harmonic_order

gear_mesh = 0
sideband_upper = 0

if fault_gear:
    gear_mesh = gear_teeth * one_x
    sideband_upper = gear_mesh + (sideband_order * one_x)

# =========================================================
# LF / HF AUTO DESIGN
# =========================================================

# Default LF band (rotational faults)
lf_lower = max(one_x * 0.5, 1)
lf_upper = harmonic_target

# Default HF band
hf_lower = 500
hf_upper = envelope_upper if fault_bearing else max(sideband_upper, 2000)

# Advanced override
if mode == "Advanced":
    with st.sidebar.expander("Override LF / HF Band"):
        lf_lower = st.number_input("LF Lower (Hz)", value=float(lf_lower))
        lf_upper = st.number_input("LF Upper (Hz)", value=float(lf_upper))
        hf_lower = st.number_input("HF Lower (Hz)", value=float(hf_lower))
        hf_upper = st.number_input("HF Upper (Hz)", value=float(hf_upper))

# Highest frequency logic
highest_freq = max(lf_upper, hf_upper)
fmax = math.ceil(highest_freq * 1.2)

# =========================================================
# ISO CLASS AUTO
# =========================================================

if power_kw < 15:
    iso_class = "Class I"
    alert = 2.8
    danger = 4.5
elif power_kw < 75:
    iso_class = "Class II"
    alert = 4.5
    danger = 7.1
else:
    if foundation == "Rigid":
        iso_class = "Class III"
        alert = 7.1
        danger = 11.0
    else:
        iso_class = "Class IV"
        alert = 11.0
        danger = 18.0

# =========================================================
# MONITORING SUMMARY
# =========================================================

st.divider()
st.header("Monitoring Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("RPM", rpm)
col2.metric("1X Frequency", f"{one_x:.2f} Hz")
col3.metric("LF Band", f"{lf_lower:.1f} - {lf_upper:.1f} Hz")
col4.metric("HF Band", f"{hf_lower:.1f} - {hf_upper:.1f} Hz")

st.write(f"Highest Frequency: {highest_freq:.1f} Hz")
st.write(f"Recommended Fmax: {fmax} Hz")
st.write(f"ISO Class: {iso_class}")
st.write(f"Alert / Danger: {alert} / {danger} mm/s")
st.write(f"Current Mode: {mode}")

# =========================================================
# MINI EDUCATION MODE (BASIC)
# =========================================================

if mode == "Basic":
    with st.expander("Mini Vibration Education (Junior Mode)"):
        st.write("1X = RPM / 60 → Fundamental shaft frequency.")
        st.write("LF Band → Used for unbalance, misalignment, looseness.")
        st.write("HF Band → Used for bearing & gear impact detection.")
        st.write("Fmax → Must be higher than highest monitored frequency.")

# =========================================================
# ADVANCED ENGINEERING BREAKDOWN
# =========================================================

if mode == "Advanced":
    with st.expander("Engineering Calculation Breakdown"):
        st.write(f"1X = {one_x:.2f} Hz")
        st.write(f"Harmonic Target ({harmonic_order}X) = {harmonic_target:.2f} Hz")
        if fault_gear:
            st.write(f"Gear Mesh = {gear_mesh:.2f} Hz")
            st.write(f"Sideband Upper = {sideband_upper:.2f} Hz")
        if fault_bearing:
            st.write(f"Envelope Upper = {envelope_upper} Hz")
        st.write(f"LF Band = {lf_lower:.1f} - {lf_upper:.1f} Hz")
        st.write(f"HF Band = {hf_lower:.1f} - {hf_upper:.1f} Hz")
        st.write(f"Fmax = {fmax} Hz")

# =========================================================
# WORKSHEET TABS
# =========================================================

tabs = st.tabs([
    "Channels",
    "Descriptors",
    "Waveforms",
    "Alarm Setpoints"
])

# =========================================================
# CHANNELS TAB
# =========================================================

with tabs[0]:
    st.header("Channels Worksheet")

    if "Motor" in machine_components:
        for point in ["Motor_DE", "Motor_NDE"]:
            st.subheader(point)
            st.text_input(
                "Channel Name",
                value=f"{point}_H",
                disabled=True,
                key=f"{point}_name",
                help="[AUTO] Generated from machine composition."
            )
            st.text_input(
                "Sensitivity (mV/g)",
                key=f"{point}_sens",
                help="[MANUAL REQUIRED] Enter from sensor datasheet."
            )

# =========================================================
# DESCRIPTORS TAB
# =========================================================

with tabs[1]:
    st.header("Descriptors Worksheet")

    st.success(f"[AUTO] LF Lower = {lf_lower:.1f} Hz")
    st.success(f"[AUTO] LF Upper = {lf_upper:.1f} Hz")
    st.success(f"[AUTO] HF Lower = {hf_lower:.1f} Hz")
    st.success(f"[AUTO] HF Upper = {hf_upper:.1f} Hz")

# =========================================================
# WAVEFORM TAB
# =========================================================

with tabs[2]:
    st.header("Waveform Configuration")
    st.success(f"[AUTO] Fmax = {fmax} Hz")
    st.selectbox("Lines", [6400,12800,25600], index=1)

# =========================================================
# ALARM TAB
# =========================================================

with tabs[3]:
    st.header("Alarm Setpoints")
    st.success(f"[AUTO] ISO Class = {iso_class}")
    st.info(f"[RECOMMENDED] Alert = {alert} mm/s")
    st.error(f"[RECOMMENDED] Danger = {danger} mm/s")