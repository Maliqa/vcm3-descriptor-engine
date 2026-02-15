import streamlit as st
import math

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(page_title="VCM-3 Smart Configurator", layout="wide")

st.title("VCM-3 Smart Configurator")
st.caption("Engineering Assistant for VCM-3 Worksheet Filling")

# =====================================================
# SIDEBAR – MACHINE SETUP
# =====================================================

st.sidebar.header("Machine Setup")

rpm = st.sidebar.number_input("Max RPM", min_value=1, value=1500)
power_kw = st.sidebar.number_input("Motor Power (kW)", min_value=0.1, value=15.0)
foundation = st.sidebar.selectbox("Foundation Type", ["Rigid", "Soft"])
variable_speed = st.sidebar.checkbox("Variable Speed Machine?")

machine_components = st.sidebar.multiselect(
    "Machine Composition",
    ["Motor", "Gearbox", "Fan", "Pump"],
    default=["Motor"]
)

monitor_harmonic = st.sidebar.selectbox(
    "Monitor Harmonic Up To:",
    [2, 3, 4, 5, 6],
    index=2
)

fault_unbalance = st.sidebar.checkbox("Unbalance")
fault_misalignment = st.sidebar.checkbox("Misalignment")
fault_looseness = st.sidebar.checkbox("Looseness")
fault_gear = st.sidebar.checkbox("Gear Fault")
fault_bearing = st.sidebar.checkbox("Bearing Fault")

gear_teeth = 0
sideband_order = 0

if fault_gear:
    gear_teeth = st.sidebar.number_input("Gear Teeth", min_value=1, value=30)
    sideband_order = st.sidebar.selectbox("Sideband ±nX", [1, 2, 3], index=1)

envelope_upper = 8000
if fault_bearing:
    envelope_upper = st.sidebar.selectbox("Envelope Upper (Hz)", [5000, 8000, 10000, 15000], index=1)

# =====================================================
# CORE CALCULATION ENGINE
# =====================================================

one_x = rpm / 60
harmonic_target = one_x * monitor_harmonic

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

# ISO Simplified Logic
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

# =====================================================
# TABS PER WORKSHEET
# =====================================================

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

# =====================================================
# CHANNELS TAB
# =====================================================

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
            help="AUTO – Generated from machine composition."
        )

        st.selectbox(
            "Sensor Type",
            ["Acceleration", "Velocity"],
            key=f"{point}_sensor",
            help="RECOMMENDED – Acceleration for predictive maintenance."
        )

        st.text_input(
            "Sensitivity (mV/g)",
            placeholder="Example: 100",
            key=f"{point}_sens",
            help="MANUAL – From sensor datasheet."
        )

        st.text_input(
            "Unit",
            value="m/s²",
            disabled=True,
            key=f"{point}_unit",
            help="AUTO – Default acceleration unit."
        )

        st.markdown("---")

# =====================================================
# TACHOMETER TAB
# =====================================================

with tabs[1]:

    st.header("Tachometers Worksheet")

    if variable_speed:
        st.success("AUTO – Tachometer Recommended")
        st.text_input(
            "Tach Channel Name",
            value="Tacho_1",
            key="tacho_name",
            help="AUTO – Required for variable speed machine."
        )
    else:
        st.info("Tachometer optional for constant speed machines.")

# =====================================================
# PROCESS VALUES TAB
# =====================================================

with tabs[2]:

    st.header("Process Values Worksheet")

    st.text_input(
        "Channel Name",
        value="Temperature_1",
        key="process_name",
        help="MANUAL – Define process variable (temperature, pressure, etc)."
    )

    st.number_input(
        "Bottom Value @4mA",
        value=0.0,
        key="bottom_4ma",
        help="MANUAL – From sensor datasheet."
    )

    st.number_input(
        "Top Value @20mA",
        value=100.0,
        key="top_20ma",
        help="MANUAL – From sensor datasheet."
    )

# =====================================================
# DESCRIPTORS TAB
# =====================================================

with tabs[3]:

    st.header("Descriptors Worksheet")

    st.success(f"AUTO – 1X = {one_x:.2f} Hz")
    st.success(f"AUTO – Harmonic Target ({monitor_harmonic}X) = {harmonic_target:.2f} Hz")

    if fault_gear:
        st.success(f"AUTO – Gear Mesh = {gear_mesh:.2f} Hz")

    if fault_bearing:
        st.success(f"AUTO – Envelope Upper = {envelope_upper} Hz")

    st.success(f"AUTO – Recommended Fmax = {fmax} Hz")

    st.markdown("---")

    if fault_unbalance or fault_misalignment or fault_looseness:
        st.info("RECOMMENDED – Enable Bandpass descriptor")

    if fault_bearing:
        st.info("RECOMMENDED – Enable Envelope descriptor")

# =====================================================
# ALARM TAB
# =====================================================

with tabs[4]:

    st.header("Alarm Setpoints Worksheet")

    st.success(f"AUTO – ISO Class = {iso_class}")
    st.success(f"RECOMMENDED – Alert = {alert} mm/s")
    st.error(f"RECOMMENDED – Danger = {danger} mm/s")

# =====================================================
# WAVEFORM TAB
# =====================================================

with tabs[5]:

    st.header("Waveform Configuration")

    st.success(f"AUTO – Set Fmax = {fmax} Hz")
    st.info("RECOMMENDED – Set appropriate resolution for harmonic visibility.")

# =====================================================
# DATA COLLECTION TAB
# =====================================================

with tabs[6]:

    st.header("Data Collection")

    if variable_speed:
        st.info("RECOMMENDED – Short measuring time for variable speed tracking.")
    else:
        st.info("Standard measuring time acceptable.")

# =====================================================
# MODBUS TAB
# =====================================================

with tabs[7]:

    st.header("Modbus Registers")

    st.info("MANUAL – Configure only if external PLC integration required.")

# =====================================================
# FINAL SUMMARY
# =====================================================

st.header("Final Engineering Summary")

st.write(f"""
- RPM: {rpm}
- 1X Frequency: {one_x:.2f} Hz
- Highest Monitoring Frequency: {highest_freq:.2f} Hz
- Recommended Fmax: {fmax} Hz
- ISO Class: {iso_class}
- Alert/Danger: {alert}/{danger} mm/s
""")