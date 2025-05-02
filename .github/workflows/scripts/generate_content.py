import os
import google.generativeai as genai
import asyncio
import edge_tts
from PIL import Image
import io

# Configurar Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Generar guion y prompts para imágenes con Gemini
prompt = """
Crea un guion de 3 minutos para un video educativo sobre el cambio climático. Divide el texto en 3 segmentos de 1 minuto, cada uno con un máximo de 150 palabras. 
Para cada segmento, proporciona un prompt en español para generar una imagen fotorrealista relacionada (máximo 50 palabras, resolución 1920x1080, estilo fotorrealista).
Formato de respuesta:
Segmento 1: [texto]
Prompt imagen 1: [prompt]
Segmento 2: [texto]
Prompt imagen 2: [prompt]
Segmento 3: [texto]
Prompt imagen 3: [prompt]
"""
response = model.generate_content(prompt)
segments = response.text.split("\nPrompt imagen")[0::2]  # Extrae segmentos
prompts = [p.strip() for p in response.text.split("Prompt imagen")[1:]]  # Extrae prompts

# Generar subtítulos en formato SRT
srt_content = ""
for i, segment in enumerate(segments, 1):
    start_time = f"00:{(i-1)*60:02d}:00,000"
    end_time = f"00:{i*60:02d}:00,000"
    srt_content += f"{i}\n{start_time} --> {end_time}\n{segment.strip()}\n\n"

with open("subtitles.srt", "w", encoding="utf-8") as f:
    f.write(srt_content)

# Generar imágenes con Gemini (modelo de imagen, ej. Imagen)
os.makedirs("images", exist_ok=True)
for i, prompt in enumerate(prompts, 1):
    image_response = model.generate_content([
        {"text": f"Genera una imagen fotorrealista basada en: {prompt.strip()}"}
    ], modality="image")
    image_data = image_response.image  # Asume que Gemini devuelve datos de imagen
    image = Image.open(io.BytesIO(image_data))
    image = image.resize((1920, 1080))  # Asegura resolución 1920x1080
    image.save(f"images/image{i}.jpg", "JPEG")

# Generar voz en off con Edge TTS
async def generate_voice():
    for i, segment in enumerate(segments, 1):
        communicate = edge_tts.Communicate(segment.strip(), voice="es-ES-ElviraNeural")
        await communicate.save(f"output/voice_segment_{i}.mp3")

asyncio.run(generate_voice())
