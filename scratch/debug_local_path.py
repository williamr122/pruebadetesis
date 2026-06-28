import os
import sys

sys.path.append(os.getcwd())

from backend.nlp.local_provider import _temas_path, _load_temas

print("getcwd:", os.getcwd())
print("_temas_path returned:", _temas_path())
print("File exists at _temas_path:", os.path.exists(_temas_path()))
print("Loaded temas content keys:", _load_temas().keys())
print("Unidades length:", len(_load_temas().get("Unidades", [])))
