import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="VCM-3 Engineering Platform", layout="wide")

st.title("VCM-3 Engineering Platform")
st.markdown("Worksheet Configuration + Engineering Analysis Mode")

# ==================================================
# SIDEBAR MODE SWITCH
# ==================================================

mode = st.sidebar.radio(
    "Select Mode",
    ["Worksheet Mode", "Analysis Mode"]
)

# ==================================================
# ==================================================
# WORKSHEET MODE
# ==================================================
# ==================================================

if mode == "Worksheet Mode":

    st.header("VCM-3 Worksheet Configuration")

    rpm = st.number_input("Max RPM", min_value=1, value=1500)
    power_kw = st.number_input("Motor Power (kW)", min_value=0.1, value=15.0)
    foundation = st.selectbox("Foundation Type", ["Rigid", "Soft"])
    variable_speed = st.checkbox("Variable Speed Machine?")

    # ISO AUTO
    if power_kw < 15:
        iso_class = "Class I"
        alert_level, danger_level = 2.8, 4.5
    elif 15 <= power_kw <= 75:
        iso_class = "Class II"
        alert_level, danger_level = 4.5, 7.1
    else:
        if foundation == "Rigid":
            iso_class = "Class III"
            alert_level, danger_level = 7.1, 11.0
        else:
            iso_class = "Class IV"
            alert_level, danger_level = 11.0, 18.0

    harmonic_order = st.selectbox("Monitor Harmonic Up To:", [2,3,4,5,6], index=2)

    st.subheader("Fault Selection")

    fault_unbalance = st.checkbox("Unbalance")
    fault_misalignment = st.checkbox("Misalignment")
    fault_looseness = st.checkbox("Looseness")
    fault_gear = st.checkbox("Gear Fault")
    fault_bearing = st.checkbox("Bearing Fault")

    one_x = rpm / 60
    harmonic_target = one_x * harmonic_order

    gear_mesh = 0
    envelope_upper = 0

    if fault_gear:
        gear_teeth = st.number_input("Gear Teeth", min_value=1, value=30)
        sideband = st.selectbox("Sideband ± nX", [1,2,3], index=1)
        gear_mesh = gear_teeth * one_x
        harmonic_target = max(harmonic_target, gear_mesh + sideband * one_x)

    if fault_bearing:
        envelope_upper = st.selectbox("Envelope Upper Band", [5000,8000,10000], index=1)
        harmonic_target = max(harmonic_target, envelope_upper)

    fmax = math.ceil(harmonic_target * 1.25)

    st.subheader("Results")

    st.write(f"1X: {one_x:.2f} Hz")
    st.write(f"Recommended Fmax: {fmax} Hz")
    st.write(f"ISO Class: {iso_class}")
    st.write(f"Alert: {alert_level} mm/s")
    st.write(f"Danger: {danger_level} mm/s")

    if variable_speed:
        st.warning("Tachometer Recommended")

# ==================================================
# ==================================================
# ANALYSIS MODE
# ==================================================
# ==================================================

elif mode == "Analysis Mode":

    st.header("Engineering Analysis Mode")

    analysis_type = st.radio(
        "Select Analysis Type",
        ["Bearing Calculator", "Gear Spectrum Preview"]
    )

    rpm = st.number_input("RPM", min_value=1, value=1500)
    one_x = rpm / 60

    # ------------------------------------------------
    # BEARING CALCULATOR
    # ------------------------------------------------
    if analysis_type == "Bearing Calculator":

        st.subheader("Bearing Geometry Input")

        n = st.number_input("Number of Rolling Elements", min_value=1, value=8)
        d = st.number_input("Ball Diameter (mm)", min_value=0.1, value=10.0)
        D = st.number_input("Pitch Diameter (mm)", min_value=0.1, value=50.0)
        theta_deg = st.number_input("Contact Angle (deg)", value=0.0)

        theta = math.radians(theta_deg)

        ftf = 0.5 * one_x * (1 - (d/D) * math.cos(theta))
        bpfo = (n/2) * one_x * (1 - (d/D) * math.cos(theta))
        bpfi = (n/2) * one_x * (1 + (d/D) * math.cos(theta))
        bsf = (D/(2*d)) * one_x * (1 - ((d/D) * math.cos(theta))**2)

        st.subheader("Calculated Bearing Frequencies")

        st.write(f"FTF: {ftf:.2f} Hz")
        st.write(f"BPFO: {bpfo:.2f} Hz")
        st.write(f"BPFI: {bpfi:.2f} Hz")
        st.write(f"BSF: {bsf:.2f} Hz")

    # ------------------------------------------------
    # GEAR SPECTRUM PREVIEW
    # ------------------------------------------------
    elif analysis_type == "Gear Spectrum Preview":

        st.subheader("Gear Input")

        teeth = st.number_input("Gear Teeth", min_value=1, value=30)
        sideband = st.selectbox("Sideband ± nX", [1,2,3], index=1)

        gmf = teeth * one_x

        st.subheader("Gear Mesh Frequency")
        st.write(f"GMF: {gmf:.2f} Hz")

        # Plot spectrum preview
        fig, ax = plt.subplots()

        ax.axvline(gmf, linestyle='--')
        ax.set_title("Gear Mesh + Sideband Preview")

        for i in range(1, sideband+1):
            ax.axvline(gmf + i*one_x, linestyle=':')
            ax.axvline(gmf - i*one_x, linestyle=':')

        ax.set_xlim(0, gmf + sideband*one_x + 200)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Amplitude (Simulated)")

        st.pyplot(fig)
