from flask import Flask, request, jsonify, render_template, Response, stream_with_context
import anthropic
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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
