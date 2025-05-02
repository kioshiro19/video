import os
import google.generativeai as genai
import asyncio
import edge_tts
import requests
import json

# Configurar Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Generar guion y prompts para imágenes con Gemini
prompt = """
Crea un guion de 3 minutos para un video educativo sobre el cambio climático. Divide el texto en 3 segmentos de 1 minuto, cada uno con un máximo de 150 palabras. 
Para cada segmento, proporciona un prompt en español para generar una imagen relacionada (máximo 50 palabras, estilo fotorrealista, resolución 1920x1080).
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

# Generar imágenes con DALL-E Mini (Craiyon API)
os.makedirs("images", exist_ok=True)
for i, prompt in enumerate(prompts, 1):
    response = requests.post(
        "https://api.craiyon.com/v1/images/generations",
        json={"prompt": prompt.strip()}
    )
    if response.status_code == 200:
        image_data = response.json()["images"][0]["url"]
        image_response = requests.get(image_data)
        with open(f"images/image{i}.jpg", "wb") as f:
            f.write(image_response.content)

# Generar voz en off con Edge TTS
async def generate_voice():
    for i, segment in enumerate(segments, 1):
        communicate = edge_tts.Communicate(segment.strip(), voice="es-ES-ElviraNeural")
        await communicate.save(f"output/voice_segment_{i}.mp3")

asyncio.run(generate_voice())
