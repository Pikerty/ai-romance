from flask import Flask, request, jsonify, render_template, Response, stream_with_context
import json
import os
import urllib.request
import urllib.error

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

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

# Free models, OpenAI-compatible. Keys are read from the environment only:
# Groq models need GROQ_API_KEY, OpenRouter models need OPENROUTER_API_KEY.
# Free-model catalogs rotate, so a model that returns 404/429 may have been
# retired or capped; pick another model in the UI in that case.
MODELS = {
    "groq-qwen": {
        "label": "Qwen 3.8 27B (Groq 免费)",
        "provider": "groq",
        "model": "qwen/qwen3.8-27b",
    },
    "groq-gpt-oss-120b": {
        "label": "GPT-OSS 120B (Groq 免费)",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    },
    "groq-gpt-oss-20b": {
        "label": "GPT-OSS 20B (Groq 免费)",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
    },
    "openrouter-gemma": {
        "label": "Gemma 4 31B (OpenRouter 免费)",
        "provider": "openrouter",
        "model": "google/gemma-4-31b-it:free",
    },
    "openrouter-nemotron": {
        "label": "Nemotron 3 120B (OpenRouter 免费)",
        "provider": "openrouter",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
    },
}

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
    },
}

DEFAULT_MODEL_KEY = "groq-qwen"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/models")
def list_models():
    return jsonify({
        "default": DEFAULT_MODEL_KEY,
        "models": [
            {"key": key, "label": info["label"], "provider": info["provider"]}
            for key, info in MODELS.items()
        ],
    })


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    persona_id = data.get("persona", "xiaoya")
    model_key = data.get("model", DEFAULT_MODEL_KEY)
    history = data.get("history", [])
    user_message = (data.get("message", "") or "").strip()
    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400
    if len(user_message) > 500:
        return jsonify({"error": "消息太长啦，请控制在500字以内～"}), 400
    persona = PERSONAS.get(persona_id, PERSONAS["xiaoya"])
    model_info = MODELS.get(model_key, MODELS[DEFAULT_MODEL_KEY])
    provider = PROVIDERS[model_info["provider"]]
    api_key = os.environ.get(provider["api_key_env"], "").strip()

    messages = [{"role": "system", "content": persona["prompt"]}]
    for m in history:
        if not isinstance(m, dict):
            continue
        role = "user" if m.get("role") == "user" else "assistant"
        content = m.get("content", "")
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    def generate():
        if not api_key:
            yield f"[错误：该模型需要 {provider['api_key_env']}，请在 Render 环境变量里填写后重新部署]"
            return
        payload = {
            "model": model_info["model"],
            "messages": messages,
            "stream": True,
            "temperature": 0.9,
            "max_tokens": 400,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if model_info["provider"] == "openrouter":
            headers["HTTP-Referer"] = "https://ai-romance.onrender.com"
            headers["X-Title"] = "AI Romance"
        req = urllib.request.Request(
            provider["base_url"] + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8", "ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    chunk_text = line[5:].strip()
                    if chunk_text == "[DONE]":
                        break
                    try:
                        chunk = json.loads(chunk_text)
                    except ValueError:
                        continue
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8", "ignore")[:300]
            except Exception:
                detail = ""
            yield f"[错误：{e.code} {detail}]"
        except Exception as e:
            yield f"[错误：{str(e)}]"

    return Response(stream_with_context(generate()), content_type="text/plain; charset=utf-8")


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, port=5000)
