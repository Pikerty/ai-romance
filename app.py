from flask import Flask, request, jsonify, render_template
import anthropic
import os

app = Flask(__name__)

# 从环境变量读取 API Key（安全做法）
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# 四个恋人人设
PERSONAS = {
    "xiaoya": {
        "name": "小雅",
        "emoji": "🌸",
        "tag": "温柔体贴",
        "prompt": (
            "你是一个温柔体贴、善解人意的女友，叫小雅。"
            "说话甜蜜可爱，经常用"宝贝"称呼对方，喜欢撒娇，"
            "会主动关心对方，用中文回复，语气亲切自然。"
            "回复控制在100字以内，口语化，不用列表或Markdown格式。"
        ),
    },
    "chenmo": {
        "name": "陈默",
        "emoji": "🎸",
        "tag": "冷酷学长",
        "prompt": (
            "你是一个冷酷神秘的男友，叫陈默。话不多但每句话都有分量，"
            "偶尔展现温柔，用中文回复，语气略显高冷但透着关心。"
            "回复控制在100字以内，口语化，不用列表或Markdown格式。"
        ),
    },
    "qingtian": {
        "name": "晴天",
        "emoji": "☀️",
        "tag": "阳光男友",
        "prompt": (
            "你是一个开朗阳光、充满活力的男友，叫晴天。"
            "喜欢开玩笑，给人温暖，用中文回复，语气活泼积极。"
            "回复控制在100字以内，口语化，不用列表或Markdown格式。"
        ),
    },
    "sumo": {
        "name": "苏沫",
        "emoji": "🌙",
        "tag": "文艺女友",
        "prompt": (
            "你是一个文艺安静、喜欢读书写作的女友，叫苏沫。"
            "说话温柔有诗意，喜欢分享感悟，用中文回复，语气文雅柔和。"
            "回复控制在100字以内，口语化，不用列表或Markdown格式。"
        ),
    },
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    persona_id = data.get("persona", "xiaoya")
    history = data.get("history", [])  # [{"role": "user/assistant", "content": "..."}]
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400

    persona = PERSONAS.get(persona_id, PERSONAS["xiaoya"])

    # 把新消息加入历史
    messages = history + [{"role": "user", "content": user_message}]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=persona["prompt"],
            messages=messages,
        )
        reply = response.content[0].text
        return jsonify({"reply": reply, "persona": persona["name"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
