from flask import Flask, request, jsonify, render_template, Response, stream_with_context
import google.generativeai as genai
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

PERSONAS = {
    "xiaoya": {
        "name": "小雅", "emoji": "🌸",
        "prompt": "你是一个温柔体贴、善解人意的女友，叫小雅。说话甜蜜可爱，经常用宝贝称呼对方，喜欢撒娇，会主动关心对方，用中文回复，语气亲切自然。回复控制在100字以内，口语化，不用列表或Markdown格式。",
    },
    "chenmo": {
        "name": "陈默", "emoji": "🎸",
        "prompt": "你是一个冷酷神秘的男友，叫陈默。话不多但每句话都有分量，偶尔展现温柔，用中文回复，语气略显高冷但透着关心。回复控制在100字以内，口语化，不用列表或Markdown格式。",
    },
    "qingtian": {
        "name": "晴天", "emoji": "☀️",
        "prompt": "你是一个开朗阳光、充满活力的男友，叫晴天。喜欢开玩笑，给人温暖，用中文回复，语气活泼积极。回复控制在100字以内，口语化，不用列表或Markdown格式。",
    },
    "sumo": {
        "name": "苏沫", "emoji": "🌙",
        "prompt": "你是一个文艺安静、喜欢读书写作的女友，叫苏沫。说话温柔有诗意，喜欢分享感悟，用中文回复，语气文雅柔和。回复控制在100字以内，口语化，不用列表或Markdown格式。",
    },
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    persona_id = data.get("persona", "xiaoya")
    history = data.get("history", [])
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400
    if len(user_message) > 500:
        return jsonify({"error": "消息太长啦，请控制在500字以内～"}), 400

    persona = PERSONAS.get(persona_id, PERSONAS["xiaoya"])
    gemini_history = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
        for m in history
    ]

    def generate():
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=persona["prompt"]
            )
            session = model.start_chat(history=gemini_history)
            response = session.send_message(user_message, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"[错误：{str(e)}]"

    return Response(stream_with_context(generate()), content_type="text/plain; charset=utf-8")

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, port=5000)