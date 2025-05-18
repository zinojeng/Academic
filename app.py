import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import openai
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Recording(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    transcript = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=False)


db.create_all()


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using OpenAI's latest transcription model."""
    openai.api_key = os.getenv('OPENAI_API_KEY')
    with open(audio_path, 'rb') as audio_file:
        resp = openai.Audio.transcribe('gpt-4o', audio_file)
    return resp['text']


def generate_notes(text: str) -> str:
    """Generate detailed notes from transcript text."""
    openai.api_key = os.getenv('OPENAI_API_KEY')
    prompt = (
        "Please produce detailed study notes with hierarchical headings, bulleted "
        "analysis, bold and underline where appropriate based on the following t"
        "ranscript. Conclude with a concise summary of the key points.\n\n" + text
    )
    messages = [{"role": "user", "content": prompt}]
    completion = openai.ChatCompletion.create(model='gpt-4', messages=messages)
    return completion.choices[0].message['content']


def ask_question(rec: 'Recording', question: str) -> str:
    openai.api_key = os.getenv('OPENAI_API_KEY')
    context = f"Transcript:\n{rec.transcript}\n\nNotes:\n{rec.notes}"
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": question},
    ]
    completion = openai.ChatCompletion.create(model='gpt-4', messages=messages)
    return completion.choices[0].message['content']


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        audio = request.files.get('audio')
        if not audio:
            flash('Please upload an audio file.')
            return redirect(request.url)

        filename = secure_filename(audio.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        audio.save(save_path)

        transcript = transcribe_audio(save_path)
        notes = generate_notes(transcript)

        rec = Recording(filename=filename, transcript=transcript, notes=notes)
        db.session.add(rec)
        db.session.commit()
        flash('File processed successfully.')
        return redirect(url_for('recordings'))

    return render_template('index.html')


@app.route('/recordings')
def recordings():
    recs = Recording.query.order_by(Recording.id.desc()).all()
    return render_template('recordings.html', recordings=recs)


@app.route('/recordings/<int:rec_id>', methods=['GET', 'POST'])
def recording_detail(rec_id):
    rec = Recording.query.get_or_404(rec_id)
    answer = None
    if request.method == 'POST':
        question = request.form.get('question')
        if question:
            answer = ask_question(rec, question)
    return render_template('recording_detail.html', rec=rec, answer=answer)


if __name__ == '__main__':
    app.run(debug=True)

