import librosa
import numpy as np
from scipy.signal import find_peaks
import json
import argparse # Ensure argparse is imported if not already


def freq_to_midi(freq):
    """Converts a frequency (Hz) to a MIDI note number."""
    if freq <= 0:
        return 0
    return librosa.hz_to_midi(freq)

def midi_to_note_name(midi_note_num):
    """
    Converts a MIDI note number to its note name (e.g., 60 -> C4).
    Uses librosa's default mapping.
    """
    if midi_note_num is None or not (0 <= midi_note_num <= 127):
        return None
    return librosa.midi_to_note(midi_note_num, cents=False)


def constrain_midi_to_octave(midi_note, target_octave_midi_start=60):
    """
    Constrains a MIDI note number to a specific octave range (12 semitones).
    E.g., if target_octave_midi_start is 60 (C4), then notes will be constrained to C4-B4.
    Notes are 'wrapped' into the target octave.
    """
    if midi_note is None:
        return None

    # Calculate the pitch class (0-11)
    pitch_class = midi_note % 12

    # Calculate the starting MIDI note of the target octave's C (if target_octave_midi_start is a C)
    # If target_octave_midi_start is, say, F#4 (66), then the octave range is F#4-F#5.
    # The constrained MIDI will be (target_octave_midi_start + pitch_class - target_octave_midi_start % 12)
    # A simpler way is to map to the pitch class of the target start note, then add the target start note's octave base.

    # Option 1: Wrap relative to the *starting pitch* of the target octave.
    # This keeps the "shape" of the melody but shifts its octave.
    # For example, if target is C4 (60) and input is C5 (72):
    # (72 - 60) % 12 + 60 = 12 % 12 + 60 = 0 + 60 = 60 (C4) -> Correct
    # If target is C4 (60) and input is B3 (59):
    # (59 - 60) % 12 + 60 = -1 % 12 + 60 = 11 + 60 = 71 (B4) -> Correct
    constrained_midi = ((midi_note - target_octave_midi_start) % 12 + 12) % 12 + target_octave_midi_start
    return constrained_midi

    # Option 2 (Less common for "constrain to octave"): If you literally want all notes to be
    # C4 or D4 or E4 etc., without wrapping above B4 to C4 again, you'd clamp the range.
    # But "constrain to a single octave" usually implies wrapping.

def extract_prominent_frequencies(audio_path, top_n=12, frame_size=2048, hop_length=512, sr=None, freq_min=20, freq_max=20000,
                                  prominence_factor=0.01, constrain_octave_start_note=None):
    """
    Extracts the N most prominent frequencies, converts them to MIDI note numbers,
    and optionally constrains them to a single octave, along with their average magnitudes
    over the duration of an audio sample using STFT.

    Args:
        audio_path (str): Path to the audio file.
        top_n (int): The number of most prominent MIDI notes to return.
        frame_size (int): FFT window size (N_FFT).
        hop_length (int): Number of samples between successive frames.
        sr (int, optional): Sample rate.
        freq_min (float): Minimum frequency to consider (Hz).
        freq_max (float): Maximum frequency to consider (Hz).
        prominence_factor (float): Factor for peak prominence threshold.
        constrain_octave_start_note (str, optional): If provided (e.g., "C4"),
                                                     notes will be constrained to this octave.
    Returns:
        list: A list of tuples (note_name, average_magnitude, original_frequency)
              for the top N frequencies, sorted by pitch (lowest to highest).
    """
    try:
        y, sr = librosa.load(audio_path, sr=sr)
    except Exception as e:
        print(f"Error loading audio file: {e}")
        return []

    D = librosa.stft(y, n_fft=frame_size, hop_length=hop_length)
    magnitude_spectrogram = np.abs(D)
    frequencies = librosa.fft_frequencies(sr=sr, n_fft=frame_size)

    valid_freq_indices = np.where((frequencies >= freq_min) & (frequencies <= freq_max))[0]
    filtered_frequencies = frequencies[valid_freq_indices]
    filtered_magnitude_spectrogram = magnitude_spectrogram[valid_freq_indices, :]

    if filtered_frequencies.size == 0:
        print("No frequencies found within the specified Hz range.")
        return []

    average_spectrum = np.mean(filtered_magnitude_spectrogram, axis=1)
    prominence_threshold = prominence_factor * np.max(average_spectrum)
    peaks, properties = find_peaks(average_spectrum, prominence=prominence_threshold)

    all_found_notes_data = []
    target_constrain_midi_start = None
    if constrain_octave_start_note:
        target_constrain_midi_start = librosa.note_to_midi(constrain_octave_start_note)
        if target_constrain_midi_start is None:
            print(f"Warning: Could not convert '{constrain_octave_start_note}' to MIDI for octave constraint. Constraint will be ignored.")


    for p_idx in peaks:
        original_freq = filtered_frequencies[p_idx]
        midi_note_float = freq_to_midi(original_freq)
        midi_note_int = int(round(midi_note_float))

        # Apply octave constraint here if requested
        constrained_midi_note = midi_note_int
        if constrain_octave_start_note and target_constrain_midi_start is not None:
             constrained_midi_note = constrain_midi_to_octave(midi_note_int, target_constrain_midi_start)

        # Convert to note name AFTER constraining
        note_name = midi_to_note_name(constrained_midi_note)
        mag = average_spectrum[p_idx]

        if note_name: # Only add if note_name conversion was successful
            all_found_notes_data.append((note_name, mag, original_freq))

    # Sort by magnitude (loudest first), then take top_n
    all_found_notes_data.sort(key=lambda x: x[1], reverse=True)
    top_notes_by_magnitude = all_found_notes_data[:top_n]

    # Finally, sort the top N by pitch (MIDI value derived from note_name)
    top_notes_by_magnitude.sort(key=lambda x: librosa.note_to_midi(x[0]), reverse=False)

    return top_notes_by_magnitude

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract prominent frequencies, convert to MIDI, constrain octave, and output as JSON note names.")
    parser.add_argument("audio_file", help="Path to the input audio file.")
    parser.add_argument("-n", "--top_n", type=int, default=12,
                        help="Number of most prominent MIDI notes to extract (default: 12).")
    parser.add_argument("--frame_size", type=int, default=2048,
                        help="FFT window size (N_FFT), ideally a power of 2 (default: 2048).")
    parser.add_argument("--hop_length", type=int, default=512,
                        help="Number of samples between successive frames (default: 512).")
    parser.add_argument("--sr", type=int, default=None,
                        help="Sample rate (Hz). If not specified, librosa will detect.")
    parser.add_argument("--freq_min", type=float, default=20,
                        help="Minimum frequency to consider (Hz) (default: 20).")
    parser.add_argument("--freq_max", type=float, default=20000,
                        help="Maximum frequency to consider (Hz) (default: 20000).")
    parser.add_argument("--prominence_factor", type=float, default=0.01,
                        help="Factor for peak prominence threshold (default: 0.01).")
    parser.add_argument("-o", "--output_json", type=str,
                        help="Optional: Path to output JSON file. If not provided, output to console.")
    parser.add_argument("--constrain_octave_start_note", type=str, default=None,
                        help="Optional: Constrain notes to the octave starting at this note (e.g., 'C4' for C4-B4).")


    args = parser.parse_args()

    # Pass the prominence_factor to the extraction function
    prominent_notes_data = extract_prominent_frequencies(
        args.audio_file,
        top_n=args.top_n,
        frame_size=args.frame_size,
        hop_length=args.hop_length,
        sr=args.sr,
        freq_min=args.freq_min,
        freq_max=args.freq_max,
        prominence_factor=args.prominence_factor,
        constrain_octave_start_note=args.constrain_octave_start_note
    )

    note_names_list = [item[0] for item in prominent_notes_data] # Extract just the note names

    if note_names_list:
        if args.output_json:
            try:
                with open(args.output_json, 'w') as f:
                    json.dump(note_names_list, f, indent=4)
                print(f"Note names successfully saved to {args.output_json}")
            except Exception as e:
                print(f"Error saving JSON to file: {e}")
                print("\nFalling back to console output:")
                print(json.dumps(note_names_list, indent=4))
        else:
            print(f"Top {args.top_n} most prominent MIDI notes (sorted by pitch) as Note Names:")
            if args.constrain_octave_start_note:
                print(f"  (Constrained to octave starting at: {args.constrain_octave_start_note})")
            print("------------------------------------------------------------------")
            print(json.dumps(note_names_list, indent=4))
    else:
        print("No prominent notes found within the specified range or audio file could not be processed.")
        if args.output_json:
            try:
                with open(args.output_json, 'w') as f:
                    json.dump([], f, indent=4)
                print(f"Empty note list saved to {args.output_json}")
            except Exception as e:
                print(f"Error saving empty JSON to file: {e}. Printing to console instead.")
                print("[]")