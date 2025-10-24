from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from vosk import Model, KaldiRecognizer
from openai import OpenAI
from pydub import AudioSegment, effects
from pydub.utils import which, mediainfo
import wave
import json
import os
import logging

# ============================================
# ⚙️ Import Config and Tools
# ============================================
from config import (
    OLLAMA_URL,
    OLLAMA_MODEL,
    VOSK_MODEL_PATH,
    DEBUG_MODE
)
from tools.logic_tool import call_engineering_tool


# ============================================
# 🧩 App Setup
# ============================================
app = Flask(__name__)
CORS(app)

# Logging setup
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Audio setup
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

# LLM client (Ollama)
client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")
MODEL = OLLAMA_MODEL

# Vosk speech model
vosk_model = Model(VOSK_MODEL_PATH)


# ============================================
# 💾 Chat Memory
# ============================================
chat_history = [
    {"role": "system", "content": "You are a helpful engineering assistant."}
]


# ============================================
# 🧠 Routes
# ============================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Handles text chat requests with persistent memory and tool calls"""
    global chat_history
    user_message = request.json.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "⚠️ Please say or type something."})

    # 🧠 1. Try to call the scientific/engineering tool
    tool_reply = call_engineering_tool(user_message)
    if tool_reply:
        log.info("🧰 Tool used for: %s", user_message)
        return jsonify({"reply": tool_reply})

    # 🧩 2. Otherwise, use the local Ollama model
    chat_history.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(model=MODEL, messages=chat_history)
    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})

    log.info("💬 LLM reply: %s", reply)
    return jsonify({"reply": reply})


@app.route("/voice", methods=["POST"])
def voice():
    """Handles voice input (WebM → WAV → text)"""
    if "audio" not in request.files:
        return jsonify({"error": "No audio uploaded"}), 400

    audio_file = request.files["audio"]
    temp_webm = "temp.webm"
    temp_wav = "temp.wav"
    audio_file.save(temp_webm)

    try:
        info = mediainfo(temp_webm)
        log.info("🎤 Incoming audio info: %s", info)

        # Convert & normalize
        sound = AudioSegment.from_file(temp_webm, format="webm")
        sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        sound = effects.normalize(sound)
        sound.export(temp_wav, format="wav")

        # Recognize speech
        wf = wave.open(temp_wav, "rb")
        rec = KaldiRecognizer(vosk_model, wf.getframerate())
        rec.SetWords(True)
        text = ""

        while True:
            data = wf.readframes(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text += " " + result.get("text", "")

        final = json.loads(rec.FinalResult()).get("text", "")
        text = (text + " " + final).strip()
        wf.close()

        log.info("🎧 Recognized text: %s", text or "[none]")

    except Exception as e:
        log.error("❌ Audio processing failed: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        for f in (temp_webm, temp_wav):
            if os.path.exists(f):
                os.remove(f)

    return jsonify({"text": text})


@app.route("/clear", methods=["POST"])
def clear_chat():
    """Clears chat memory"""
    global chat_history
    chat_history = [
        {"role": "system", "content": "You are a helpful engineering assistant."}
    ]
    log.info("🧹 Chat memory cleared.")
    return jsonify({"status": "cleared"})


# ============================================
# 🚀 Run App
# ============================================
if __name__ == "__main__":
    app.run(debug=DEBUG_MODE)
