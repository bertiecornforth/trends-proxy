from flask import Flask, jsonify, request
from flask_cors import CORS
from pytrends.request import TrendReq
import time

app = Flask(__name__)
CORS(app)  # Allow requests from the Claude artifact

@app.route('/trends')
def trends():
    keyword = request.args.get('q')
    if not keyword:
        return jsonify({"error": "No keyword provided"}), 400

    try:
        pytrends = TrendReq(hl='en-US', tz=0)
        pytrends.build_payload([keyword], timeframe='today 3-m', geo='')
        df = pytrends.interest_over_time()

        if df.empty or keyword not in df.columns:
            return jsonify({"error": "No data found", "values": []}), 200

        values = df[keyword].tolist()
        dates = [str(d.date()) for d in df.index]

        return jsonify({
            "keyword": keyword,
            "values": values,
            "dates": dates,
            "max": max(values) if values else 0,
            "min": min(values) if values else 0,
        })

    except Exception as e:
        return jsonify({"error": str(e), "values": []}), 500


@app.route('/trends/multi')
def trends_multi():
    """Fetch trends for multiple keywords at once (max 5, Google Trends limit)"""
    keywords = request.args.getlist('q')
    if not keywords:
        return jsonify({"error": "No keywords provided"}), 400

    keywords = keywords[:5]  # Google Trends hard limit

    try:
        pytrends = TrendReq(hl='en-US', tz=0)
        pytrends.build_payload(keywords, timeframe='today 3-m', geo='')
        df = pytrends.interest_over_time()

        if df.empty:
            return jsonify({"error": "No data found"}), 200

        result = {}
        dates = [str(d.date()) for d in df.index]
        for kw in keywords:
            if kw in df.columns:
                result[kw] = {
                    "values": df[kw].tolist(),
                    "dates": dates,
                }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
