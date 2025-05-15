import os
import requests
from gtts import gTTS
from moviepy.editor import ImageSequenceClip, AudioFileClip

# Claves de las APIs
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')

# Función para obtener el guion desde Gemini API
def get_script(topic):
    url = "https://api.gemini.com/generate"
    payload = {"topic": topic, "length": "short"}
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["content"]

# Función para obtener imágenes desde Pexels API
def get_images(topic):
    url = f"https://api.pexels.com/v1/search?query={topic}&per_page=10"
    headers = {"Authorization": PEXELS_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return [photo["src"]["large"] for photo in response.json()["photos"]]

# Función para descargar imágenes
def download_images(image_urls):
    os.makedirs("images", exist_ok=True)
    image_paths = []
    for i, url in enumerate(image_urls):
        response = requests.get(url)
        path = f"images/image_{i}.jpg"
        with open(path, "wb") as f:
            f.write(response.content)
        image_paths.append(path)
    return image_paths

# Función para generar voz en off
def generate_voiceover(script):
    tts = gTTS(text=script, lang="es")
    voice_path = "voiceover.mp3"
    tts.save(voice_path)
    return voice_path

# Función para generar subtítulos
def generate_subtitles(script):
    subtitles_path = "subtitles.srt"
    with open(subtitles_path, "w") as f:
        f.write("1\n00:00:00,000 --> 00:00:10,000\n" + script)
    return subtitles_path

# Función para ensamblar el video
def assemble_video(image_paths, voiceover_path):
    clip = ImageSequenceClip(image_paths, fps=1)  # 1 imagen por segundo
    audio = AudioFileClip(voiceover_path)
    clip = clip.set_audio(audio)
    os.makedirs("output", exist_ok=True)
    output_path = "output/video.mp4"
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path

if __name__ == "__main__":
    topic = os.getenv("INPUT_TOPIC", "la depresión")
    script = get_script(topic)
    print("Guion generado:", script)

    print("Descargando imágenes...")
    image_urls = get_images(topic)
    image_paths = download_images(image_urls)

    print("Generando voz en off...")
    voiceover_path = generate_voiceover(script)

    print("Creando video...")
    video_path = assemble_video(image_paths, voiceover_path)
    print("Video generado:", video_path)
