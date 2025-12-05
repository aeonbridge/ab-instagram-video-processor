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