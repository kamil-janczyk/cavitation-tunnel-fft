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
---

## Mathematical Background

### 1. Blade Passing Frequency (BPF)

The blade passing frequency represents the frequency at which propeller blades pass a fixed point in the flow.

\[
BPF = n \cdot Z
\]

where:

- \(BPF\) – blade passing frequency [Hz]
- \(n\) – rotational speed [rev/s]
- \(Z\) – number of propeller blades

The \(k\)-th harmonic frequency is:

\[
f_k = k \cdot BPF
\]

where:

- \(k = 1...5\) corresponds to harmonics H1–H5.

---

### 2. Sliding Window FFT

The pressure signal is divided into overlapping time windows.

For a sampling frequency \(f_s\), window length \(T_w\), and overlap \(O\):

\[
N = T_w \cdot f_s
\]

where:

- \(N\) – number of samples in FFT window
- \(T_w\) – window duration [s]
- \(f_s\) – sampling frequency [Hz]

The step between consecutive windows is:

\[
step = T_w(1-O)
\]

Example:

\[
T_w=1s,\quad O=50\%
\]

gives:

\[
step=0.5s
\]

For each window, the discrete Fourier transform is calculated:

\[
X(k)=\sum_{n=0}^{N-1}x(n)e^{-j2\pi kn/N}
\]

The single-sided amplitude spectrum is calculated as:

\[
A(k)=\frac{2|X(k)|}{N}
\]

where:

- \(A(k)\) – signal amplitude at frequency bin \(k\)
- \(X(k)\) – FFT coefficient
- \(N\) – FFT length

---

### 3. Harmonic Peak Detection

For each expected harmonic frequency:

\[
f_{expected}=k \cdot BPF
\]

the FFT spectrum is searched in a frequency range:

\[
f_{search}=f_{expected}\pm2Hz
\]

The detected harmonic amplitude is:

\[
A_H=max(A(f_{search}))
\]

The robust search allows compensation for small frequency variations caused by:

- rotational speed fluctuations
- FFT frequency resolution
- measurement noise

---

### 4. IQR-Based Outlier Rejection

Before calculating representative amplitudes, detected harmonic amplitudes are filtered using the Interquartile Range method.

The first and third quartiles are:

\[
Q_1=P_{25}
\]

\[
Q_3=P_{75}
\]

The interquartile range is:

\[
IQR=Q_3-Q_1
\]

The accepted data range is:

\[
Q_1-1.5IQR \leq x \leq Q_3+1.5IQR
\]

Values outside this range are considered outliers and removed.

---

### 5. Histogram-Based Representative Amplitude

After IQR filtering, the dominant operating amplitude is estimated using histogram binning.

The filtered signal range is divided into 5 equally sized bins:

\[
bin_i=[x_i,x_{i+1}]
\]

The dominant bin is selected:

\[
bin_{mode}=argmax(count(bin_i))
\]

The representative amplitude is calculated as the median value inside the selected bin:

\[
A_{rep}=median(x_{bin_{mode}})
\]

If multiple bins have equal counts, the higher-amplitude bin is selected.

This approach reduces the influence of:

- short cavitation bursts
- transient peaks
- measurement spikes

while preserving the dominant operating condition.

---

### 6. Model-to-Full-Scale Scaling

For cavitation similarity analysis, measured model-scale results are converted to full-scale values.

#### Frequency scaling

The frequency scale follows the rotation ratio:

\[
f_{FS}=f_M\cdot\frac{n_{FS}}{n_M}
\]

where:

- \(f_M\) – model frequency
- \(f_{FS}\) – full-scale frequency
- \(n_M\) – model rotational speed
- \(n_{FS}\) – full-scale rotational speed

---

#### Pressure amplitude scaling

Pressure fluctuations follow:

\[
p \propto \rho n^2D^2
\]

Therefore:

\[
p_{FS}=p_M
\cdot
\frac{\rho_{FS}}{\rho_M}
\cdot
\left(\frac{n_{FS}}{n_M}\right)^2
\cdot
\left(\frac{D_{FS}}{D_M}\right)^2
\]

where:

- \(p_M\) – measured model pressure amplitude
- \(p_{FS}\) – scaled full-scale pressure amplitude
- \(\rho\) – water density
- \(n\) – rotational speed
- \(D\) – propeller diameter

The complete scaling factor is:

\[
K_p=
\rho_{ratio}
\cdot
(n_{ratio})^2
\cdot
(scale)^2
\]

---

### 7. Stability Metrics

#### Mean

\[
\bar{x}=\frac{1}{N}\sum_{i=1}^{N}x_i
\]

Average harmonic amplitude after filtering.

---

#### Standard deviation

\[
\sigma=
\sqrt{
\frac{1}{N-1}
\sum_{i=1}^{N}(x_i-\bar{x})^2
}
\]

Measures amplitude variation.

---

#### Coefficient of Variation

\[
CoV=\frac{\sigma}{\bar{x}}\cdot100\%
\]

Interpretation:

- <10% – stable signal
- 10–30% – moderate variation
- >30% – unstable signal

---

#### IQR / Median

\[
R_{IQR}=\frac{IQR}{median(x)}
\]

Interpretation:

- <0.2 – stable
- 0.2–0.5 – moderate
- >0.5 – unstable

---

#### Quartile Dispersion (CQD)

\[
CQD=
\frac{Q_3-Q_1}{Q_3+Q_1}
\]

Interpretation:

- close to 0 – stable
- >0.3 – unstable

---
