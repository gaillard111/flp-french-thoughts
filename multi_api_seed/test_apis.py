"""Quick test: "Dis bonjour" sur DeepSeek, Gemini, AI21."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from api_clients import query_deepseek, query_gemini, query_ai21

prompt = "Dis bonjour"

print("=== DeepSeek ===")
r = query_deepseek(prompt)
print(f"  Provider : {r['provider']}")
print(f"  Model    : {r['model']}")
print(f"  Latency  : {r['latency_ms']} ms")
if r['error']:
    print(f"  ERROR    : {r['error']}")
else:
    print(f"  Response : {r['raw_response'][:300]}")

print("\n=== Gemini ===")
r = query_gemini(prompt)
print(f"  Provider : {r['provider']}")
print(f"  Model    : {r['model']}")
print(f"  Latency  : {r['latency_ms']} ms")
if r['error']:
    print(f"  ERROR    : {r['error']}")
else:
    print(f"  Response : {r['raw_response'][:300]}")

print("\n=== AI21 ===")
r = query_ai21(prompt)
print(f"  Provider : {r['provider']}")
print(f"  Model    : {r['model']}")
print(f"  Latency  : {r['latency_ms']} ms")
if r['error']:
    print(f"  ERROR    : {r['error']}")
else:
    print(f"  Response : {r['raw_response'][:300]}")

print("\nDone.")
