"""Routes to serve course resources dynamically from backend/resources/."""

from __future__ import annotations

import os
from pathlib import Path
from flask import Blueprint, send_from_directory, abort, jsonify

resources_bp = Blueprint("resources", __name__)

RESOURCES_DIR = Path(__file__).resolve().parents[2] / "backend" / "resources"

@resources_bp.route("/resources/<path:filename>", methods=["GET"])
def serve_resource(filename: str):
    """Serve a resource file securely from backend/resources/."""
    try:
        # Prevent path traversal attacks
        root = RESOURCES_DIR.resolve()
        # Resolve target path safely
        target = (root / filename).resolve()
        
        # Check that the target is within the root directory
        if root not in target.parents and target != root:
            return jsonify({"ok": False, "error": "Acceso denegado"}), 403
            
        if not target.exists() or not target.is_file():
            abort(404)
            
        # Serve the file from directory
        return send_from_directory(str(root), filename)
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Error al servir recurso: {str(exc)}"}), 500
