"""
Main entry point for the Arabic Real Estate AI Agent.
Sets up the Gradio interface and initializes the agent.
"""
import os
import gradio as gr
import logging
from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS

from config import (
    UI_TITLE,
    UI_DESCRIPTION,
    UI_WELCOME_MESSAGE,
    GRADIO_THEME,
    DEBUG,
    ConversationPhase
)
from agent import RealEstateAgent
from phase_manager import PhaseManager
from history import ConversationHistory

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Initialize components ===
phase_manager = PhaseManager()
conversation_history = ConversationHistory()

# === Initialize the real estate agent ===
agent = RealEstateAgent(
    phase_manager=phase_manager,
    conversation_history=conversation_history,
    dialect="Egyptian"
)

# === Gradio UI Setup ===
with gr.Blocks(theme=GRADIO_THEME, css="""
    .gradio-container {direction: rtl;}
    .chat-message p {text-align: right;}
    .chat-message h4 {text-align: right;}
""") as demo:
    gr.Markdown(f"# {UI_TITLE}")
    gr.Markdown(UI_DESCRIPTION)

    chatbot = gr.Chatbot(
        height=600,
        show_copy_button=True,
        avatar_images=(None, "https://img.icons8.com/color/48/000000/property.png"),
        type="messages"
    )

    msg = gr.Textbox(
        placeholder="اكتب رسالتك هنا...",
        container=False,
        scale=7,
    )

    with gr.Row():
        submit = gr.Button("إرسال", variant="primary", scale=1)
        clear = gr.Button("مسح المحادثة", variant="secondary", scale=1)

    state = gr.State([])

    def init_chat():
        return [{"role": "assistant", "content": UI_WELCOME_MESSAGE}], []

    def respond(message, history, state):
        if not message.strip():
            return history, state

        history.append({"role": "user", "content": message})
        response, new_state = agent.process_message(message, state)
        history.append({"role": "assistant", "content": response})

        return history, new_state

    msg.submit(respond, [msg, chatbot, state], [chatbot, state]).then(lambda: "", None, msg)
    submit.click(respond, [msg, chatbot, state], [chatbot, state]).then(lambda: "", None, msg)
    clear.click(init_chat, None, [chatbot, state])
    demo.load(init_chat, None, [chatbot, state])

# === Flask App Setup ===
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    if request.is_json:
        data = request.json
        message = data.get('message', '')
        state = data.get('state', [])
    else:
        message = request.form.get('message', '')
        state = []

    if message:
        response, new_state = agent.process_message(message, state)
    else:
        response = "عذراً، لم أفهم رسالتك. هل يمكنك إعادة صياغتها؟"
        new_state = state

    return jsonify({
        'response': response,
        'state': new_state
    })

@app.route('/api/dialects', methods=['GET'])
def get_dialects():
    return jsonify({
        'dialects': ["egyptian", "khaliji", "levantine", "msa"],
        'default': "egyptian"
    })

@app.route('/gradio')
def gradio_interface():
    return redirect('/')

# === Run App ===
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=5000,
        share=True,
        debug=DEBUG
    )
