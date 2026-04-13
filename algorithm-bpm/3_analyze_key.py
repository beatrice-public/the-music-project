import numpy as np
import subprocess
import sys

# Krumhansl-Schmuckler Key Profiles
MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def get_key(audio_file):
    # 1. Use FFmpeg to stream raw PCM audio (16-bit, Mono, 44.1kHz)
    command = [
        'ffmpeg', '-i', audio_file,
        '-f', 's16le', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '44100', '-'
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    # Read audio into NumPy array
    audio_data = np.frombuffer(process.stdout.read(), dtype=np.int16)
    
    # 2. Compute Magnitude Spectrum (FFT)
    # Using a large window to get better frequency resolution
    fft_data = np.abs(np.fft.rfft(audio_data))
    freqs = np.fft.rfftfreq(len(audio_data), 1/44100)
    
    # 3. Map Frequencies to Chromagram Bins
    chroma = np.zeros(12)
    for i, f in enumerate(freqs):
        if f > 20: # Ignore sub-bass
            # Convert Frequency to MIDI Note Number: 12 * log2(f/440) + 69
            note_num = int(round(12 * np.log2(f / 440.0) + 69)) % 12
            chroma[note_num] += fft_data[i]
            
    # Normalize chroma
    chroma /= np.sum(chroma)
    
    # 4. Correlation (Template Matching)
    best_corr = -1
    best_key = ""
    
    for i in range(12):
        # Rotate profiles to check every key
        maj_corr = np.corrcoef(chroma, np.roll(MAJOR, i))[0, 1]
        min_corr = np.corrcoef(chroma, np.roll(MINOR, i))[0, 1]
        
        if maj_corr > best_corr:
            best_corr = maj_corr
            best_key = f"{NOTES[i]} Major"
        if min_corr > best_corr:
            best_corr = min_corr
            best_key = f"{NOTES[i]} Minor"
            
    return best_key

if __name__ == "__main__":
    print(f"Detected Key: {get_key(sys.argv[1])}")

