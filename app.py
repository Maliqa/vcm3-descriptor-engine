import streamlit as st
import math

st.set_page_config(page_title="VCM-3 Smart Worksheet Assistant", layout="wide")

st.title("VCM-3 Smart Worksheet Assistant 2.0")
st.caption("Internal Engineering Version – Structured Per Worksheet")

# =========================================================
# ================= SIDEBAR INPUT =========================
# =========================================================

st.sidebar.header("Machine Basic Information")

rpm = st.sidebar.number_input(
    "RPM (Max Speed)",
    min_value=1,
    value=1500,
    help="RPM adalah kecepatan putar mesin. Semua frekuensi (1X, GMF, harmonic) dihitung dari sini."
)

variable_speed = st.sidebar.checkbox(
    "Variable Speed Machine?",
    help="Aktifkan jika mesin memiliki variasi RPM. Tachometer akan direkomendasikan."
)

st.sidebar.divider()

# ---------------- Machine Composition --------------------

st.sidebar.header("Machine Composition")

use_motor = st.sidebar.checkbox("Motor")
use_gearbox = st.sidebar.checkbox("Gearbox")
use_fan = st.sidebar.checkbox("Fan")
use_pump = st.sidebar.checkbox("Pump")

gear_teeth = 0
blade_count = 0
vane_count = 0

if use_gearbox:
    gear_teeth = st.sidebar.number_input(
        "Gear Teeth",
        min_value=1,
        value=30,
        help="Jumlah gigi gear. Digunakan untuk menghitung Gear Mesh Frequency."
    )

if use_fan:
    blade_count = st.sidebar.number_input(
        "Blade Count",
        min_value=1,
        value=8,
        help="Jumlah blade fan untuk menghitung Blade Pass Frequency."
    )

if use_pump:
    vane_count = st.sidebar.number_input(
        "Vane Count",
        min_value=1,
        value=6,
        help="Jumlah vane pump untuk menghitung Vane Pass Frequency."
    )

st.sidebar.divider()

# ---------------- Descriptor Selection --------------------

st.sidebar.header("Descriptor Selection")

desc_iso = st.sidebar.checkbox(
    "ISO RMS",
    help="Band 10–1000 Hz untuk overall vibration level."
)

desc_rot = st.sidebar.checkbox(
    "Rotational Band",
    help="Monitoring harmonic 1X–nX untuk unbalance/misalignment."
)

desc_env = st.sidebar.checkbox(
    "Envelope",
    help="Monitoring frekuensi tinggi untuk deteksi dini kerusakan bearing."
)

desc_gmf = st.sidebar.checkbox(
    "Gear Mesh",
    help="Monitoring Gear Mesh Frequency (teeth × 1X) ± sideband."
)

desc_bpf = st.sidebar.checkbox(
    "Blade/Vane Pass",
    help="Monitoring Blade/Vane pass frequency."
)

harmonic_order = st.sidebar.selectbox(
    "Harmonic Coverage",
    [2, 3, 4, 5, 6],
    index=2,
    help="Menentukan sampai harmonic ke berapa yang dimonitor."
)

sideband_order = st.sidebar.selectbox(
    "Gear Sideband Coverage",
    [1, 2, 3],
    index=1,
    help="Jumlah sideband di sekitar GMF (± n × 1X)."
)

envelope_lower = 500
envelope_upper = 5000

if desc_env:
    envelope_lower = st.sidebar.number_input("Envelope Lower (Hz)", value=500)
    envelope_upper = st.sidebar.number_input("Envelope Upper (Hz)", value=5000)

st.sidebar.divider()

# ---------------- LF / HF Override --------------------

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

# ---------------- ISO Classification --------------------

st.sidebar.header("ISO Classification")

iso_class = st.sidebar.selectbox(
    "ISO Class",
    [
        "Class I - Small",
        "Class II - Medium",
        "Class III - Large Rigid",
        "Class IV - Large Soft"
    ],
    help="Menentukan batas Alert dan Danger berdasarkan ukuran mesin."
)

iso_limits = {
    "Class I - Small": (2.8, 4.5),
    "Class II - Medium": (4.5, 7.1),
    "Class III - Large Rigid": (7.1, 11.0),
    "Class IV - Large Soft": (11.0, 18.0)
}

alert_level, danger_level = iso_limits[iso_class]

# =========================================================
# ================= ENGINE PROCESSING =====================
# =========================================================

shaft_freq = rpm / 60
frequency_targets = []

if desc_rot:
    harmonic_target = shaft_freq * harmonic_order
    frequency_targets.append(harmonic_target)

gmf = 0
gmf_upper = 0
if desc_gmf and use_gearbox:
    gmf = gear_teeth * shaft_freq
    gmf_upper = gmf + (sideband_order * shaft_freq)
    frequency_targets.append(gmf_upper)

blade_pass = 0
if desc_bpf and use_fan:
    blade_pass = blade_count * shaft_freq
    frequency_targets.append(blade_pass)

if desc_bpf and use_pump:
    vane_pass = vane_count * shaft_freq
    frequency_targets.append(vane_pass)

if desc_env:
    frequency_targets.append(envelope_upper)

highest_freq = max(frequency_targets) if frequency_targets else shaft_freq
Fmax = highest_freq * 1.2

# -------- LF/HF AUTO ---------

if desc_env:
    LF_auto = envelope_lower
elif desc_gmf:
    LF_auto = 5
else:
    LF_auto = 2

HF_auto = Fmax * 1.2

LF_used = manual_lf if override_lf else LF_auto
HF_used = manual_hf if override_hf else HF_auto

# =========================================================
# ================= CHANNEL ALLOCATION ====================
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

channel_map = []
optimization_log = []

for bearing in bearing_list:
    for axis in ["H", "V", "A"]:
        channel_map.append((bearing, axis))

if len(channel_map) > 12:
    overflow = len(channel_map) - 12

    for bearing in reversed(bearing_list):
        if overflow <= 0:
            break
        if (bearing, "A") in channel_map:
            channel_map.remove((bearing, "A"))
            optimization_log.append(f"Removed Axial from {bearing}")
            overflow -= 1

    for bearing in reversed(bearing_list):
        if overflow <= 0:
            break
        if (bearing, "V") in channel_map:
            channel_map.remove((bearing, "V"))
            optimization_log.append(f"Removed Vertical from {bearing}")
            overflow -= 1

# =========================================================
# ================= OUTPUT SECTION ========================
# =========================================================

st.divider()
st.header("1️⃣ Monitoring Summary")

col1, col2, col3 = st.columns(3)
col1.metric("RPM", rpm)
col2.metric("1X Frequency (Hz)", f"{shaft_freq:.2f}")
col3.metric("Fmax (Hz)", f"{Fmax:.2f}")

st.divider()
st.header("2️⃣ Channels Worksheet")

for i, (bearing, axis) in enumerate(channel_map, start=1):
    st.write(f"Channel {i:02d} – {bearing} – {axis}")

if variable_speed:
    st.write("Channel 13 – Tachometer – Enabled")

st.divider()
st.header("3️⃣ Waveforms Worksheet")

st.write(f"Fmax : {Fmax:.2f} Hz")
st.write(f"LF Used : {LF_used:.2f} Hz (Auto: {LF_auto:.2f})")
st.write(f"HF Used : {HF_used:.2f} Hz (Auto: {HF_auto:.2f})")
st.write("Window : Hanning")
st.write("Averaging : 3")
st.write("Overlap : 50%")

st.divider()
st.header("4️⃣ Descriptors Worksheet")

if desc_iso:
    st.write("ISO RMS → 10–1000 Hz")

if desc_rot:
    st.write(f"Rotational Band → 1X–{harmonic_order}X")

if desc_gmf and use_gearbox:
    st.write(f"Gear Mesh → {gmf:.2f} Hz ± {sideband_order}X")

if desc_bpf and use_fan:
    st.write(f"Blade Pass → {blade_pass:.2f} Hz")

if desc_env:
    st.write(f"Envelope → {envelope_lower}–{envelope_upper} Hz")

st.divider()
st.header("5️⃣ Alarm Setpoints Worksheet")

st.write(f"ISO Alert : {alert_level} mm/s RMS")
st.write(f"ISO Danger : {danger_level} mm/s RMS")

st.divider()
st.header("6️⃣ Data Collection Worksheet")

st.write("Scalar Update Rate : 60 s")
st.write("Waveform Update Rate : 600 s")

st.divider()
st.header("7️⃣ Modbus Register Worksheet")

st.write("Register mapping auto-generate based on channel order.")

st.divider()

with st.expander("🔍 Channel Optimization Log"):
    if optimization_log:
        for log in optimization_log:
            st.write(log)
    else:
        st.write("No optimization required.")