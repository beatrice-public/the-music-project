import re
import numpy as np
import sys

def run_analysis(file_path):
    times = []
    loudness = []

    # 1. DATA EXTRACTION & SANITIZATION
    # Look for 't: <time>' and 'M: <loudness>' in the FFmpeg log
    pattern = re.compile(r"t:\s+([\d\.]+)\s+M:\s+(-?\d+\.\d+|nan)")

    try:
        with open(file_path, 'r') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    m_val = match.group(2)
                    if m_val != "nan":
                        times.append(float(match.group(1)))
                        loudness.append(float(m_val))

        if not loudness:
            print("Error: No valid data found in the log file.")
            return

        # Convert to NumPy array
        # Col 0: Time (s), Col 1: Loudness (LUFS)
        data = np.column_stack((times, loudness))

        # 2. LOUDNESS STATISTICS
        p95 = np.percentile(data[:, 1], 95)

        # 3. ONSET DETECTION (BPM)
        # Convert LUFS to linear scale for mathematical processing
        linear_loudness = np.power(10, (data[:, 1] / 20))

        # SMOOTHING: Merge tiny spikes into clean onsets (30ms window)
        window_size = 3
        smoothed = np.convolve(linear_loudness, np.ones(window_size)/window_size, mode='same')

        # DERIVATIVE: Calculate the 'attack' (velocity of volume increase)
        diff = np.diff(smoothed, prepend=0)
        diff = np.maximum(diff, 0) # Focus only on onsets

        # THRESHOLDING: Find the top 5% of volume jumps
        thresh = np.percentile(diff, 95)
        peaks = np.where(diff > thresh)[0]

        bpm = 0
        if len(peaks) > 1:
            # Calculate time intervals between detected peaks
            peak_times = data[peaks, 0]
            intervals = np.diff(peak_times)

            # Filter for realistic intervals (approx 60-180 BPM)
            valid_intervals = intervals[(intervals > 0.33) & (intervals < 1.0)]

            if len(valid_intervals) > 0:
                # Use Median to ignore syncopation/glitches
                avg_interval = np.median(valid_intervals)
                bpm = 60 / avg_interval

        # --- FINAL REPORT ---
        print("-" * 30)
        print(f"AUDIO ANALYSIS REPORT")
        print("-" * 30)
        print(f"95th Percentile:  {p95:.2f} LUFS")
        print(f"Estimated BPM:    {bpm:.1f}")
        print(f"Samples Analyzed: {len(data)}")
        print("-" * 30)

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")

if __name__ == "__main__":
    # Allows you to run: python3 analyze.py your_log_file.txt
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'raw_loudness.txt'
    run_analysis(log_file)

