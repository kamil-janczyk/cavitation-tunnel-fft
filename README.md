# Cavitation Tunnel FFT Analysis

A **Streamlit** application for analyzing pressure signals from cavitation tunnel experiments. The tool extracts Blade Passing Frequency (BPF) harmonics, applies sensor calibration, performs model-to-full-scale scaling, and exports processed results for further analysis.

---

## Features

- Import measurement data exported from:
  - HBM Spider8 measurement system (`.asc`)
  - HBM QuantumX measurement system (`.asc`)
  - Generic CSV files (5 pressure channels)
- Import Gain calibration .csv file
- Sliding-window FFT analysis
- Blade Passing Frequency (BPF) harmonic extraction
- Robust harmonic detection (±2 Hz search window)
- IQR-based outlier rejection
- Histogram-based representative amplitude estimation
- Automatic model-to-full-scale scaling
- Harmonic stability statistics
- Interactive plots and quality checks
- Batch processing of multiple measurement files
- CSV export of results

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/cavitation-tunnel-fft.git
cd cavitation-tunnel-fft
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

---
