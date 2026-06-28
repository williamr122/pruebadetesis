import urllib.request
import json
import subprocess

def call_api(payload):
    url = "http://localhost:5000/api/feedback"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            status = res.status
            body = res.read().decode("utf-8")
            return status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else e.reason

# Call with new payload format (rating, note)
print("Sending rating/note payload...")
status1, body1 = call_api({
    "rating": "up",
    "note": "Prueba de feedback con rating/note",
    "conversation_id": 999
})
print("Status:", status1)
print("Response:", body1)

# Call with compatible payload format (value, message)
print("\nSending value/message payload...")
status2, body2 = call_api({
    "value": "down",
    "message": "Prueba de feedback con value/message (compatibilidad)",
    "conversation_id": 999
})
print("Status:", status2)
print("Response:", body2)

# Copy check_db.py to container and run it to verify DB contents
print("\nVerifying database contents inside the Docker container:")
subprocess.run(["docker", "cp", "scratch/check_db.py", "yelia4ap_backend_flask:/app/check_db.py"])
res = subprocess.run(["docker", "exec", "yelia4ap_backend_flask", "python", "/app/check_db.py"], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)
