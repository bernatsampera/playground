import sounddevice as sd
import numpy as np
import whisper
import sys
import threading

# Configuration
SAMPLE_RATE = 16000  # Whisper works best at 16kHz

def record_until_key(key="s"):
    """
    Records audio until the user presses the given key in the terminal.
    Returns the recorded audio as a 1D numpy array.
    """
    print(f"Recording... Press '{key}' then Enter to stop.")

    audio_buffer = []

    def audio_callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        audio_buffer.append(indata.copy())

    # Flag to stop recording
    stop_flag = threading.Event()

    def wait_for_key():
        while True:
            user_input = sys.stdin.readline().strip().lower()
            if user_input == key:
                stop_flag.set()
                break

    key_thread = threading.Thread(target=wait_for_key, daemon=True)
    key_thread.start()

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', callback=audio_callback):
        while not stop_flag.is_set():
            sd.sleep(100)  # Small sleep to reduce CPU usage

    print("Recording stopped.")
    return np.ravel(np.concatenate(audio_buffer, axis=0))

def transcribe_audio(audio, model_name="base"):
    """
    Loads a Whisper model and transcribes the given audio.
    """
    print(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)
    result = model.transcribe(audio)
    return result["text"]

def main():
    audio = record_until_key("s")
    text = transcribe_audio(audio)
    print("\nTranscribed text:")
    print(text)

if __name__ == "__main__":
    main()
