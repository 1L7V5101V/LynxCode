"""Compare two trace files."""
import json, sys

def analyze_trace(path, label):
    events = [json.loads(l) for l in open(path, encoding="utf-8")]
    tools = {}
    retries = 0
    errors = 0
    model_err = None
    max_ms = 0
    for e in events:
        t = e.get("event", "")
        if t == "tool_executed":
            p = e.get("payload", e)
            name = p.get("name", "?")
            tools[name] = tools.get(name, 0) + 1
        if t == "model_parsed":
            if e.get("payload", {}).get("kind") == "retry":
                retries += 1
        if t == "model_error":
            err = e.get("error", {})
            model_err = f"code={err.get('code')} duration={e.get('duration_ms')}ms"
        ms = e.get("duration_ms", 0)
        if isinstance(ms, (int, float)):
            max_ms = max(max_ms, ms)
    print(f"  {label}:")
    print(f"    events={len(events)} tools={sum(tools.values())} retries={retries}")
    if model_err:
        print(f"    model_error: {model_err}")
    print(f"    max_call_ms: {max_ms}")
    for k, v in sorted(tools.items(), key=lambda x: -x[1]):
        print(f"      {k}: {v}")
    print()

if len(sys.argv) >= 3:
    analyze_trace(sys.argv[1], sys.argv[2])
if len(sys.argv) >= 4:
    analyze_trace(sys.argv[3], sys.argv[4])
