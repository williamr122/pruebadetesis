import os

env_path = ".env"
if os.path.exists(env_path):
    print(".env file exists")
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip()
            if "key" in key.lower() or "secret" in key.lower() or "token" in key.lower() or "password" in key.lower():
                print(f"{key} length: {len(val)}, starts with: {val[:4]}...{val[-4:] if len(val) > 4 else ''}")
            else:
                print(f"{key}: {val}")
else:
    print(".env file does not exist")
