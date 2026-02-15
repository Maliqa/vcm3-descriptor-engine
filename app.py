import streamlit as st
import math

st.set_page_config(page_title="VCM-3 Smart Worksheet Assistant", layout="wide")

st.title("VCM-3 Smart Worksheet Assistant – Mirror Mode")
st.caption("AUTO fields locked | RECOMMENDED & MANUAL editable")

# =========================================================
# ================= CORE INPUT ENGINE =====================
# =========================================================

st.sidebar.header("Core Machine Input")

rpm = st.sidebar.number_input(
    "RPM",
    min_value=1,
    value=1500,
    help="Kecepatan putar mesin. Semua frekuensi dihitung dari RPM."
)

variable_speed = st.sidebar.checkbox(
    "Variable Speed?",
    help="Aktifkan jika mesin memiliki variasi RPM."
)

use_motor = st.sidebar.checkbox("Motor")
use_gearbox = st.sidebar.checkbox("Gearbox")
use_fan = st.sidebar.checkbox("Fan")
use_pump = st.sidebar.checkbox("Pump")

gear_teeth = 0
blade_count = 0
vane_count = 0

if use_gearbox:
    gear_teeth = st.sidebar.number_input("Gear Teeth", value=30)

if use_fan:
    blade_count = st.sidebar.number_input("Blade Count", value=8)

if use_pump:
    vane_count = st.sidebar.number_input("Vane Count", value=6)

st.sidebar.divider()

st.sidebar.header("Fault Strategy")

desc_iso = st.sidebar.checkbox("ISO RMS")
desc_rot = st.sidebar.checkbox("Rotational Band")
desc_gmf = st.sidebar.checkbox("Gear Mesh")
desc_env = st.sidebar.checkbox("Envelope")

harmonic_order = st.sidebar.selectbox("Harmonic Coverage", [2,3,4,5], index=2)

st.sidebar.divider()

st.sidebar.header("ISO Classification")

iso_class = st.sidebar.selectbox(
    "ISO Class",
    ["Class I", "Class II", "Class III", "Class IV"]
)

iso_limits = {
    "Class I": (2.8, 4.5),
    "Class II": (4.5, 7.1),
    "Class III": (7.1, 11.0),
    "Class IV": (11.0, 18.0)
}

alert_level, danger_level = iso_limits[iso_class]

# =========================================================
# ================= ENGINE CALCULATION ====================
# =========================================================

shaft_freq = rpm / 60
frequency_targets = []

if desc_rot:
    harmonic_target = shaft_freq * harmonic_order
    frequency_targets.append(harmonic_target)

if desc_gmf and use_gearbox:
    gmf = gear_teeth * shaft_freq
    frequency_targets.append(gmf)

if desc_env:
    envelope_upper = 5000
    frequency_targets.append(envelope_upper)

highest_freq = max(frequency_targets) if frequency_targets else shaft_freq
Fmax = highest_freq * 1.2

# =========================================================
# ================= TAB STRUCTURE =========================
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
# ================= TAB 1 – CHANNELS ======================
# =========================================================

with tabs[0]:
    st.header("Channels Worksheet")

    bearing_list = []
    if use_motor:
        bearing_list += ["Motor_DE", "Motor_NDE"]
    if use_gearbox:
        bearing_list += ["Gearbox_Input", "Gearbox_Output"]

    for bearing in bearing_list:
        st.subheader(bearing)

        st.text_input(
            "Channel Name",
            value=f"{bearing}_H",
            disabled=True,
            help="AUTO – Dibentuk otomatis berdasarkan machine composition."
        )

        st.selectbox(
            "Sensor Type",
            ["Acceleration", "Velocity"],
            help="RECOMMENDED – Acceleration untuk predictive maintenance."
        )

        st.text_input(
            "Sensitivity (mV/g)",
            placeholder="Isi sesuai datasheet",
            help="MANUAL REQUIRED – Contoh: 100 mV/g."
        )

        st.text_input(
            "Unit",
            value="m/s²",
            disabled=True,
            help="AUTO – Unit default acceleration."
        )

# =========================================================
# ================= TAB 2 – TACHOMETERS ===================
# =========================================================

with tabs[1]:
    st.header("Tachometer Worksheet")

    st.checkbox(
        "Enable Tachometer",
        value=variable_speed,
        disabled=True,
        help="AUTO – Aktif jika variable speed dipilih."
    )

    st.selectbox(
        "Trigger Type",
        ["Rising", "Falling"],
        help="RECOMMENDED – Rising edge umum digunakan."
    )

    st.text_input(
        "Threshold Voltage",
        placeholder="Isi sesuai sensor",
        help="MANUAL REQUIRED – Sesuai tipe tachometer."
    )

# =========================================================
# ================= TAB 3 – PROCESS VALUES ================
# =========================================================

with tabs[2]:
    st.header("Process Values Worksheet")

    st.text_input(
        "Channel Name",
        placeholder="Contoh: Gearbox Temp",
        help="MANUAL REQUIRED – Nama parameter process."
    )

    st.text_input(
        "Bottom @4mA",
        help="MANUAL REQUIRED – Nilai fisik saat 4mA."
    )

    st.text_input(
        "Top @20mA",
        help="MANUAL REQUIRED – Nilai fisik saat 20mA."
    )

# =========================================================
# ================= TAB 4 – DESCRIPTORS ===================
# =========================================================

with tabs[3]:
    st.header("Descriptors Worksheet")

    if desc_iso:
        st.text_input(
            "ISO Lower",
            value="10 Hz",
            disabled=True,
            help="AUTO – ISO band fixed 10–1000 Hz."
        )
        st.text_input(
            "ISO Upper",
            value="1000 Hz",
            disabled=True
        )

    if desc_rot:
        st.text_input(
            "Rotational Upper",
            value=f"{harmonic_order}X",
            disabled=True,
            help="AUTO – Berdasarkan harmonic coverage."
        )

    if desc_gmf and use_gearbox:
        st.text_input(
            "Gear Mesh Frequency",
            value=f"{gmf:.2f} Hz",
            disabled=True,
            help="AUTO – Teeth × 1X."
        )

# =========================================================
# ================= TAB 5 – ALARM =========================
# =========================================================

with tabs[4]:
    st.header("Alarm Setpoints Worksheet")

    st.text_input(
        "ISO Alert",
        value=f"{alert_level} mm/s",
        disabled=True,
        help="AUTO – Berdasarkan ISO Class."
    )

    st.text_input(
        "ISO Danger",
        value=f"{danger_level} mm/s",
        disabled=True
    )

    st.text_input(
        "Delay (seconds)",
        placeholder="Contoh: 5",
        help="MANUAL REQUIRED – Mencegah false alarm."
    )

# =========================================================
# ================= TAB 6 – WAVEFORMS =====================
# =========================================================

with tabs[5]:
    st.header("Waveforms Worksheet")

    st.text_input(
        "Fmax",
        value=f"{Fmax:.2f} Hz",
        disabled=True,
        help="AUTO – Frekuensi tertinggi + margin 20%."
    )

    st.selectbox(
        "Lines",
        [6400, 12800, 25600],
        index=1,
        help="RECOMMENDED – Semakin besar semakin tinggi resolusi."
    )

    st.selectbox(
        "Window",
        ["Hanning", "Rectangular"],
        help="RECOMMENDED – Hanning untuk analisa umum."
    )

# =========================================================
# ================= TAB 7 – DATA COLLECTION ===============
# =========================================================

with tabs[6]:
    st.header("Data Collection Worksheet")

    st.selectbox(
        "Scalar Interval",
        [30, 60, 120],
        index=1,
        help="RECOMMENDED – Interval update scalar."
    )

    st.selectbox(
        "Waveform Interval",
        [300, 600, 900],
        index=1,
        help="RECOMMENDED – Interval update waveform."
    )

# =========================================================
# ================= TAB 8 – MODBUS ========================
# =========================================================

with tabs[7]:
    st.header("Modbus Register Worksheet")

    st.text_input(
        "Register Start",
        value="100",
        help="RECOMMENDED – Default start register."
    )

    st.text_input(
        "Scaling",
        placeholder="Isi jika perlu scaling",
        help="MANUAL REQUIRED – Sesuai kebutuhan PLC."
    )