from flask import Blueprint, jsonify, abort, request
import json
import os
from Modules.jwt_utils import allowed_users
frontend_site = Blueprint("frontend", __name__)

# Citește camerele din JSON la pornirea serverului
CAMERE_FILE = os.path.join("Modules", "camere.json")
with open(CAMERE_FILE, "r") as f:
    camere_data = json.load(f)["camere"]

# Dicționar pentru acces rapid după id
camere_dict = {c["id"]: c for c in camere_data}

# ========================
# Endpoint pentru lista camere
# ========================
@frontend_site.route("/lista_camere", methods=["GET"])
def get_list():
    camere_scurte = []
    for c in camere_data:
        cam = c.copy()
        cam.pop("camereDisponibile", None)
        camere_scurte.append(cam)
    return jsonify(camere_scurte)


# ========================
# Endpoint pentru detalii camera
# ========================
@frontend_site.route("/detalii_camera/<string:id>", methods=["GET"])
def get_camera(id):
    key = id.lower()
    if key not in camere_dict:
        abort(404, description=f"Camera cu id '{id}' nu a fost găsită")
    return jsonify(camere_dict[key])

# ========================
# Endpoint pentru rezervare cameră
# ========================
@frontend_site.route("/rezerva_camera", methods=["POST"])
@allowed_users(["Client","Angajat", "Administrator"])
def rezerva_camera():
    data = request.json
    camera_tip = data.get("camera_id")
    camera_id = data.get("camera_disponibila_id")

    if not camera_tip or not camera_id:
        abort(400, description="Trebuie să specifici 'camera_id' și 'camera_disponibila_id'")

    if camera_tip not in camere_dict:
        abort(404, description=f"Camera tip '{camera_tip}' nu a fost găsită")

    camere_disponibile = camere_dict[camera_tip]["camereDisponibile"]

    # 🔍 Căutăm camera specifică
    for cam in camere_disponibile:
        if cam["id"] == camera_id:
            if not cam["libera"]:
                abort(400, description=f"Camera {camera_id} este deja rezervată")

            # ✅ Marcăm ca rezervată
            cam["libera"] = False

            # 🔒 Salvăm modificările în fișierul JSON
            try:
                with open(CAMERE_FILE, "w") as f:
                    json.dump({"camere": camere_data}, f, indent=2)
            except Exception as e:
                abort(500, description=f"Eroare la salvarea fișierului: {e}")

            return jsonify({
                "status": "succes",
                "camera_id": camera_id,
                "camera_tip": camera_tip,
                "mesaj": f"Camera {camera_id} din tipul {camera_tip} a fost rezervată cu succes."
            })

    abort(404, description=f"Camera disponibilă '{camera_id}' nu a fost găsită")

CONTACT_FILE = os.path.join("Modules", "contact_messages.json")

@frontend_site.route("/contact", methods=["POST"])
def contact():
    data = request.json
    if not data or "name" not in data or "email" not in data or "message" not in data:
        abort(400, description="Date invalide")

    # Creează fișierul dacă nu există
    if not os.path.exists(CONTACT_FILE):
        with open(CONTACT_FILE, "w") as f:
            json.dump([], f)

    # Citește mesajele existente
    with open(CONTACT_FILE, "r") as f:
        try:
            msgs = json.load(f)
        except json.JSONDecodeError:
            msgs = []

    # Adaugă mesajul nou
    msgs.append({
        "name": data["name"],
        "email": data["email"],
        "message": data["message"],
        "date": data.get("date")
    })

    # Salvează înapoi
    with open(CONTACT_FILE, "w") as f:
        json.dump(msgs, f, indent=2)

    return jsonify({"status": "success"})