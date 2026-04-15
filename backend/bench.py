import time, json, urllib.request

def chat(q):
    body = json.dumps({"question": q, "llm_provider": "groq"}).encode()
    req  = urllib.request.Request(
        "http://127.0.0.1:8000/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as r:
        b = json.loads(r.read())
    ms = round((time.perf_counter() - t0) * 1000)
    return ms, b

tests = [
    ("FAQ  (what is roe)",    "what is roe"),
    ("FAQ  (what is ebitda)", "what is ebitda"),
    ("DATA (TCS cold)",       "tcs analysis"),
    ("DATA (TCS cached)",     "tcs analysis"),
    ("DATA (Infosys cold)",   "analyse Infosys"),
]

print("=" * 70)
print(f"{'Test':<28} {'ms':>6}  {'model':<28} {'conf':>6}  {'gate'}")
print("=" * 70)
for label, q in tests:
    try:
        t, b = chat(q)
        model  = str(b.get("model_used", "?"))[:28]
        conf   = b.get("confidence")
        conf_s = f"{conf:.0%}" if conf is not None else "--"
        gate   = b.get("failed_at") or b.get("gates_passed", ["?"])[-1]
        print(f"{label:<28} {t:>6}  {model:<28} {conf_s:>6}  {gate}")
    except Exception as e:
        print(f"{label:<28}  ERROR: {e}")
print("=" * 70)
