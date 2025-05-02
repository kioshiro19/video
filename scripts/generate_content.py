import os
import google.generativeai as genai
import asyncio
import edge_tts
import requests
from PIL import Image
import io

# Configurar Gemini API
GEMINI_API_KEY = os.getenv("AIzaSyBO5CuTMECW-35h6pCKbn9cfUdfHSQlMJA")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Configurar Pexels API
PEXELS_API_KEY = os.getenv("zb0iInbJryadQvGAFX8L1W22I38ns3wAPXXeSP6quQE3QfZQF8KzWOb2")

# Imágenes de respaldo (enlaces públicos de Pexels, sin API)
FALLBACK_IMAGES = [
    "https://images.pexels.com/photos/414171/pexels-photo-414171.jpeg",
    "https://images.pexels.com/photos/1632790/pexels-photo-1632790.jpeg",
    "https://images.pexels.com/photos/518543/pexels-photo-518543.jpeg"
]

# Generar guion y palabras clave para imágenes con Gemini
prompt = """
Crea un guion de 3 minutos para un video educativo sobre el cambio climático. Divide el texto en 3 segmentos de 1 minuto, cada uno con un máximo de 150 palabras. 
Para cada segmento, proporciona una palabra clave en español para buscar una imagen fotorrealista relacionada (máximo 10 caracteres, relevante al tema).
Formato de respuesta:
Segmento 1: [texto]
Palabra clave 1: [keyword]
Segmento 2: [texto]
Palabra clave 2: [keyword]
Segmento 3: [texto]
Palabra clave 3: [keyword]
"""
try:
    response = model.generate_content(prompt)
    segments = response.text.split("\nPalabra clave")[0::2]  # Extrae segmentos
    keywords = [k.strip() for k in response.text.split("Palabra clave")[1:]]  # Extrae palabras clave
except Exception as e:
    print(f"Error generando guion con Gemini: {e}")
    exit(1)

# Generar subtítulos en formato SRT
srt_content = ""
for i, segment in enumerate(segments, 1):
    start_time = f"00:{(i-1)*60:02d}:00,000"
    end_time = f"00:{i*60:02d}:00,000"
    srt_content += f"{i}\n{start_time} --> {end_time}\n{segment.strip()}\n\n"

with open("subtitles.srt", "w", encoding="utf-8") as f:
    f.write(srt_content)

# Crear carpetas necesarias
os.makedirs("images", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Generar imágenes con Pexels API
for i, keyword in enumerate(keywords, 1):
    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": keyword.strip(), "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": PEXELS_API_KEY}
        )
        if response.status_code == 200:
            photos = response.json().get("photos", [])
            if photos:
                image_url = photos[0]["src"]["large"]
                image_response = requests.get(image_url)
                image = Image.open(io.BytesIO(image_response.content))
                image = image.resize((1920, 1080))  # Asegura resolución 1920x1080
                image.save(f"images/image{i}.jpg", "JPEG")
                print(f"Imagen {i} generada con éxito para palabra clave: {keyword}")
            else:
                print(f"No se encontraron imágenes para la palabra clave {keyword}, usando imagen de respaldo")
                image_response = requests.get(FALLBACK_IMAGES[i-1])
                image = Image.open(io.BytesIO(image_response.content))
                image = image.resize((1920, 1080))
                image.save(f"images/image{i}.jpg", "JPEG")
        else:
            print(f"Error generando imagen {i}: {response.status_code}, usando imagen de respaldo")
            image_response = requests.get(FALLBACK_IMAGES[i-1])
            image = Image.open(io.BytesIO(image_response.content))
            image = image.resize((1920, 1080))
            image.save(f"images/image{i}.jpg", "JPEG")
    except Exception as e:
        print(f"Excepción al generar imagen {i}: {e}, usando imagen de respaldo")
        image_response = requests.get(FALLBACK_IMAGES[i-1])
        image = Image.open(io.BytesIO(image_response.content))
        image = image.resize((1920, 1080))
        image.save(f"images/image{i}.jpg", "JPEG")

# Generar voz en off con Edge TTS
async def generate_voice():
    for i, segment in enumerate(segments, 1):
        try:
            communicate = edge_tts.Communicate(segment.strip(), voice="es-ES-ElviraNeural")
            await communicate.save(f"output/voice_segment_{i}.mp3")
            print(f"Segmento de voz {i} generado con éxito")
        except Exception as e:
            print(f"Error generando segmento de voz {i}: {e}")
            exit(1)

asyncio.run(generate_voice())

# Verificar que todos los archivos necesarios existen
for i in range(1, 4):
    if not os.path.exists(f"images/image{i}.jpg"):
        print(f"Error: No se encontró images/image{i}.jpg")
        exit(1)
    if not os.path.exists(f"output/voice_segment_{i}.mp3"):
        print(f"Error: No se encontró output/voice_segment_{i}.mp3")
        exit(1)
