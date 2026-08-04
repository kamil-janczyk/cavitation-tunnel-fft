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

## Mathematical Background

### Blade Passing Frequency (BPF)

Blade Passing Frequency is calculated as:

$$
BPF=n \cdot Z
$$

where:

- \(n\) – rotational speed [rev/s]
- \(Z\) – number of blades

The harmonic frequencies are:

$$
f_k=k \cdot BPF
$$

where \(k=1...5\) corresponds to harmonics H1–H5.

---

### Sliding FFT

The pressure signal is divided into overlapping windows. Before FFT calculation:

1. The mean value is removed:

$$
x(t)=x(t)-\bar{x}
$$

2. The signal length is adjusted to contain an integer number of BPF cycles.

Number of samples per FFT window:

$$
N=T_w \cdot f_s
$$

where:

- \(T_w\) – window length [s]
- \(f_s\) – sampling frequency [Hz]

Window step:

$$
step=T_w(1-O)
$$

where \(O\) is the overlap ratio.

For each window, the FFT is calculated using the real FFT:

$$
X(k)=rFFT(x)
$$

The amplitude spectrum used for harmonic extraction is:

$$
A(k)=\frac{2|X(k)|}{N}
$$

where:

- \(A(k)\) – FFT amplitude
- \(X(k)\) – FFT coefficient
- \(N\) – number of samples in the window

### Harmonic Detection

For each harmonic, the expected frequency is:

$$
f_{expected}=k \cdot BPF
$$

The algorithm searches for the maximum FFT amplitude within:

$$
f_{expected}\pm2Hz
$$

Detected amplitude:

$$
A_H=\max(A(f)), \quad f\in[f_{expected}-2Hz, f_{expected}+2Hz]
$$

---

### IQR Outlier Rejection

The interquartile range is:

$$
IQR=Q_3-Q_1
$$

Accepted values:

$$
Q_1-1.5IQR \leq x \leq Q_3+1.5IQR
$$

Values outside this range are removed before calculating the representative amplitude.

---

### Representative Amplitude

After filtering, histogram-based mode estimation is used:

1. Divide remaining values into 5 bins.
2. Select the bin with the highest number of samples.
3. Representative amplitude:

$$
A_{rep}=median(x_{bin})
$$

If multiple bins have equal counts, the higher-amplitude bin is selected.

---

### Model-to-Full-Scale Scaling

Frequency scaling:

$$
f_{FS}=f_M \cdot n_{ratio}
$$

Amplitude scaling:

$$
A_{FS}=A_M \cdot \rho_{ratio}\cdot n_{ratio}^{2}\cdot scale^{2}
$$

where:

- $\rho_{ratio}$ – density ratio
- $n_{ratio}$ – rotational speed ratio
- $scale$ – geometric scale ratio

with:

$$
n_{ratio}=\frac{n_{FS}}{n_M}
$$

---

### Stability Metrics

Mean:

$$
\bar{x}=\frac{1}{N}\sum x_i
$$

Standard deviation:

$$
\sigma=\sqrt{\frac{\sum(x_i-\bar{x})^2}{N-1}}
$$

Coefficient of variation:

$$
CoV=\frac{\sigma}{\bar{x}}\cdot100\%
$$

IQR spread:

$$
R_{IQR}=\frac{IQR}{median(x)}
$$

Quartile dispersion:

$$
CQD=\frac{Q_3-Q_1}{Q_3+Q_1}
$$

---
