# Quick Start - AI Metadata Generator

Get started with AI-powered metadata generation in 5 minutes.

## Step 1: Install Dependencies

```bash
pip install agno openai
```

## Step 2: Set API Key

Get your OpenAI API key from: https://platform.openai.com/api-keys

```bash
export OPENAI_API_KEY='sk-...'
```

Or add to `.env` file:
```bash
OPENAI_API_KEY=sk-...
```

## Step 3: Generate Metadata

### Single File

```bash
cd ab/dc/publishers/agents

# Generate metadata
python cli_metadata_agent.py generate ../../processed_videos/RusBe_8arLQ/RusBe_8arLQ_0001_40s_score_137_original_en.md

# Result: RusBe_8arLQ_0001_40s_score_137_original_en_metadata.json
```

### Batch Processing

```bash
# Generate for all transcripts in directory
python cli_metadata_agent.py batch ../../processed_videos/RusBe_8arLQ/

# Results: Multiple *_metadata.json files created
```

## Step 4: Use Metadata

### View Generated Metadata

```bash
cat RusBe_8arLQ_0001_40s_score_137_original_en_metadata.json | jq
```

### Publish with Metadata

```bash
cd ../  # Back to publishers directory

# Extract metadata fields
METADATA="../../processed_videos/RusBe_8arLQ/RusBe_8arLQ_0001_40s_score_137_original_en_metadata.json"
VIDEO="../../processed_videos/RusBe_8arLQ/RusBe_8arLQ_0001_40s_score_137_original_en.mp4"

# Publish to YouTube
python cli_publisher.py upload "$VIDEO" \
  --title "$(jq -r .title $METADATA)" \
  --description "$(jq -r .description $METADATA)" \
  --tags "$(jq -r '.tags | join(",")' $METADATA)" \
  --category "$(jq -r .category $METADATA)"
```

## Complete Workflow Example

```bash
#!/bin/bash

# Set video ID
VIDEO_ID="RusBe_8arLQ"

# 1. Clean subtitles to markdown
cd ab/dc/downloaders
python cli_subtitle_cleaner.py batch processed_videos/$VIDEO_ID/

# 2. Generate AI metadata
cd ../publishers/agents
python cli_metadata_agent.py batch ../../processed_videos/$VIDEO_ID/ --platform youtube

# 3. Publish all videos
cd ..
for metadata in ../../processed_videos/$VIDEO_ID/*_metadata.json; do
    video="${metadata%_metadata.json}.mp4"

    if [ -f "$video" ]; then
        python cli_publisher.py upload "$video" \
            --title "$(jq -r .title $metadata)" \
            --description "$(jq -r .description $metadata)" \
            --tags "$(jq -r '.tags | join(",")' $metadata)" \
            --category "$(jq -r .category $metadata)" \
            --privacy public

        echo "✓ Published: $(jq -r .title $metadata)"
    fi
done
```

## Cost-Effective Tips

### Use GPT-3.5 for Testing

```bash
# Much cheaper for development
python cli_metadata_agent.py generate transcript.md --model gpt-3.5-turbo
```

### Batch Processing

```bash
# Process multiple files in one go
python cli_metadata_agent.py batch videos/ --model gpt-3.5-turbo
```

### Estimated Costs

- **GPT-4 Turbo**: $0.01-0.03 per video
- **GPT-3.5 Turbo**: $0.001-0.005 per video

For 10 videos:
- GPT-4: ~$0.30
- GPT-3.5: ~$0.05

## Examples by Platform

### YouTube

```bash
python cli_metadata_agent.py generate transcript.md --platform youtube
```

### TikTok

```bash
python cli_metadata_agent.py generate transcript.md --platform tiktok
```

### YouTube Shorts

```bash
python cli_metadata_agent.py generate transcript.md --platform shorts
```

### Instagram Reels

```bash
python cli_metadata_agent.py generate transcript.md --platform instagram
```

## Validation

```bash
# Validate generated metadata
python cli_metadata_agent.py validate metadata.json
```

## Troubleshooting

### "Agno not installed"
```bash
pip install agno openai
```

### "API key not found"
```bash
export OPENAI_API_KEY='sk-...'
```

### "Rate limit exceeded"
- Wait a few minutes
- Reduce batch size
- Upgrade OpenAI plan

## Next Steps

1. Read full documentation: `README.md`
2. See more examples: `python cli_metadata_agent.py examples`
3. Customize for your niche: Edit `metadata_generator_agent.py`

---

**Need help?** Check the full README.md for detailed documentation.
