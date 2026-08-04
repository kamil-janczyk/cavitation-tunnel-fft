import streamlit as st
import pandas as pd
import numpy as np
import io
import zipfile
import matplotlib.pyplot as plt
from datetime import datetime


st.title("Cavitation Tunnel FFT Analysis")

st.caption(
    "Analysis of pressure signals at blade passing frequency (BPF) harmonics. "
    "Includes calibration, harmonic extraction, and full-scale scaling."
)


# ------------------------------------------------
st.subheader("Data Input")
# ------------------------------------------------

data_format = st.selectbox(
    "Measurement format",
    [ "QuantumX (new)", "Spider8 (old)", "CSV (custom format)"],
    help="""
Select the format of your measurement files:

- **Spider8 (old)**: Data from Spider8 system (skip 35 header rows).  
- **QuantumX**: Data from QuantumX.
- **CSV (custom format)**: Plain CSV with **5 columns, no header**, first column = pressure1, ..., fifth = pressure5.
"""
)

# ------------------------------------------------
# Upload files
# ------------------------------------------------
file_types = {
    "QuantumX (new)": ["asc"],
    "Spider8 (old)": ["asc"],
    "CSV (custom format)": ["csv"]

}

measurement_files = st.file_uploader(
    f"Upload measurement files ({', '.join(file_types[data_format])})",
    type=file_types[data_format],
    accept_multiple_files=True,
    help="""
Upload your measurement files:
- **Quantum (new):** .asc files with 5 pressure channels - at last 5 out of 8 channels
- **Spider8 (old):** .asc files with 5 pressure channels - at last 5 out of 8 channels
- **CSV (custom format):** plain CSV with 5 columns (pressure1..pressure5), no header
"""
)

gain_file = st.file_uploader(
    "Upload gain file (5 rows)",
    type=["txt", "csv"],
    help="CSV/TXT file with one gain value per channel (one column, five rows order must match channels) - total 5 values."
)
@st.cache_data
def load_gains(file_bytes):

    df = pd.read_csv(io.BytesIO(file_bytes),header=None)

    # Check if there are at least 5 rows
    if df.shape[0] < 5:
        st.error(f"Expected 5 gain values, but got {df.shape[0]}")
        return None

    gains = {
        "pressure1": df.iloc[0, 0],
        "pressure2": df.iloc[1, 0],
        "pressure3": df.iloc[2, 0],
        "pressure4": df.iloc[3, 0],
        "pressure5": df.iloc[4, 0]
    }

    if df.empty:
        st.error("Uploaded file is empty")
        return None

    return gains


# 👇 LOAD + DISPLAY HERE
gains = None
if gain_file is not None:
    gains = load_gains(gain_file.getvalue())

    if gains:
        st.caption("Gains: " + ", ".join([f"{k}: {v:.3f}" for k, v in gains.items()]))

sampling_rate = st.number_input(
    "Sampling rate (Hz)",
    value=9600,
    help="Enter the sampling rate of your measurement device. Default is 9600 Hz."

)
st.markdown("### Model Scale (Tunnel)")

col1, col2 = st.columns(2)




with col1:
    with st.container(border=True):

        st.markdown("### Propeller – Tunnel")

        tunnel_rps = st.number_input(
            "Propeller revolutions (Hz)",
            value=22.0,
            step=1.0,
            help = "Propeller rotational speed in the tunnel."
        )

        tunnel_blades = st.number_input(
            "Propeller blades",
            value=5,
            step=1,
            help = "Blade count used to compute Blade Passing Frequency (BPF)."
        )

        tunnel_scale = st.number_input(
            "Scale",
            value=15.5566,
            format = "%.4f",
            help="Model-to-full-scale ratio (λ). Used for amplitude scaling."
        )

        tunnel_density = st.number_input(
            "Water density",
            value=998.2,
            help="Density of water in tunnel conditions."
        )

# -----------------------------
# Sea parameters
# -----------------------------

with col2:
    with st.container(border=True):

        st.markdown("### Full Scale (Sea)")

        sea_rps = st.number_input(
            "Propeller revolutions (Hz)",
            value=3.10,
            step = 0.1,
            format="%.3f",
            help="Expected propeller rotational speed at full scale."
        )

        sea_density = st.number_input(
            "Water density",
            value=1025.9,
            help="Density of seawater."
        )



with st.expander("FFT Settings", expanded=False):
    st.caption("Controls for sliding window FFT used to extract harmonic amplitudes.")
    col1, col2 = st.columns(2)
    with col1:
        window_sec = st.number_input(
            "Window length (seconds)",
            value=1.0,
            step=0.1,
            help="Length of each FFT window. Longer = better frequency resolution, worse time resolution."
        )

    with col2:
        overlap = st.slider(
            "Overlap",
            0.0, 0.9, 0.5,
            help="Fraction of overlap between windows. Higher = smoother results but slower computation."
        )
    use_peak_search = st.checkbox(
        "Use robust harmonic peak detection - 2Hz window",
        value=True,
        help="Search for local peak around harmonic frequency instead of taking exact FFT bin. Final table will still show exact FFT bin."
    )


@st.cache_data
def load_spider8(file_bytes,filename=None):
    df = pd.read_csv(
        io.BytesIO(file_bytes),
        sep=r"\s+",
        skiprows=35,
        header=None,
        engine="python"
    )

    df = df.iloc[:, 4:9]

    df.columns = [
        "pressure1",
        "pressure2",
        "pressure3",
        "pressure4",
        "pressure5"
    ]

    # replace Spider8 error markers
    df = df.replace("****", np.nan)

    # convert to numeric safely
    df = df.apply(pd.to_numeric, errors="coerce")

    # remove rows with invalid data
    original_len =  len(df)
    df = df.dropna()

    removed = original_len - len(df)
    removed_ratio = removed / original_len

    if removed_ratio > 0.2:
        st.caption(f"{filename}: {removed_ratio:.0%} of data removed (check signal quality)")

    # reduce memory
    df = df.astype("float32")
    return df

@st.cache_data
def load_csv_robust(file_bytes):
    """
    Load a CSV file with 5 columns (pressure1…pressure5), no header.
    Tries multiple separators (semicolon, comma, tab) and converts to numeric.
    """
    separators = [";", ",", "\t", " "]

    for sep in separators:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, header=None)
            if df.shape[1] != 5:
                continue
            df.columns = [f"pressure{i + 1}" for i in range(5)]
            df = df.apply(pd.to_numeric, errors="coerce").dropna()
            return df
        except Exception:
            continue

    raise ValueError("Cannot parse CSV. Make sure it has 5 columns (pressure1…pressure5), no header.")

@st.cache_data
def load_quantum(file_bytes,filename=None):

    import io

    df = pd.read_csv(
        io.BytesIO(file_bytes),
        sep="\t",
        skiprows=1,      # drop header line
        header=None
    )

    # keep last 5 columns (pressure signals)
    df = df.iloc[:, 5:10]

    df.columns = [
        "pressure1",
        "pressure2",
        "pressure3",
        "pressure4",
        "pressure5"
    ]

    # numeric conversion
    df = df.apply(pd.to_numeric, errors="coerce")
    # IMPORTANT: only drop invalid pressure rows
    original_len =  len(df)
    df = df.dropna()

    removed = original_len - len(df)
    removed_ratio = removed / original_len

    if removed_ratio > 0.2:
        st.caption(f"{filename}: {removed_ratio:.0%} of data removed (check signal quality)")


    return df


def cut_signal_to_bpf(signal, sampling_rate, revolutions, blades):

    bpf = revolutions * blades

    samples_per_cycle = sampling_rate / bpf

    n_cycles = int(len(signal) / samples_per_cycle)

    new_length = int(n_cycles * samples_per_cycle)

    return signal[:new_length]

def prepare_signal_for_fft(signal, sampling_rate, revolutions, blades):

    # remove DC
    signal = signal - np.mean(signal)

    # cut to integer BPF cycles
    signal = cut_signal_to_bpf(
        signal,
        sampling_rate,
        revolutions,
        blades
    )

    return signal


def find_harmonic_peak(freqs, fft_vals, target_freq, window=2):

    mask = (freqs >= target_freq - window) & (freqs <= target_freq + window)

    local_freqs = freqs[mask]
    local_fft = fft_vals[mask]

    idx_local = np.argmax(local_fft)

    return local_freqs[idx_local], local_fft[idx_local]

def compute_fft(signal, sampling_rate):


    N = len(signal)

    fft_vals = np.abs(np.fft.rfft(signal)) * 2 / N
    freqs = np.fft.rfftfreq(N, d=1/sampling_rate)

    return freqs, fft_vals


def sliding_fft_harmonics(signal, sampling_rate, revolutions, blades, window_sec=1.0,overlap=0.5):

    window_samples = int(window_sec * sampling_rate)
    step = int(window_samples * (1 - overlap))

    base_freq = revolutions * blades

    results = []

    for start in range(0, len(signal) - window_samples, step):

        segment = signal[start:start + window_samples]

        segment = prepare_signal_for_fft(
            segment,
            sampling_rate,
            revolutions,
            blades
        )

        freqs, fft_vals = compute_fft(segment, sampling_rate)

        row = {
            "time_start": start / sampling_rate
        }

        for i in range(1, 6):

            target = base_freq * i

            if use_peak_search:
                peak_freq, peak_amp = find_harmonic_peak(
                    freqs, fft_vals, target, window=2
                )
            else:
                idx = np.argmin(np.abs(freqs - target))
                peak_freq = freqs[idx]
                peak_amp = fft_vals[idx]


            row[f"H{i}_freq"] = peak_freq
            row[f"H{i}_amp"] = peak_amp

        results.append(row)

    return pd.DataFrame(results)

def sliding_fft_to_max_harmonics(signal,sampling_rate,revolutions,blades,window_sec=1.0,overlap=0.5):

    df_slide = sliding_fft_harmonics(
        signal,
        sampling_rate,
        revolutions,
        blades,
        window_sec,
        overlap
    )
    results = []

    for i in range(1, 6):

        amps = df_slide[f"H{i}_amp"].values
        freqs = df_slide[f"H{i}_freq"].values


        q1, q3, iqr, filtered, idx_filtered = iqr_filter(amps)

        if len(idx_filtered) > 0:
            amp_val = mode_after_iqr(filtered, bins=5)
            freq_val = np.nanmedian(freqs)
        else:
            freq_val = np.nan
            amp_val = np.nan

        results.append({
            "Harmonic": i,
            "FFT Frequency (Hz)":  freq_val,
            "Amplitude": amp_val
        })
    return pd.DataFrame(results)

def apply_gain(fft_df, gains):

    df = fft_df.copy()

    calibrated = []

    for _, row in df.iterrows():

        ch = row["Channel"]
        amp = row["Amplitude"]

        if ch in gains:
            amp = amp * gains[ch]

        calibrated.append(amp)

    df["Amplitude_calibrated"] = calibrated

    return df

def create_combined_fft_table(fft_results_all):
    """
    Create a combined FFT table containing:
      - all formatted FFT tables,
      - a separator,
      - a 'MAXIMUM VALUES' section with the element-wise maximum
        across all uploaded files.

    Parameters
    ----------
    fft_results_all : dict
        Dictionary {filename: formatted_dataframe}

    Returns
    -------
    pandas.DataFrame
        Combined dataframe ready for export.
    """

    # --- Combine all tables ---
    combined_tables = []

    for name, df in fft_results_all.items():
        tmp = df.copy()
        tmp.insert(0, "Source file", name)
        combined_tables.append(tmp)

    combined_df = pd.concat(combined_tables, ignore_index=True)

    # --- Calculate maximum values ---
    template = next(iter(fft_results_all.values())).copy()

    value_columns = [
        c for c in template.columns
        if c != "Frequency [Hz]"
    ]

    for col in value_columns:
        template[col] = pd.concat(
            [df[col] for df in fft_results_all.values()],
            axis=1
        ).max(axis=1)

    max_df = template.copy()
    max_df.insert(0, "Source file", "MAX")

    # --- Separator and title ---
    separator = pd.DataFrame(
        [[""] * len(combined_df.columns)],
        columns=combined_df.columns
    )

    title = pd.DataFrame(
        [["MAXIMUM VALUES"] + [""] * (len(combined_df.columns) - 1)],
        columns=combined_df.columns
    )

    # --- Final table ---
    combined_with_max = pd.concat(
        [
            combined_df,
            separator,
            title,
            max_df
        ],
        ignore_index=True
    )

    return combined_with_max
def export_fft(results, combined_with_max ):

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as z:

        z.writestr(
            "fft_all_results.csv",
            combined_with_max.to_csv(index=False)
        )

        for name, df in results.items():

            filename = f"fft_{name}.csv"

            z.writestr(
                filename,
                df.to_csv(index=False)
            )

    return zip_buffer

def scale_to_full_scale(df, density_tunnel, density_sea,
                       rev_tunnel, rev_sea, scale):

    df_scaled = df.copy()

    freq_ratio = rev_sea / rev_tunnel

    amp_factor = (
        (density_sea / density_tunnel) *
        (rev_sea / rev_tunnel)**2 *
        scale**2
    )

    df_scaled["Frequency_sea"] = df_scaled["FFT Frequency (Hz)"] * freq_ratio

    df_scaled["Amplitude_sea"] = df_scaled["Amplitude_calibrated"] * amp_factor

    return df_scaled

def mode_after_iqr(filtered, bins=5):
    if len(filtered) == 0:
        return np.nan

    counts, bin_edges = np.histogram(filtered, bins=bins)

    max_count = np.max(counts)

    # find ALL bins with max count
    candidate_bins = np.where(counts == max_count)[0]

    # pick the RIGHTMOST (highest amplitude)
    selected_bin = candidate_bins[-1]

    # return bin median
    mask = (filtered >= bin_edges[selected_bin]) & (filtered < bin_edges[selected_bin + 1])

    if np.any(mask):
        mode_val = np.median(filtered[mask])

    else:
        mode_val = np.nan

    return mode_val

def format_fft_amplitude_table(df, base_freq_tunnel, base_freq_sea):
    # --- Tunnel amplitudes ---
    df_tunnel = df.pivot(
        index="Harmonic",
        columns="Channel",
        values="Amplitude_calibrated"
    )

    df_tunnel.index = [
        f"{base_freq_tunnel*h:.1f}"
        for h in df_tunnel.index
    ]

    # --- Sea amplitudes ---
    df_sea = df.pivot(
        index="Harmonic",
        columns="Channel",
        values="Amplitude_sea"
    )

    df_sea.index = [
        f"{base_freq_sea*h:.1f}"
        for h in df_sea.index
    ]

    # --- Combine ---
    final_df = pd.concat([df_tunnel, df_sea])

    # --- Add "Frequency" as column instead of index ---
    final_df = final_df.reset_index()
    final_df = final_df.rename(columns={"index": "Frequency [Hz]"})

    return final_df


def iqr_filter(amps):
    q1 = np.nanpercentile(amps, 25)
    q3 = np.nanpercentile(amps, 75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    mask = (amps >= lower) & (amps <= upper)

    filtered = amps[mask]
    idx = np.where(mask)[0]

    return q1, q3, iqr, filtered, idx


# ------------------------------------------------
# Main processing
# ------------------------------------------------

if measurement_files and gains:

    # Map filename → file object
    file_map = {f.name: f for f in measurement_files}

    # Select preview file
    preview_file = st.selectbox("Preview file", file_map.keys())
    file_to_preview = file_map[preview_file]

    # FFT results for all files
    fft_results_all = {}

    for file in measurement_files:
        file_bytes = file.getvalue()

        if data_format == "Spider8 (old)":
            df = load_spider8(file.getvalue(), file.name)
        elif data_format == "CSV (custom format)":
            df = load_csv_robust(file.getvalue())
        else:
            df = load_quantum(file_bytes, file.name)

        fft_results = []

        for col in df.columns:
            signal = df[col].values

            df_max = sliding_fft_to_max_harmonics(signal, sampling_rate, tunnel_rps, tunnel_blades, window_sec, overlap)

            df_max["Channel"] = col

            fft_results.append(df_max)

        fft_raw = pd.concat(fft_results, ignore_index=True)

        fft_cal = apply_gain(fft_raw, gains)

        fft_scaled = scale_to_full_scale(fft_cal, tunnel_density, sea_density, tunnel_rps, sea_rps, tunnel_scale)

        # Format table before saving
        base_freq_tunnel = tunnel_rps * tunnel_blades
        base_freq_sea = sea_rps * tunnel_blades

        formatted_df = format_fft_amplitude_table(
            fft_scaled,
            base_freq_tunnel,
            base_freq_sea
        )

        fft_results_all[file.name] = formatted_df

    # -----------------------------
    # Preview plotting for selected file
    # -----------------------------
    file_to_preview = file_map[preview_file]
    file_bytes = file_to_preview.getvalue()

    if data_format == "Spider8 (old)":
        df_preview = load_spider8(file_bytes)
    elif data_format == "CSV (custom format)":
        df_preview = load_csv_robust(file_bytes)
    else:
        df_preview = load_quantum(file_bytes)

    with st.expander("Raw Data Header", expanded=False):
        st.dataframe(df_preview.head())

    # FFT Peaks
    fft_preview = fft_results_all[preview_file]

    with st.expander("Harmonic Amplitudes (Tunnel & Full Scale)", expanded=True):
        st.caption(
            "Amplitude of pressure signals at blade passing frequency harmonics. "
            "Top rows: tunnel measurements. Bottom rows: scaled to full-scale conditions."
        )
        st.dataframe(fft_preview.round(3), use_container_width=True)

    # Additional Info / Plots
    with st.expander("Signal Analysis & Quality Check", expanded=False):
        selected_channel = st.selectbox("Select Pressure Channel", df_preview.columns)
        gain = gains[selected_channel]
        signal = df_preview[selected_channel].values * gain
        df_slide = sliding_fft_harmonics(signal, sampling_rate, tunnel_rps, tunnel_blades, window_sec, overlap)

        # Harmonic stability
        st.subheader("Harmonic stability over time")
        fig2, ax2 = plt.subplots()

        for i in range(1, 6):
            ax2.plot(
                df_slide["time_start"],
                df_slide[f"H{i}_amp"],
                marker='x',
                markersize=4,
                linestyle='None',
                label=f"H{i}"
            )

        ax2.set_xlabel("Time (s)")
        ax2.set_title("Harmonic Amplitude Stability Over Time")
        ax2.set_ylabel("Amplitude [Pa]")
        ax2.legend()

        st.pyplot(fig2)

        # Stability metrics
        st.subheader("Statistical Summary (IQR Filtered)")
        st.caption(
            "Statistical summary of harmonic amplitudes after IQR-based outlier removal. "
            "All metrics (Mean, Std, Min, Max, CoV) are computed from filtered data. "
            "IQR-based metrics (IQR/Median, CQD, rejection ratio) describe signal stability."
        )
        summary = []
        bin = 5
        for i in range(1, 6):
            amps = df_slide[f"H{i}_amp"]
            q1, q3, iqr, filtered, idx_filtered = iqr_filter(amps)

            if len(filtered) > 0:
                mean_val = np.nanmean(filtered)
                std_val = np.nanstd(filtered)
                min_val = np.nanmin(filtered)
                max_val = np.nanmax(filtered)
                median = np.nanmedian(filtered)
                mode_val = mode_after_iqr(filtered, bins=bin)
            else:
                mean_val = std_val = min_val = max_val = median = mode_val = np.nan

            # Stability metrics
            iqr_stability = iqr / median if median not in [0, np.nan] else np.nan
            cqd = (q3 - q1) / (q3 + q1) if (q3 + q1) != 0 else np.nan
            rsr = median / iqr if iqr != 0 else np.nan

            outlier_ratio = (1 - (len(filtered) / len(amps))) * 100

            summary.append({
                "Harmonic": i,
                "Mean [Pa]": mean_val,
                "Std [Pa]": std_val,
                "Min [Pa]": min_val,
                "Max [Pa]": max_val,
                "Mode [Pa]": mode_val,

                "CoV (%)": 100 * std_val / mean_val if mean_val != 0 else np.nan,
                "IQR/Median": iqr_stability,
                "CQD": cqd,
                "IQR rejection ratio (%)": outlier_ratio
            })
        st.dataframe(pd.DataFrame(summary))

        # Histogram
        st.subheader("Quick Check")
        fig3, ax3 = plt.subplots()
        for i in range(1, 6):
            amps = df_slide[f"H{i}_amp"].values
            _, _, _, filtered, _ = iqr_filter(amps)
            ax3.hist(filtered, bins=bin, alpha=0.5, label=f"H{i}")

            mode_val = mode_after_iqr(filtered,bins = bin)
            ax3.axvline(mode_val, linestyle="--")
        ax3.set_title("Distribution of Harmonic Amplitudes (IQR Filtered)")
        ax3.set_xlabel("Amplitude [Pa]")
        ax3.set_ylabel("Number of windows")
        ax3.legend()
        st.pyplot(fig3)

    combined_with_max = create_combined_fft_table(fft_results_all)


    zip_data = export_fft(
        fft_results_all, combined_with_max
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"fft_results_{timestamp}.zip"

    st.download_button(
        "Download Results (CSV, zipped)",
        zip_data.getvalue(),
        file_name=zip_filename,
        mime="application/zip",
        help="Download formatted harmonic amplitude tables for all uploaded files."
    )


if measurement_files and not gains:
    st.warning("Please upload a gain file to proceed.")


with st.expander("How to Use This App", expanded=False):

    st.markdown("""
### Workflow

1. Upload **measurement files (.asc)** from Spider8  
2. Upload **gain file** (one column, five rows, one value per channel)  
3. Set **sampling rate** and **propeller/sea parameters**  
4. Adjust FFT **window length** and **overlap** if needed  
5. Select a file to preview results  
6. Download processed FFT results  

---
### Notes
- **Blade Passing Frequency (BPF):**  
  `BPF = rotation speed × number of blades`  

- **Sliding FFT:**  
  - Signal is split into windows of specified length  
  - Each window is FFT’ed, then the window shifts by `step = window_length × (1 - overlap)`  
  - Example: 1 s window, 50% overlap → step = 0.5 s  

- **Representative amplitude (mode-based selection):**  
  - Signal is first filtered using **IQR-based outlier rejection
    - q1 = 25th percentile of the signal  
    - q3 = 75th percentile of the signal  
    - iqr = q3 - q1  

    - lower bound = q1 - 1.5 × IQR  
    - upper bound = q3 + 1.5 × IQR  

    - Values outside this range are treated as spikes or noise and removed.

  - After filtering, the **mode (most frequent value) of the remaining signal is selected**
  using histogram-based binning.
   The mode is computed by:
    - dividing the filtered data into 5 bins
    - selecting the bin with the highest count
    - taking the median value within that bin
    - If multiple bins have equal counts, the higher-amplitude bin is selected.
 

- **Harmonic extraction:**  
  - Focuses on BPF and its harmonics (H1…H5)  
  - **Standard method:** amplitude at the closest FFT bin  
  - **Robust method:** searches ±2 Hz around expected harmonic for maximum  

- **Full-scale scaling:**  
  - Frequency scaled by:  `rotation ratio`  
  - Amplitude scaled by: `density_ratio · (rotation_ratio)² · (scale)²`  

- **Final table:**  
  - Displays representative amplitudes and frequencies for each harmonic:
  - Amplitude: mode of IQR-filtered values (dominant operating level)
  - Frequency: median of detected FFT peak frequencies across windows

- Note:
  Amplitude and frequency are computed independently and may not correspond
  to the same time window.
  
- **Stability Metrics Guide:**  
    - Mean – average amplitude across windows after removing outliers
    - Std – standard deviation (overall variability) after removing outliers
    - Min – minimum after removing outliers
    - Max – maximum after removing outliers
    - Mode – dominant amplitude level (most frequent value) 

    - CoV (%) – coefficient of variation (Std/Mean × 100)  
  → <10% stable, 10–30% moderate, >30% unstable  

    - IQR/Median – spread indicator  
  → <0.2 stable, 0.2–0.5 moderate, >0.5 unstable  

    - CQD (Quartile Dispersion) – relative spread of middle 50%  
  → close to 0 = stable, >0.3 = unstable  

    - IQR rejection ratio – fraction of rejected points  
  → <10% good, >20% noisy signal

""")

    st.markdown("""
        ### Notes on File Formats
        - **Spider8**: Assumes 35 header rows and channels in columns 5–9.  
        Note: On 8-channel Spider8 measurements, the last 5 channels correspond to the pressure sensors used.
        - **CSV (custom format)**: Just in case option.  5 columns **without a header**, corresponding to pressure1…pressure5. Should support different separators ( comma `,`, semicolon `;`, tab `\t`, or space. )
        - **QuantumX**:  Same as Spider8, the last 5 channels correspond to the pressure sensors used.
        """)



#By Kamil Jańczyk