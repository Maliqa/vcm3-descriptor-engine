import streamlit as st
import math

st.set_page_config(page_title="VCM-3 Smart Configurator", layout="wide")

st.title("VCM-3 Smart Configurator")
st.caption("Internal Engineer Version – Worksheet Assistant Mode")

# =========================================================
# SIDEBAR INPUT SECTION
# =========================================================

st.sidebar.header("Machine Basic Information")

rpm = st.sidebar.number_input("RPM (Max Speed)", min_value=1, value=1500)
variable_speed = st.sidebar.checkbox("Variable Speed Machine?")
monitoring_level = "Advanced (H + V + Axial)"

st.sidebar.divider()

# -------------------------
# Machine Composition
# -------------------------

st.sidebar.header("Machine Composition")

use_motor = st.sidebar.checkbox("Motor")
use_gearbox = st.sidebar.checkbox("Gearbox")
use_fan = st.sidebar.checkbox("Fan")
use_pump = st.sidebar.checkbox("Pump")

gear_teeth = 0
blade_count = 0
vane_count = 0

if use_gearbox:
    gear_teeth = st.sidebar.number_input("Gear Teeth", min_value=1, value=30)

if use_fan:
    blade_count = st.sidebar.number_input("Blade Count", min_value=1, value=8)

if use_pump:
    vane_count = st.sidebar.number_input("Vane Count", min_value=1, value=6)

st.sidebar.divider()

# -------------------------
# Descriptor Selection
# -------------------------

st.sidebar.header("Descriptor Selection")

desc_iso = st.sidebar.checkbox(
    "ISO RMS",
    help="Overall machine vibration 10–1000 Hz band (global health indicator)"
)

desc_rot = st.sidebar.checkbox(
    "Rotational Band",
    help="1X to nX harmonic band for unbalance/misalignment detection"
)

desc_env = st.sidebar.checkbox(
    "Envelope",
    help="High-frequency band for early bearing fault detection"
)

desc_gmf = st.sidebar.checkbox(
    "Gear Mesh",
    help="GMF ± sideband monitoring for gear wear detection"
)

desc_bpf = st.sidebar.checkbox(
    "Blade/Vane Pass",
    help="Blade or vane pass frequency monitoring"
)

harmonic_order = st.sidebar.selectbox(
    "Harmonic Coverage (for Rotational)",
    [2, 3, 4, 5, 6],
    index=2
)

sideband_order = st.sidebar.selectbox(
    "Sideband Coverage (for Gear)",
    [1, 2, 3],
    index=1
)

envelope_lower = 500
envelope_upper = 5000

if desc_env:
    envelope_lower = st.sidebar.number_input("Envelope Lower (Hz)", value=500)
    envelope_upper = st.sidebar.number_input("Envelope Upper (Hz)", value=5000)

st.sidebar.divider()

# -------------------------
# LF / HF Override
# -------------------------

st.sidebar.header("LF / HF Override")

override_lf = st.sidebar.checkbox("Override LF manually")
manual_lf = 0
if override_lf:
    manual_lf = st.sidebar.number_input("Manual LF (Hz)", min_value=0.0, value=10.0)

override_hf = st.sidebar.checkbox("Override HF manually")
manual_hf = 0
if override_hf:
    manual_hf = st.sidebar.number_input("Manual HF (Hz)", min_value=0.0, value=1000.0)

st.sidebar.divider()

# -------------------------
# ISO Class
# -------------------------

st.sidebar.header("ISO Classification")

iso_class = st.sidebar.selectbox(
    "Select ISO Class",
    [
        "Class I - Small",
        "Class II - Medium",
        "Class III - Large Rigid",
        "Class IV - Large Soft"
    ]
)

iso_limits = {
    "Class I - Small": (2.8, 4.5),
    "Class II - Medium": (4.5, 7.1),
    "Class III - Large Rigid": (7.1, 11.0),
    "Class IV - Large Soft": (11.0, 18.0)
}

alert_level, danger_level = iso_limits[iso_class]

# =========================================================
# PROCESSING ENGINE
# =========================================================

shaft_freq = rpm / 60

frequency_targets = []

# Rotational
if desc_rot:
    harmonic_target = shaft_freq * harmonic_order
    frequency_targets.append(harmonic_target)

# Gear Mesh
gmf = 0
gmf_upper = 0
if desc_gmf and use_gearbox:
    gmf = gear_teeth * shaft_freq
    gmf_upper = gmf + (sideband_order * shaft_freq)
    frequency_targets.append(gmf_upper)

# Blade/Vane
blade_pass = 0
if desc_bpf and use_fan:
    blade_pass = blade_count * shaft_freq
    frequency_targets.append(blade_pass)

if desc_bpf and use_pump:
    vane_pass = vane_count * shaft_freq
    frequency_targets.append(vane_pass)

# Envelope
if desc_env:
    frequency_targets.append(envelope_upper)

if len(frequency_targets) == 0:
    highest_freq = shaft_freq
else:
    highest_freq = max(frequency_targets)

Fmax = highest_freq * 1.2

# -------------------------
# LF / HF AUTO LOGIC
# -------------------------

if desc_env:
    LF_auto = envelope_lower
elif desc_gmf:
    LF_auto = 5
else:
    LF_auto = 2

HF_auto = Fmax * 1.2

LF_used = manual_lf if override_lf else LF_auto
HF_used = manual_hf if override_hf else HF_auto

# Validation
if LF_used >= HF_used:
    st.warning("Warning: LF must be lower than HF")

if HF_used < Fmax:
    st.warning("Warning: HF should not be lower than Fmax")

# =========================================================
# CHANNEL ALLOCATION (Advanced H+V+A)
# =========================================================

bearing_list = []

if use_motor:
    bearing_list += ["Motor_DE", "Motor_NDE"]

if use_gearbox:
    bearing_list += ["Gearbox_Input", "Gearbox_Output"]

if use_fan:
    bearing_list += ["Fan_DE", "Fan_NDE"]

if use_pump:
    bearing_list += ["Pump_DE", "Pump_NDE"]

channels_required = len(bearing_list) * 3
max_channels = 12

channel_map = []
optimization_log = []

axis_priority = ["H", "V", "A"]

for bearing in bearing_list:
    for axis in axis_priority:
        channel_map.append((bearing, axis))

if len(channel_map) > max_channels:
    overflow = len(channel_map) - max_channels

    # Remove Axial first (low priority bearings last)
    for bearing in reversed(bearing_list):
        if overflow <= 0:
            break
        if (bearing, "A") in channel_map:
            channel_map.remove((bearing, "A"))
            optimization_log.append(f"Removed Axial from {bearing}")
            overflow -= 1

    # Remove Vertical if still overflow
    for bearing in reversed(bearing_list):
        if overflow <= 0:
            break
        if (bearing, "V") in channel_map:
            channel_map.remove((bearing, "V"))
            optimization_log.append(f"Removed Vertical from {bearing}")
            overflow -= 1

# =========================================================
# OUTPUT SECTION
# =========================================================

st.divider()
st.header("Monitoring Summary")

col1, col2, col3 = st.columns(3)

col1.metric("RPM", rpm)
col2.metric("1X Frequency (Hz)", f"{shaft_freq:.2f}")
col3.metric("Fmax (Hz)", f"{Fmax:.2f}")

st.divider()
st.header("Channel Allocation (Optimized)")

for i, (bearing, axis) in enumerate(channel_map, start=1):
    st.write(f"Channel {i:02d} – {bearing} – {axis}")

if variable_speed:
    st.write("Channel 13 – Tachometer – Enabled")

st.divider()
st.header("Waveform Configuration")

st.write(f"Fmax : {Fmax:.2f} Hz")
st.write(f"LF Used : {LF_used:.2f} Hz (Auto: {LF_auto:.2f})")
st.write(f"HF Used : {HF_used:.2f} Hz (Auto: {HF_auto:.2f})")
st.write("Window : Hanning")
st.write("Averaging : 3")
st.write("Overlap : 50%")

st.divider()
st.header("Descriptor Configuration")

if desc_iso:
    st.write("ISO_RMS_GLOBAL → 10–1000 Hz")

if desc_rot:
    st.write(f"ROT_{harmonic_order}X → 1X–{harmonic_order}X band")

if desc_gmf and use_gearbox:
    st.write(f"GMF → {gmf:.2f} Hz ± {sideband_order}X")

if desc_bpf and use_fan:
    st.write(f"BLADE_PASS → {blade_pass:.2f} Hz")

if desc_env:
    st.write(f"ENVELOPE → {envelope_lower}–{envelope_upper} Hz")

st.divider()
st.header("Alarm Setpoints")

st.write(f"ISO Alert : {alert_level} mm/s RMS")
st.write(f"ISO Danger : {danger_level} mm/s RMS")

st.divider()

with st.expander("Channel Optimization Log"):
    if optimization_log:
        for log in optimization_log:
            st.write(log)
    else:
        st.write("No optimization required. Within 12 channel limit.")