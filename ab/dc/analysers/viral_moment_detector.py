# analyzers/viral_moment_detector.py
from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class MomentScore:
    start_time: float
    end_time: float
    audio_energy: float  # Picos de áudio/reações
    scene_changes: int  # Mudanças visuais
    speech_density: float  # Quantidade de fala
    keyword_hits: int  # Palavras-chave virais
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