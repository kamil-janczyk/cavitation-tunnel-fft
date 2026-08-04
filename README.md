# cavitation-tunnel-fft

A Streamlit application for analysing pressure signals from cavitation tunnel experiments.

The application performs:

loading Spider8, QuantumX and CSV measurements
gain calibration
sliding-window FFT
Blade Passing Frequency (BPF) harmonic extraction
robust harmonic detection
IQR-based outlier rejection
model-to-full-scale scaling
statistical analysis of harmonic stability
CSV export of processed results
Supported formats
Spider8 (.asc)
QuantumX (.asc)
CSV (5 pressure channels)
Installation
git clone https://github.com/yourname/cavitation-tunnel-fft.git

cd cavitation-tunnel-fft

pip install -r requirements.txt

streamlit run app.py
Features
Sliding FFT
Robust ±2 Hz harmonic search
Gain calibration
IQR filtering
Automatic full-scale conversion
Multiple file processing
Interactive plots
CSV export
