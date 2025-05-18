# Academic

This project contains tools for academic research assistance. In addition to the
PubMed summarizer, it now includes a simple web application for transcribing aud
io files and generating structured notes with OpenAI models.

## Audio Notes Web App

1. Upload an audio file through the web interface.
2. The file is transcribed using OpenAI's latest model (`gpt-4o`).
3. Detailed notes are produced with hierarchical sections and a summary.
4. All recordings, transcripts and notes are stored and can be reviewed online.
5. Users may ask questions about each recording, answered by GPT based on the t
ranscript and notes.

### Running the App

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your-key
python app.py
```

Open your browser at `http://localhost:5000`.

Writing by Doctor Tseng from Tungs' Taichung Metroharbor Hospital.
