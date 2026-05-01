"""Quick test to verify API keys are working."""
import requests

# Test explain endpoint (tests Gemini key)
print("Testing /api/explain (Gemini API)...")
r = requests.post(
    "http://localhost:8000/api/explain",
    json={"filename": "test.py", "content": "def hello(): pass", "simple": False},
)
print(f"  Status: {r.status_code}")
data = r.json()
print(f"  Response: {data.get('status', 'error')}")
if "explanation" in data:
    print(f"  Explanation preview: {data['explanation'][:150]}...")
else:
    print(f"  Detail: {data.get('detail', 'unknown error')}")

# Test health
print("\nTesting /health...")
r2 = requests.get("http://localhost:8000/health")
print(f"  Status: {r2.json()}")
