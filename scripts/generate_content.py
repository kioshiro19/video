import os
import google.generativeai as genai
import asyncio
import edge_tts
import requests
from PIL import Image
import io
import shutil

# Configurar claves API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
if not GEMINI_API_KEY or not PEXELS_API_KEY:
    print("Error: Faltan GEMINI_API_KEY o PEXELS_API_KEY")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Verificar imágenes de respaldo
for i in range(1, 4):
    if not os.path.exists(f"images/fallback{i}.jpg"):
        print(f"Error: No se encuentra images/fallback{i}.jpg")
        exit(1)

# Generar guion y palabras clave
prompt = """
Crea un guion de 3 minutos sobre cambio climático, dividido en 3 segmentos de 1 minuto (máximo 150 palabras cada uno).
Para cada segmento, incluye una palabra clave en español (máximo 10 caracteres) para una imagen fotorrealista.
Formato:
Segmento 1: [texto]
Palabra clave 1: [keyword]
Segmento 2: [texto]
Palabra clave 2: [keyword]
Segmento 3: [texto]
Palabra clave 3: [keyword]
"""
try:
    response = model.generate_content(prompt)
    segments = response.text.split("\nPalabra clave")[0::2]
    keywords = [k.strip() for k in response.text.split("Palabra clave")[1:]]
except Exception as e:
    print(f"Error con Gemini: {e}")
    exit(1)

# Generar subtítulos SRT
srt_content = ""
for i, segment in enumerate(segments, 1):
    start_time = f"00:{(i-1)*60:02d}:00,000"
    end_time = f"00:{i*60:02d}:00,000"
    srt_content += f"{i}\n{start_time} --> {end_time}\n{segment.strip()}\n\n"

with open("subtitles.srt", "w", encoding="utf-8") as f:
    f.write(srt_content)

# Generar imágenes con Pexels
for i, keyword in enumerate(keywords, 1):
    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": keyword.strip(), "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": PEXELS_API_KEY}
        )
        if response.status_code == 200 and response.json().get("photos"):
            image_url = response.json()["photos"][0]["src"]["large"]
            image_response = requests.get(image_url)
            image = Image.open(io.BytesIO(image_response.content))
            image = image.resize((1920, 1080))
            image.save(f"images/image{i}.jpg", "JPEG")
            print(f"Imagen {i} generada: {keyword}")
        else:
            print(f"Fallo en Pexels para {keyword}, usando fallback")
            shutil.copy(f"images/fallback{i}.jpg", f"images/image{i}.jpg")
    except Exception as e:
        print(f"Error generando imagen {i}: {e}, usando fallback")
        shutil.copy(f"images/fallback{i}.jpg", f"images/image{i}.jpg")

# Generar voz con Edge TTS
async def generate_voice():
    for i, segment in enumerate(segments, 1):
        try:
            communicate = edge_tts.Communicate(segment.strip(), voice="es-ES-ElviraNeural")
            await communicate.save(f"output/voice_segment_{i}.mp3")
            print(f"Voz {i} generada")
        except Exception as e:
            print(f"Error generando voz {i}: {e}")
            exit(1)

asyncio.run(generate_voice())

# Verificar archivos generados
for i in range(1, 4):
    if not os.path.exists(f"images/image{i}.jpg"):
        print(f"Error: No se encuentra images/image{i}.jpg")
        exit(1)
    if not os.path.exists(f"output/voice_segment_{i}.mp3"):
        print(f"Error: No se encuentra output/voice_segment_{i}.mp3")
        exit(1)
if not os.path.exists("subtitles.srt"):
    print("Error: No se encuentra subtitles.srt")
    exit(1)
