#!/bin/bash

# Crear directorio de salida si no existe
mkdir -p output

# Combinar los segmentos de audio
ffmpeg -y -i output/voice_segment_1.mp3 -i output/voice_segment_2.mp3 -i output/voice_segment_3.mp3 \
  -filter_complex "[0:a][1:a][2:a]concat=n=3:v=0:a=1[outa]" -map "[outa]" output/full_audio.mp3

# Crear video con imágenes estáticas (1 minuto por imagen) y audio
ffmpeg -y \
  -loop 1 -t 60 -i images/image1.jpg \
  -loop 1 -t 60 -i images/image2.jpg \
  -loop 1 -t 60 -i images/image3.jpg \
  -i output/full_audio.mp3 \
  -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map 3:a -c:v libx264 -c:a aac -shortest output/temp_video.mp4

# Agregar subtítulos
ffmpeg -y -i output/temp_video.mp4 -vf "subtitles=subtitles.srt:force_style='Fontsize=24,PrimaryColour=&Hffffff&'" \
  -c:v libx264 -c:a copy output/final_video.mp4
