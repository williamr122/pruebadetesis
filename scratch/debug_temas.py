import os
import sys

sys.path.append(os.getcwd())

import backend.services.temas_service
backend.services.temas_service.cargar_temas(force=True)

from backend.nlp.local_provider import responder_local_temas, _build_index, _score, _nivel_ok

print("Testing responder_local_temas directly:")
res = responder_local_temas(
    pregunta_user="ayúdame con algo sobre qué es encapsulamiento",
    nivel="Básico",
    modo_interaccion="normal"
)
print("Result:")
print(res)

print("\nDetail of idx and scoring:")
idx = _build_index()
print("Idx length:", len(idx))
for it in idx:
    if "encapsulamiento" in it.get("tema", "").lower():
        print("Item:", it)
        print("Level ok:", _nivel_ok("Básico", it.get("nivel", "")))
        print("Score:", _score("ayudame con algo sobre que es encapsulamiento", it))
