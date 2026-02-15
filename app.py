import streamlit as st
import math

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(page_title="VCM-3 Smart Configurator v3", layout="wide")

st.title("VCM-3 Smart Configurator v3")
st.caption("Basic Mode (Default) + Advanced Engineering Mode")

# =========================================================
# MODE TOGGLE
# =========================================================

st.sidebar.header("Mode Selection")

mode = st.sidebar.radio(
    "Select Mode",
    ["Basic", "Advanced"],
    index=0,
    help="Basic: Simplified worksheet view. Advanced: Full engineering transparency."
)

# =========================================================
# CORE MACHINE INPUT
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

# Advanced only inputs
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

envelope_upper = 8000
if fault_bearing:
    if mode == "Advanced":
        envelope_upper = st.sidebar.selectbox("Envelope Upper (Hz)", [5000,8000,10000,15000], index=1)

# =========================================================
# ENGINE CALCULATION
# =========================================================

one_x = rpm / 60
harmonic_target = one_x * harmonic_order

gear_mesh = 0
sideband_upper = 0

if fault_gear:
    gear_mesh = gear_teeth * one_x
    sideband_upper = gear_mesh + (sideband_order * one_x)

highest_freq = harmonic_target

if fault_gear:
    highest_freq = max(highest_freq, sideband_upper)

if fault_bearing:
    highest_freq = max(highest_freq, envelope_upper)

fmax = math.ceil(highest_freq * 1.2)

# ISO CLASS LOGIC
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
# MONITORING SUMMARY (ALWAYS VISIBLE)
# =========================================================

st.divider()
st.header("Monitoring Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("RPM", rpm)
col2.metric("1X Frequency", f"{one_x:.2f} Hz")
col3.metric("Highest Frequency", f"{highest_freq:.2f} Hz")
col4.metric("Recommended Fmax", f"{fmax} Hz")

st.write(f"ISO Class: {iso_class}")
st.write(f"Alert / Danger: {alert} / {danger} mm/s")
st.write(f"Current Mode: {mode}")

# =========================================================
# ADVANCED ENGINEERING BREAKDOWN
# =========================================================

if mode == "Advanced":
    with st.expander("Engineering Calculation Breakdown"):
        st.write(f"1X = RPM / 60 = {one_x:.2f} Hz")
        st.write(f"Harmonic Target ({harmonic_order}X) = {harmonic_target:.2f} Hz")

        if fault_gear:
            st.write(f"Gear Mesh = Teeth × 1X = {gear_mesh:.2f} Hz")
            st.write(f"Sideband Upper = {sideband_upper:.2f} Hz")

        if fault_bearing:
            st.write(f"Envelope Upper = {envelope_upper} Hz")

        st.write(f"Highest Frequency = {highest_freq:.2f} Hz")
        st.write(f"Fmax = Highest × 1.2 = {fmax} Hz")

# =========================================================
# WORKSHEET TABS
# =========================================================

tabs = st.tabs([
    "Channels",
    "Tachometers",
    "Process Values",
    "Descriptors",
    "Alarm Setpoints",
    "Waveforms",
    "Data Collection",
    "Modbus Registers"
])

# =========================================================
# CHANNELS TAB
# =========================================================

with tabs[0]:

    st.header("Channels Worksheet")

    bearing_points = []

    if "Motor" in machine_components:
        bearing_points += ["Motor_DE", "Motor_NDE"]

    if "Gearbox" in machine_components:
        bearing_points += ["Gearbox_Input", "Gearbox_Output"]

    for point in bearing_points:

        st.subheader(point)

        st.text_input(
            "Channel Name",
            value=f"{point}_H",
            disabled=True,
            key=f"{point}_name",
            help="[AUTO] Generated from machine composition."
        )

        st.selectbox(
            "Sensor Type",
            ["Acceleration", "Velocity"],
            key=f"{point}_sensor",
            help="[RECOMMENDED] Acceleration preferred for predictive maintenance."
        )

        st.text_input(
            "Sensitivity (mV/g)",
            placeholder="Example: 100",
            key=f"{point}_sens",
            help="[MANUAL REQUIRED] Enter from sensor datasheet."
        )

        st.markdown("---")

# =========================================================
# TACHOMETER TAB
# =========================================================

with tabs[1]:

    st.header("Tachometers Worksheet")

    st.checkbox(
        "Enable Tachometer",
        value=variable_speed,
        disabled=True,
        help="[AUTO] Enabled if variable speed selected."
    )

# =========================================================
# PROCESS VALUES TAB
# =========================================================

with tabs[2]:

    st.header("Process Values Worksheet")

    st.text_input(
        "Channel Name",
        key="process_name",
        help="[MANUAL REQUIRED] Example: Gearbox Temperature."
    )

    st.number_input(
        "Bottom @4mA",
        value=0.0,
        key="bottom_4ma",
        help="[MANUAL REQUIRED] Value at 4mA."
    )

    st.number_input(
        "Top @20mA",
        value=100.0,
        key="top_20ma",
        help="[MANUAL REQUIRED] Value at 20mA."
    )

# =========================================================
# DESCRIPTORS TAB
# =========================================================

with tabs[3]:

    st.header("Descriptors Worksheet")

    st.success(f"[AUTO] 1X = {one_x:.2f} Hz")

    if fault_unbalance or fault_misalignment:
        st.info("[RECOMMENDED] Enable Bandpass descriptor")

    if fault_gear:
        st.success(f"[AUTO] Gear Mesh = {gear_mesh:.2f} Hz")

    if fault_bearing:
        st.success(f"[AUTO] Envelope Upper = {envelope_upper} Hz")

# =========================================================
# ALARM TAB
# =========================================================

with tabs[4]:

    st.header("Alarm Setpoints")

    st.success(f"[AUTO] ISO Class = {iso_class}")
    st.info(f"[RECOMMENDED] Alert = {alert} mm/s")
    st.error(f"[RECOMMENDED] Danger = {danger} mm/s")

# =========================================================
# WAVEFORM TAB
# =========================================================

with tabs[5]:

    st.header("Waveform Configuration")

    st.success(f"[AUTO] Fmax = {fmax} Hz")

    st.selectbox(
        "Lines",
        [6400, 12800, 25600],
        index=1,
        help="[RECOMMENDED] Higher lines = better frequency resolution."
    )

# =========================================================
# DATA COLLECTION TAB
# =========================================================

with tabs[6]:

    st.header("Data Collection")

    st.selectbox(
        "Scalar Interval (sec)",
        [30, 60, 120],
        index=1,
        help="[RECOMMENDED] Shorter interval for critical machine."
    )

# =========================================================
# MODBUS TAB
# =========================================================

with tabs[7]:

    st.header("Modbus Registers")

    st.text_input(
        "Register Start",
        value="100",
        help="[RECOMMENDED] Default starting register."
    )

    st.text_input(
        "Scaling",
        key="modbus_scaling",
        help="[MANUAL REQUIRED] If PLC integration needed."
    )