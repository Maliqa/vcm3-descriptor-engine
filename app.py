import streamlit as st
import math

st.set_page_config(page_title="VCM-3 Descriptor Engine PRO", layout="wide")

st.title("VCM-3 Advanced Descriptor Design Engine PRO")
st.markdown("Dynamic Harmonic + Gear + Envelope + ISO Alarm Recommendation")

# ==================================================
# MACHINE INPUT
# ==================================================

st.header("Machine Basic Information")

rpm = st.number_input("Max RPM", min_value=1, value=1500)
variable_speed = st.checkbox("Variable Speed Machine?")

machine_type = st.selectbox(
    "Machine Type",
    ["Motor Only", "Motor + Gearbox", "Fan / Pump"]
)

# ==================================================
# ISO CLASS SELECTION
# ==================================================

st.header("ISO Classification")

iso_class = st.selectbox(
    "Select ISO Machine Class",
    [
        "Class I - Small Machine",
        "Class II - Medium Machine",
        "Class III - Large Rigid Foundation",
        "Class IV - Large Soft Foundation"
    ]
)

# Simplified ISO velocity RMS limits (mm/s)
iso_limits = {
    "Class I - Small Machine": (2.8, 4.5),
    "Class II - Medium Machine": (4.5, 7.1),
    "Class III - Large Rigid Foundation": (7.1, 11.0),
    "Class IV - Large Soft Foundation": (11.0, 18.0)
}

alert_level, danger_level = iso_limits[iso_class]

# ==================================================
# HARMONIC SELECTION
# ==================================================

st.subheader("Harmonic Monitoring Target")

harmonic_order = st.selectbox(
    "Monitor Harmonic Up To:",
    [2, 3, 4, 5, 6],
    index=2
)

# ==================================================
# FAULT SELECTION
# ==================================================

st.subheader("Fault To Monitor")

fault_unbalance = st.checkbox("Unbalance")
fault_misalignment = st.checkbox("Misalignment")
fault_looseness = st.checkbox("Looseness")
fault_gear = st.checkbox("Gear Fault")
fault_bearing = st.checkbox("Bearing Fault")

gear_teeth = 0
sideband_order = 0

if fault_gear:
    gear_teeth = st.number_input("Gear Teeth Count", min_value=1, value=30)
    sideband_order = st.selectbox(
        "Gear Sideband Coverage (± n × 1X)",
        [1, 2, 3],
        index=1
    )

envelope_upper = 0
ecu_lower = 0
ecu_upper = 0

if fault_bearing:
    envelope_upper = st.selectbox(
        "Envelope Upper Band (Hz)",
        [5000, 8000, 10000, 15000],
        index=1
    )
    ecu_lower = st.number_input("ECU Lower Band (Hz)", value=500)
    ecu_upper = envelope_upper

# ==================================================
# CALCULATION SECTION
# ==================================================

one_x = rpm / 60
harmonic_target = one_x * harmonic_order

gear_mesh = 0
gear_upper_sideband = 0

if fault_gear:
    gear_mesh = gear_teeth * one_x
    gear_upper_sideband = gear_mesh + (sideband_order * one_x)

target_freq = harmonic_target

if fault_gear:
    target_freq = max(target_freq, gear_upper_sideband)

if fault_bearing:
    target_freq = max(target_freq, envelope_upper)

fmax_recommend = target_freq * 1.2 if target_freq > 0 else 0

# ==================================================
# BP AUTO DESIGN
# ==================================================

bp_lower = 0
bp_upper = 0

if fault_unbalance or fault_misalignment or fault_looseness:
    bp_lower = max(one_x * 0.5, 1)
    bp_upper = harmonic_target * 1.2

if fault_gear:
    bp_lower = gear_mesh - (sideband_order * one_x)
    bp_upper = gear_mesh + (sideband_order * one_x)

# ==================================================
# OUTPUT SECTION
# ==================================================

st.header("Frequency Analysis Result")

st.write(f"1X Frequency: **{one_x:.2f} Hz**")
st.write(f"Harmonic Target ({harmonic_order}X): **{harmonic_target:.2f} Hz**")

if fault_gear:
    st.write(f"Gear Mesh Frequency: **{gear_mesh:.2f} Hz**")
    st.write(f"Gear Sideband Upper: **{gear_upper_sideband:.2f} Hz**")

if fault_bearing:
    st.write(f"Envelope Upper Band: **{envelope_upper} Hz**")

st.write(f"Highest Monitoring Frequency: **{target_freq:.2f} Hz**")
st.write(f"Recommended Fmax (20% margin): **{math.ceil(fmax_recommend)} Hz**")

# ==================================================
# BP & ECU DISPLAY
# ==================================================

st.header("Descriptor Auto Design")

if bp_upper > 0:
    st.success(f"BP Lower: {bp_lower:.2f} Hz")
    st.success(f"BP Upper: {bp_upper:.2f} Hz")

if fault_bearing:
    st.success(f"ECU Lower: {ecu_lower} Hz")
    st.success(f"ECU Upper: {ecu_upper} Hz")

# ==================================================
# ISO ALARM OUTPUT
# ==================================================

st.header("Automatic ISO Alarm Recommendation")

st.success(f"ISO Alert Level: {alert_level} mm/s RMS")
st.error(f"ISO Danger Level: {danger_level} mm/s RMS")

st.info("Based on ISO 10816/20816 simplified classification.")

# ==================================================
# WORKSHEET GUIDANCE
# ==================================================

st.header("Worksheet Filling Guidance")

st.markdown("### Channels")
st.write("- Sensor Type: Acceleration")
st.write("- Verify sensitivity & direction")

st.markdown("### Waveforms")
if target_freq > 0:
    st.write(f"- Set Fmax ≈ {math.ceil(fmax_recommend)} Hz")

st.markdown("### Descriptors")
if bp_upper > 0:
    st.write("- Enter BP Lower & Upper in Descriptor Worksheet")

if fault_bearing:
    st.write("- Enter ECU Lower & Upper in Descriptor Worksheet")

st.markdown("### Alarm Setpoints")
st.write(f"- Alert: {alert_level} mm/s")
st.write(f"- Danger: {danger_level} mm/s")

st.markdown("### Tachometer")
if variable_speed:
    st.write("- Enable Tachometer (Variable Speed)")
else:
    st.write("- Tachometer optional for constant speed")

# ==================================================
# FINAL SUMMARY
# ==================================================

st.header("Final Summary")

if target_freq > 0:
    st.write(f"""
    - RPM: {rpm}
    - 1X: {one_x:.2f} Hz
    - Harmonic Coverage: {harmonic_order}X
    - Highest Frequency: {target_freq:.2f} Hz
    - Recommended Fmax: {math.ceil(fmax_recommend)} Hz
    - ISO Alert/Danger: {alert_level}/{danger_level} mm/s
    """)
else:
    st.write("Please configure RPM and fault selection.")
