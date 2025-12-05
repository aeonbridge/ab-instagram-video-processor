# Projeto: Canal Dark Viral de Cortes - Sistema Automatizado

## Visão Geral do Sistema

Vou projetar uma arquitetura completa para automação de um canal de cortes virais. O sistema será modular, permitindo escalar cada componente independentemente.

---

## Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE PRINCIPAL                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐│
│  │ Monitor  │──▶│ Download │──▶│ Análise  │──▶│ Edição   │──▶│Publish ││
│  │ Channels │   │ Manager  │   │ & Corte  │   │ & Capa   │   │Manager ││
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘│
│       │              │              │              │              │     │
│       ▼              ▼              ▼              ▼              ▼     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      BANCO DE DADOS CENTRAL                     │   │
│  │  (PostgreSQL + Redis para filas + S3 para mídia)                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Módulo 1: Monitoramento de Canais

### Objetivo
Rastrear canais top de um nicho e identificar vídeos com potencial viral.

### Stack Técnica
- **YouTube Data API v3** — dados oficiais de canais e vídeos
- **yt-dlp** — fallback para métricas adicionais
- **Celery + Redis** — agendamento de tarefas
- **PostgreSQL** — persistência

### Estrutura de Dados

```python
# models/channel.py
class Channel:
    id: str                    # YouTube channel ID
    name: str
    niche: str                 # "games", "humor", "tech"
    subscriber_count: int
    avg_views_per_video: int
    monitoring_priority: int   # 1-10
    last_checked: datetime

class Video:
    id: str                    # YouTube video ID
    channel_id: str
    title: str
    views: int
    likes: int
    comments: int
    published_at: datetime
    duration_seconds: int
    viral_score: float         # Calculado
    status: str                # "new", "analyzed", "processed", "published"
```

### Algoritmo de Viral Score

```python
def calculate_viral_score(video, channel_avg_views):
    """
    Score de 0-100 baseado em múltiplos fatores
    """
    # Fator 1: Performance vs média do canal
    view_ratio = video.views / max(channel_avg_views, 1)
    
    # Fator 2: Engajamento (likes + comments / views)
    engagement_rate = (video.likes + video.comments * 2) / max(video.views, 1)
    
    # Fator 3: Velocidade de crescimento (views por hora desde publicação)
    hours_since_publish = (datetime.now() - video.published_at).total_seconds() / 3600
    velocity = video.views / max(hours_since_publish, 1)
    
    # Fator 4: Recência (vídeos mais novos = mais relevantes)
    recency_bonus = max(0, 30 - hours_since_publish) / 30
    
    # Ponderação final
    score = (
        view_ratio * 30 +
        engagement_rate * 1000 * 25 +
        min(velocity / 1000, 1) * 25 +
        recency_bonus * 20
    )
    
    return min(score, 100)
```

### Agendamento

```python
# tasks/monitoring.py
@celery.task
def scan_channels_for_niche(niche: str):
    """Executa a cada 2 horas"""
    channels = Channel.query.filter_by(niche=niche, active=True).all()
    
    for channel in channels:
        recent_videos = youtube_api.get_recent_videos(
            channel_id=channel.id,
            max_results=10,
            published_after=datetime.now() - timedelta(days=3)
        )
        
        for video_data in recent_videos:
            video = Video.from_api_response(video_data)
            video.viral_score = calculate_viral_score(video, channel.avg_views)
            
            if video.viral_score >= VIRAL_THRESHOLD:
                queue_for_download.delay(video.id)
```

---

## Módulo 2: Download Manager

### Objetivo
Baixar vídeos qualificados de forma eficiente e organizada.

### Stack Técnica
- **yt-dlp** — download robusto com fallbacks
- **FFmpeg** — conversão e normalização
- **MinIO/S3** — armazenamento de mídia

### Implementação

```python
# services/downloader.py
import yt_dlp
from pathlib import Path

class VideoDownloader:
    def __init__(self, output_dir: str, s3_client):
        self.output_dir = Path(output_dir)
        self.s3 = s3_client
        
    def download(self, video_id: str) -> dict:
        """
        Baixa vídeo em melhor qualidade até 1080p
        Retorna metadados e caminho local
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        output_template = str(self.output_dir / f"{video_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['pt', 'en'],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
        local_path = self.output_dir / f"{video_id}.mp4"
        
        # Upload para S3
        s3_key = f"raw_videos/{video_id}.mp4"
        self.s3.upload_file(str(local_path), s3_key)
        
        return {
            'video_id': video_id,
            'local_path': str(local_path),
            's3_key': s3_key,
            'duration': info['duration'],
            'title': info['title'],
            'description': info.get('description', ''),
            'subtitles_path': self._get_subtitles_path(video_id)
        }
```

---

## Módulo 3: Análise e Identificação de Trechos Virais

### Objetivo
Identificar automaticamente os melhores momentos do vídeo.

### Stack Técnica
- **Whisper (OpenAI)** — transcrição de áudio
- **PySceneDetect** — detecção de cortes de cena
- **librosa** — análise de áudio (picos de energia)
- **Claude API** — análise semântica do conteúdo
- **OpenCV** — análise visual

### Sinais de Momentos Virais

```python
# analyzers/viral_moment_detector.py
from dataclasses import dataclass
from typing import List
import numpy as np

@dataclass
class MomentScore:
    start_time: float
    end_time: float
    audio_energy: float      # Picos de áudio/reações
    scene_changes: int       # Mudanças visuais
    speech_density: float    # Quantidade de fala
    keyword_hits: int        # Palavras-chave virais
    sentiment_intensity: float
    final_score: float

class ViralMomentDetector:
    VIRAL_KEYWORDS = {
        'games': ['insano', 'clutch', 'play', 'inacreditável', 'mano', 
                  'caraca', 'impossible', 'goat', 'melhor', 'pior'],
        'humor': ['kkk', 'morri', 'rachei', 'não aguento', 'socorro'],
    }
    
    def __init__(self, niche: str):
        self.niche = niche
        self.keywords = self.VIRAL_KEYWORDS.get(niche, [])
        
    def analyze_video(self, video_path: str, transcript: dict) -> List[MomentScore]:
        """
        Análise multi-modal para encontrar melhores momentos
        """
        # 1. Análise de áudio
        audio_peaks = self._analyze_audio_energy(video_path)
        
        # 2. Análise de cenas
        scene_changes = self._detect_scene_changes(video_path)
        
        # 3. Análise de transcrição
        speech_segments = self._analyze_speech(transcript)
        
        # 4. Combinar sinais em janelas de tempo
        moments = self._combine_signals(
            audio_peaks, 
            scene_changes, 
            speech_segments,
            window_size=60  # segundos
        )
        
        return sorted(moments, key=lambda m: m.final_score, reverse=True)
    
    def _analyze_audio_energy(self, video_path: str) -> List[tuple]:
        """Detecta picos de energia no áudio (reações, gritos, etc)"""
        import librosa
        
        y, sr = librosa.load(video_path, sr=22050)
        
        # RMS energy em janelas de 1 segundo
        rms = librosa.feature.rms(y=y, frame_length=sr, hop_length=sr)[0]
        
        # Encontrar picos (2x acima da média)
        threshold = np.mean(rms) * 2
        peaks = []
        
        for i, energy in enumerate(rms):
            if energy > threshold:
                peaks.append((i, float(energy)))  # (segundo, energia)
                
        return peaks
    
    def _detect_scene_changes(self, video_path: str) -> List[float]:
        """Detecta mudanças de cena usando PySceneDetect"""
        from scenedetect import detect, ContentDetector
        
        scene_list = detect(video_path, ContentDetector(threshold=30))
        return [scene[0].get_seconds() for scene in scene_list]
    
    def _analyze_speech(self, transcript: dict) -> List[dict]:
        """Analisa transcrição para keywords e intensidade"""
        segments = []
        
        for segment in transcript['segments']:
            text = segment['text'].lower()
            keyword_count = sum(1 for kw in self.keywords if kw in text)
            
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'],
                'keywords': keyword_count,
                'word_density': len(text.split()) / (segment['end'] - segment['start'])
            })
            
        return segments
```

### Análise Semântica com IA

```python
# analyzers/content_analyzer.py
from anthropic import Anthropic

class ContentAnalyzer:
    def __init__(self):
        self.client = Anthropic()
        
    def extract_viral_moments(self, transcript: str, niche: str) -> dict:
        """
        Usa Claude para identificar momentos de alto potencial viral
        """
        prompt = f"""Analise esta transcrição de um vídeo de {niche} e identifique:

1. Os 3-5 momentos mais impactantes/engraçados/emocionantes
2. Para cada momento, indique:
   - Timestamp aproximado (baseado no fluxo da conversa)
   - Por que esse momento tem potencial viral
   - Sugestão de título clickbait para o corte
   - Palavras-chave principais

Transcrição:
{transcript}

Responda em JSON com a estrutura:
{{
  "moments": [
    {{
      "estimated_position": "início/meio/fim",
      "quote": "frase exata do momento",
      "viral_reason": "...",
      "suggested_title": "...",
      "keywords": ["...", "..."]
    }}
  ],
  "main_topic": "...",
  "overall_tone": "..."
}}"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
```

---

## Módulo 4: Edição Automatizada

### Objetivo
Recortar, processar e preparar o vídeo final.

### Stack Técnica
- **FFmpeg** — corte e processamento principal
- **MoviePy** — manipulações avançadas
- **Pillow** — geração de thumbnails

### Implementação de Corte

```python
# editors/video_cutter.py
import subprocess
from pathlib import Path

class VideoCutter:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        
    def cut_clip(
        self, 
        source_path: str, 
        start_time: float, 
        duration: int,  # 30, 45, ou 60
        output_name: str
    ) -> str:
        """
        Corta trecho do vídeo com fade in/out
        """
        output_path = self.output_dir / f"{output_name}.mp4"
        
        # FFmpeg com fade de 0.5s no início e fim
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-i', source_path,
            '-t', str(duration),
            '-vf', f'fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5',
            '-af', f'afade=t=in:st=0:d=0.5,afade=t=out:st={duration-0.5}:d=0.5',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)
    
    def add_intro_overlay(
        self, 
        video_path: str, 
        thumbnail_path: str,
        intro_duration: float = 2.0
    ) -> str:
        """
        Adiciona thumbnail como intro de 2 segundos
        """
        output_path = video_path.replace('.mp4', '_with_intro.mp4')
        
        # Criar vídeo da thumbnail
        thumb_video = video_path.replace('.mp4', '_thumb.mp4')
        
        cmd_thumb = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', thumbnail_path,
            '-t', str(intro_duration),
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            thumb_video
        ]
        subprocess.run(cmd_thumb, check=True)
        
        # Concatenar
        concat_file = video_path.replace('.mp4', '_concat.txt')
        with open(concat_file, 'w') as f:
            f.write(f"file '{thumb_video}'\n")
            f.write(f"file '{video_path}'\n")
            
        cmd_concat = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path
        ]
        subprocess.run(cmd_concat, check=True)
        
        return output_path
```

---

## Módulo 5: Geração de Thumbnails

### Objetivo
Criar capas atraentes e consistentes com a identidade visual.

### Stack Técnica
- **Pillow** — composição de imagens
- **Claude Vision** — seleção de frame ideal
- **DALL-E 3 ou Stable Diffusion** — elementos gráficos (opcional)

### Template System

```python
# thumbnails/generator.py
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import cv2

class ThumbnailGenerator:
    def __init__(self, brand_config: dict):
        """
        brand_config = {
            'primary_color': '#FF0000',
            'secondary_color': '#FFFFFF',
            'font_path': 'fonts/Impact.ttf',
            'logo_path': 'assets/logo.png',
            'style': 'gaming'  # gaming, humor, tech
        }
        """
        self.config = brand_config
        self.templates = self._load_templates()
        
    def generate(
        self, 
        video_path: str, 
        title: str, 
        keywords: List[str],
        best_frame_time: float = None
    ) -> str:
        """
        Gera thumbnail 1280x720 (padrão YouTube)
        """
        # 1. Extrair melhor frame
        if best_frame_time:
            background = self._extract_frame(video_path, best_frame_time)
        else:
            background = self._find_best_frame(video_path)
            
        # 2. Aplicar template
        thumb = self._apply_template(background, title, keywords)
        
        # 3. Adicionar elementos de marca
        thumb = self._add_branding(thumb)
        
        # 4. Salvar
        output_path = video_path.replace('.mp4', '_thumb.jpg')
        thumb.save(output_path, 'JPEG', quality=95)
        
        return output_path
    
    def _extract_frame(self, video_path: str, timestamp: float) -> Image:
        """Extrai frame específico do vídeo"""
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
        cap.release()
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
    
    def _find_best_frame(self, video_path: str) -> Image:
        """
        Encontra frame mais expressivo usando análise de variância
        (frames com mais movimento/expressão têm maior variância)
        """
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        best_frame = None
        best_score = 0
        
        # Amostrar 20 frames distribuídos
        for i in range(20):
            frame_pos = int((i / 20) * total_frames)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            
            if ret:
                # Score baseado em variância (mais detalhes = melhor)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                score = cv2.Laplacian(gray, cv2.CV_64F).var()
                
                if score > best_score:
                    best_score = score
                    best_frame = frame
                    
        cap.release()
        
        frame_rgb = cv2.cvtColor(best_frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
    
    def _apply_template(self, background: Image, title: str, keywords: List[str]) -> Image:
        """Aplica texto e elementos do template"""
        # Redimensionar para 1280x720
        thumb = background.resize((1280, 720), Image.LANCZOS)
        
        # Overlay escuro para legibilidade
        overlay = Image.new('RGBA', thumb.size, (0, 0, 0, 100))
        thumb = Image.alpha_composite(thumb.convert('RGBA'), overlay)
        
        draw = ImageDraw.Draw(thumb)
        
        # Título principal (grande, chamativo)
        title_font = ImageFont.truetype(self.config['font_path'], 72)
        
        # Quebrar título se muito longo
        words = title.upper().split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=title_font)
            if bbox[2] - bbox[0] < 1100:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        
        # Desenhar texto com contorno
        y_position = 350 - (len(lines) * 40)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            x = (1280 - (bbox[2] - bbox[0])) // 2
            
            # Contorno preto
            for dx, dy in [(-3,-3), (-3,3), (3,-3), (3,3)]:
                draw.text((x+dx, y_position+dy), line, font=title_font, fill='black')
            
            # Texto principal
            draw.text((x, y_position), line, font=title_font, fill=self.config['primary_color'])
            y_position += 80
            
        return thumb.convert('RGB')
    
    def _add_branding(self, thumb: Image) -> Image:
        """Adiciona logo e elementos de marca"""
        if self.config.get('logo_path'):
            logo = Image.open(self.config['logo_path']).convert('RGBA')
            logo = logo.resize((100, 100), Image.LANCZOS)
            
            # Posicionar no canto inferior direito
            thumb.paste(logo, (1160, 600), logo)
            
        return thumb
```

---

## Módulo 6: Publicação Automatizada

### Objetivo
Publicar vídeos no YouTube com metadados otimizados.

### Stack Técnica
- **YouTube Data API v3** — upload e gerenciamento
- **OAuth 2.0** — autenticação
- **Claude API** — geração de títulos e descrições

### Implementação

```python
# publishers/youtube_publisher.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubePublisher:
    def __init__(self, credentials_path: str):
        self.credentials = Credentials.from_authorized_user_file(credentials_path)
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        thumbnail_path: str,
        category_id: str = "20",  # Gaming
        privacy: str = "public",
        scheduled_time: datetime = None
    ) -> str:
        """
        Faz upload do vídeo e retorna o video ID
        """
        body = {
            'snippet': {
                'title': title[:100],  # Limite do YouTube
                'description': description[:5000],
                'tags': tags[:500],
                'categoryId': category_id,
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False,
            }
        }
        
        # Se agendado
        if scheduled_time and privacy == 'private':
            body['status']['publishAt'] = scheduled_time.isoformat()
            
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True
        )
        
        request = self.youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response = request.execute()
        video_id = response['id']
        
        # Upload da thumbnail
        self._set_thumbnail(video_id, thumbnail_path)
        
        return video_id
    
    def _set_thumbnail(self, video_id: str, thumbnail_path: str):
        """Define thumbnail customizada"""
        self.youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
```

### Geração de Metadados Virais

```python
# publishers/metadata_generator.py
from anthropic import Anthropic

class MetadataGenerator:
    def __init__(self):
        self.client = Anthropic()
        
    def generate_viral_metadata(
        self,
        clip_content: str,  # Transcrição do corte
        original_title: str,
        original_channel: str,
        niche: str,
        keywords: List[str]
    ) -> dict:
        """
        Gera título, descrição e tags otimizados para viralização
        """
        prompt = f"""Você é um especialista em YouTube Shorts virais no nicho de {niche}.

Baseado neste conteúdo de um corte de vídeo, crie metadados otimizados para máximo alcance:

Conteúdo do corte:
{clip_content}

Canal original: {original_channel}
Título original: {original_title}
Keywords identificadas: {', '.join(keywords)}

Gere:
1. TÍTULO (máx 100 chars): Use técnicas de clickbait ético - curiosidade, emoção, números
2. DESCRIÇÃO (máx 500 chars): Inclua call-to-action, hashtags relevantes, créditos ao original
3. TAGS (20-30): Mix de tags populares e específicas

Importante:
- Não use promessas falsas ou enganosas
- Inclua emojis estrategicamente
- Crie urgência sem ser spam
- Dê crédito ao criador original

Responda em JSON:
{{
  "title": "...",
  "description": "...",
  "tags": ["...", "..."],
  "hashtags": ["#...", "#..."]
}}"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
```

---

## Módulo 7: Orquestração (Pipeline Completo)

### Workflow Manager

```python
# orchestrator/pipeline.py
from celery import chain
from datetime import datetime, timedelta

class ViralClipPipeline:
    def __init__(self, config: dict):
        self.config = config
        
    def run_full_pipeline(self, niche: str):
        """
        Executa pipeline completo para um nicho
        """
        # Celery chain para execução sequencial
        workflow = chain(
            scan_channels.s(niche),
            process_viral_candidates.s(),
            generate_clips.s(),
            schedule_publications.s()
        )
        
        return workflow.apply_async()

# Tasks Celery
@celery.task
def scan_channels(niche: str) -> List[str]:
    """Retorna lista de video_ids com alto viral_score"""
    monitor = ChannelMonitor(niche)
    return monitor.find_viral_candidates(threshold=70)

@celery.task  
def process_viral_candidates(video_ids: List[str]) -> List[dict]:
    """Baixa e analisa vídeos, retorna momentos virais"""
    results = []
    
    for video_id in video_ids:
        # Download
        downloader = VideoDownloader()
        video_data = downloader.download(video_id)
        
        # Transcrição
        transcriber = WhisperTranscriber()
        transcript = transcriber.transcribe(video_data['local_path'])
        
        # Análise de momentos
        detector = ViralMomentDetector(niche)
        moments = detector.analyze_video(
            video_data['local_path'], 
            transcript
        )
        
        # Análise semântica
        analyzer = ContentAnalyzer()
        semantic_analysis = analyzer.extract_viral_moments(
            transcript['text'],
            niche
        )
        
        results.append({
            'video_id': video_id,
            'video_data': video_data,
            'moments': moments[:3],  # Top 3 momentos
            'semantic': semantic_analysis
        })
        
    return results

@celery.task
def generate_clips(analyzed_videos: List[dict]) -> List[dict]:
    """Gera cortes finais com thumbnails"""
    clips = []
    
    for video in analyzed_videos:
        for i, moment in enumerate(video['moments']):
            # Determinar duração (30, 45 ou 60s baseado no conteúdo)
            duration = determine_optimal_duration(moment)
            
            # Cortar vídeo
            cutter = VideoCutter()
            clip_path = cutter.cut_clip(
                video['video_data']['local_path'],
                moment.start_time,
                duration,
                f"{video['video_id']}_clip_{i}"
            )
            
            # Gerar thumbnail
            thumb_gen = ThumbnailGenerator(BRAND_CONFIG)
            thumb_path = thumb_gen.generate(
                clip_path,
                video['semantic']['moments'][i]['suggested_title'],
                video['semantic']['moments'][i]['keywords']
            )
            
            # Adicionar intro com thumbnail
            final_path = cutter.add_intro_overlay(clip_path, thumb_path)
            
            # Gerar metadados
            meta_gen = MetadataGenerator()
            metadata = meta_gen.generate_viral_metadata(
                moment.transcript_segment,
                video['video_data']['title'],
                video['video_data']['channel'],
                NICHE,
                video['semantic']['moments'][i]['keywords']
            )
            
            clips.append({
                'video_path': final_path,
                'thumbnail_path': thumb_path,
                'metadata': metadata,
                'source_video_id': video['video_id']
            })
            
    return clips

@celery.task
def schedule_publications(clips: List[dict]) -> List[str]:
    """Agenda publicações em horários otimizados"""
    publisher = YouTubePublisher(CREDENTIALS_PATH)
    published_ids = []
    
    # Horários otimizados para engajamento
    optimal_hours = [10, 14, 18, 21]  # Horários de pico
    
    base_time = datetime.now()
    
    for i, clip in enumerate(clips):
        # Distribuir publicações ao longo de dias
        publish_time = base_time + timedelta(
            days=i // 4,
            hours=optimal_hours[i % 4]
        )
        
        video_id = publisher.upload_video(
            clip['video_path'],
            clip['metadata']['title'],
            clip['metadata']['description'],
            clip['metadata']['tags'],
            clip['thumbnail_path'],
            scheduled_time=publish_time
        )
        
        published_ids.append(video_id)
        
        # Log para tracking
        log_publication({
            'youtube_id': video_id,
            'source_id': clip['source_video_id'],
            'scheduled_time': publish_time,
            'metadata': clip['metadata']
        })
        
    return published_ids
```

---

## Configuração e Deploy

### Estrutura do Projeto

```
viral-clips-automation/
├── config/
│   ├── settings.py
│   ├── brand_config.yaml
│   └── niches/
│       ├── games.yaml
│       └── humor.yaml
├── src/
│   ├── monitors/
│   ├── downloaders/
│   ├── analyzers/
│   ├── editors/
│   ├── thumbnails/
│   ├── publishers/
│   └── orchestrator/
├── workers/
│   └── celery_app.py
├── api/
│   └── main.py (FastAPI dashboard)
├── assets/
│   ├── fonts/
│   └── templates/
├── docker-compose.yml
└── requirements.txt
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    environment:
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@db:5432/viral_clips
    volumes:
      - ./data:/app/data
      - ./credentials:/app/credentials
    depends_on:
      - redis
      - db
      
  worker:
    build: .
    command: celery -A workers.celery_app worker -l info
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@db:5432/viral_clips
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
      - db
      
  scheduler:
    build: .
    command: celery -A workers.celery_app beat -l info
    depends_on:
      - redis
      
  redis:
    image: redis:7-alpine
    
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=viral_clips
    volumes:
      - pgdata:/var/lib/postgresql/data
      
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  pgdata:
  minio_data:
```

---

## Considerações Legais e Éticas

### ⚠️ Pontos Importantes

1. **Direitos Autorais**
   - Este sistema usa conteúdo de terceiros — verifique políticas de fair use
   - Sempre credite o criador original na descrição
   - Considere programa de parceria ou revenue share

2. **Termos de Serviço**
   - YouTube proíbe automação excessiva de uploads
   - Use delays entre ações para simular comportamento humano
   - Mantenha-se dentro dos limites de quota da API

3. **Monetização**
   - Canais de compilação têm restrições de monetização
   - Conteúdo reutilizado pode não ser elegível para ads

4. **Alternativa Ética**
   - Contate criadores para parcerias oficiais
   - Use sistema para seu próprio conteúdo original
   - Implemente como ferramenta de análise sem republicação

---

## Próximos Passos

Quer que eu detalhe algum módulo específico ou implemente alguma parte em código funcional? Posso:

1. Criar um **MVP funcional** de qualquer módulo
2. Detalhar a **configuração de APIs** (YouTube, Whisper)
3. Desenvolver o **dashboard de monitoramento**
4. Implementar **testes automatizados**
5. Criar **documentação de deploy**