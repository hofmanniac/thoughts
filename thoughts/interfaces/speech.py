import io
import requests
import sounddevice as sd
import soundfile as sf

def speak(text: str, voice: str = None) -> None:

    # API endpoint URL
    url = "http://127.0.0.1:5005/speak"

    default_voice = "af_alloy"
    if voice is None: voice = default_voice

    # JSON payload
    payload = {
        "text": text,
        "voice": voice
    }

    # Make the POST request
    try:
        response = requests.post(url, json=payload, stream=True)

        # Check if the request was successful
        if response.status_code == 200:

            # Read and play the streamed audio in real-time
            audio_buffer = io.BytesIO()

            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    audio_buffer.write(chunk)

            # Move the buffer pointer to the beginning before reading it
            audio_buffer.seek(0)

            try:
                # Load the audio from the buffer and play it
                data, sample_rate = sf.read(audio_buffer)
                sd.play(data, samplerate=sample_rate)
                sd.wait()
            except:
                print("An error occurred while trying to play the audio")
            #sd.wait()  # Wait until the playback finishes

        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")




