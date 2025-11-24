from flask import Blueprint, jsonify, abort, request
from Modules.jwt_utils import allowed_users
from Modules.SQLModels import db, Camera, CameraDisponibila, Feedback
from datetime import datetime

frontend_site = Blueprint("frontend", __name__)

# ========================
# List of camera types
# ========================
@frontend_site.route("/lista_camere", methods=["GET"])
def get_list():
    camere = Camera.query.all()
    print("DEBUG: camere query returned:", camere)  # ✅ print raw SQLAlchemy objects

    camere_scurte = [
        {
            "Id": c.Id,
            "Nume": c.Nume,
            "Pret": c.Pret,
            "Moneda": c.Moneda,
            "Imagine": c.Imagine,
            "Descriere": c.Descriere
        }
        for c in camere
    ]

    print("DEBUG: camere_scurte:", camere_scurte)  # ✅ print formatted list
    return jsonify(camere_scurte)


# ========================
# Detalii camera
# ========================
@frontend_site.route("/detalii_camera/<string:id>", methods=["GET"])
def get_camera(id):
    camera = Camera.query.filter_by(Id=id).first()
    print(f"DEBUG: query camera id={id} returned:", camera)

    if not camera:
        abort(404, description=f"Camera cu id '{id}' nu a fost găsită")

    camere_disp = [
        {"Id": cd.Id, "Libera": cd.Libera} for cd in camera.camere_disponibile
    ]
    print("DEBUG: camere disponibile:", camere_disp)

    camera_dict = {
        "Id": camera.Id,
        "Nume": camera.Nume,
        "Pret": camera.Pret,
        "Moneda": camera.Moneda,
        "Imagine": camera.Imagine,
        "Descriere": camera.Descriere,
        "camereDisponibile": camere_disp
    }

    print("DEBUG: final camera_dict:", camera_dict)
    return jsonify(camera_dict)


# ========================
# Rezervare cameră
# ========================
@frontend_site.route("/rezerva_camera", methods=["POST"])
@allowed_users(["Client", "Angajat", "Administrator"])
def rezerva_camera():
    data = request.json
    print("DEBUG: rezervare payload:", data)

    camera_tip = data.get("camera_id")
    camera_id = data.get("camera_disponibila_id")

    if not camera_tip or not camera_id:
        abort(400, description="Trebuie să specifici 'camera_id' și 'camera_disponibila_id'")

    cam_disp = CameraDisponibila.query.filter_by(Id=camera_id, CameraId=camera_tip).first()
    print(f"DEBUG: CameraDisponibila query returned: {cam_disp}")

    if not cam_disp:
        abort(404, description=f"Camera disponibilă '{camera_id}' nu a fost găsită")
    if not cam_disp.Libera:
        abort(400, description=f"Camera {camera_id} este deja rezervată")

    cam_disp.Libera = False
    db.session.commit()
    print(f"DEBUG: Camera {camera_id} marked as reserved")

    return jsonify({
        "status": "succes",
        "camera_id": camera_id,
        "camera_tip": camera_tip,
        "mesaj": f"Camera {camera_id} din tipul {camera_tip} a fost rezervată cu succes."
    })


# ========================
# Feedback/contact
# ========================
@frontend_site.route("/contact", methods=["POST"])
def contact():
    data = request.json
    print("DEBUG: contact payload:", data)

    if not data or "name" not in data or "email" not in data or "message" not in data:
        abort(400, description="Date invalide")

    date_sent = datetime.strptime(data.get("date"), "%d.%m.%Y, %H:%M:%S") if data.get("date") else datetime.utcnow()
    feedback = Feedback(
        Name=data["name"],
        Email=data["email"],
        Message=data["message"],
        DateSent=date_sent
    )

    db.session.add(feedback)
    db.session.commit()
    print("DEBUG: Feedback saved:", feedback)

    return jsonify({"status": "success"})
