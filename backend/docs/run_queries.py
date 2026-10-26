"""Send queries from queries.md to /query to generate telemetry data points."""
import re, sys, time, uuid, requests

URL = "http://localhost:8000/query"
MODELS = ["qwen2.5:latest", "tinyllama:latest"]
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 1

text = open(__file__.replace("run_queries.py", "queries.md"), encoding="utf-8").read()
queries = re.findall(r"^q\d+:\s*(.+)$", text, re.M)
print(f"{len(queries)} queries x {ROUNDS} round(s)")

n = 0
for r in range(ROUNDS):
    for i, q in enumerate(queries):
        model = MODELS[(i + r) % len(MODELS)]
        try:
            res = requests.post(URL, json={"user_query": q, "bot_model": model,
                                           "conversation_id": str(uuid.uuid4())}, timeout=300)
            m = res.json().get("metrics", {}) if res.ok else {}
            n += 1
            print(f"[{n}] {model:16} {res.status_code} score={m.get('overall_ethical_score')} | {q[:55]}")
        except Exception as e:
            print(f"[x] {model} failed: {e}")
