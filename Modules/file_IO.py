from flask import Blueprint, request, jsonify, send_file
import csv
import io
from pydantic import ValidationError
from Modules.DTOs import get_dto_class
from Modules.misc import SENSITIVE_FIELDS
from Modules.jwt_utils import allowed_users
from Modules.DBConn import db
from Modules.SQLModels import MODEL_MAP

CSV_IO = Blueprint("CSV_IO", __name__)
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# =============================================================================
# ✅ IMPORT CSV — salvează în baza de date
# =============================================================================
@CSV_IO.route("/<table_name>", methods=["POST"])
@allowed_users(["Angajat", "Administrator"])
def import_csv(table_name):
    table_name = table_name.lower()

    if table_name not in MODEL_MAP:
        return jsonify({"eroare": "Nu există un model SQL pentru acest tabel."}), 500

    Model = MODEL_MAP[table_name]
    dto_class = get_dto_class(table_name)

    full_match = request.form.get("full_match", "false").lower() == "true"

    # ----------------------------------------
    # 1. FIȘIER
    # ----------------------------------------
    if "file" not in request.files:
        return jsonify({"eroare": "Nu a fost trimis niciun fișier."}), 400

    file = request.files["file"]

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"eroare": "Fișierul trebuie să fie CSV."}), 400

    file.seek(0, 2)
    if file.tell() > MAX_FILE_SIZE:
        return jsonify({"eroare": "Fișier prea mare (max 2MB)."}), 400
    file.seek(0)

    try:
        content = file.read().decode("utf-8")
    except Exception:
        return jsonify({"eroare": "CSV trebuie să fie UTF-8."}), 400

    reader = csv.DictReader(io.StringIO(content))

    # Determinăm câmpurile așteptate: DTO dacă există, altfel coloanele SQLAlchemy
    if dto_class:
        expected_fields = dto_class.__fields__.keys()
    else:
        expected_fields = [col.name for col in Model.__table__.columns]

    if full_match:
        missing = [f for f in expected_fields if f not in reader.fieldnames]
        extra = [f for f in reader.fieldnames if f not in expected_fields]
        if missing or extra:
            return jsonify({"eroare": "Structura CSV nu corespunde.", "lipsesc": missing, "extra": extra}), 400

    # ----------------------------------------
    # 2. PROCESARE RÂNDURI
    # ----------------------------------------
    total, reusite, esecuri = 0, 0, 0
    erori, importate = [], []

    for row in reader:
        total += 1
        try:
            row.pop("id", None)  # DB generează automat ID

            # completăm câmpurile lipsă cu valori implicite (DTO dacă există)
            if dto_class:
                for key, field in dto_class.__fields__.items():
                    if key not in row or row[key] == "":
                        default = field.default if field.default is not None else None
                        row[key] = default

                # validare DTO
                valid = dto_class(**row)
                data = valid.dict()
                data.pop("id", None)
            else:
                data = row  # folosește direct datele din CSV pentru SQLAlchemy

            obj = Model(**data)
            db.session.add(obj)
            importate.append(data)
            reusite += 1

        except ValidationError as e:
            esecuri += 1
            erori.append({"rand": total, "date_initiale": row, "erori": [err["msg"] for err in e.errors()]})
        except Exception as e:
            esecuri += 1
            erori.append({"rand": total, "date_initiale": row, "erori": [str(e)]})

    # ----------------------------------------
    # 3. SALVARE ÎN BAZA DE DATE
    # ----------------------------------------
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"eroare": f"Eroare salvare DB: {str(e)}"}), 500

    return jsonify({
        "totalRanduri": total,
        "reusite": reusite,
        "esecuri": esecuri,
        "importate": importate,
        "erori": erori
    })


# =============================================================================
# ✅ EXPORT CSV — citește direct din baza de date
# =============================================================================
@CSV_IO.route("/<table_name>", methods=["GET"])
@allowed_users(["Client", "Angajat", "Administrator"])
def export_csv(table_name):
    table_name = table_name.lower()

    if table_name not in MODEL_MAP:
        return jsonify({"eroare": "Tabelul nu există sau nu are model SQL."}), 404

    Model = MODEL_MAP[table_name]
    sensitive_fields = SENSITIVE_FIELDS.get(table_name, [])

    try:
        data = Model.query.all()
    except Exception as e:
        return jsonify({"eroare": f"Eroare la interogare: {str(e)}"}), 500

    if not data:
        return jsonify({"eroare": "Tabelul este gol."}), 404

    rows = []
    for item in data:
        row = {col: getattr(item, col) for col in item.__table__.columns.keys() if col not in sensitive_fields}
        rows.append(row)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{table_name}.csv"
    )
