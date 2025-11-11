from flask import Blueprint, request, jsonify, send_file
import csv
import io
import json
from pydantic import ValidationError
from Modules.misc import TABLE_SCHEMAS,SENSITIVE_FIELDS, get_dto_class
from Modules.jwt_utils import allowed_users

CSV_IO = Blueprint("CSV_IO", __name__)

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


# =============================================================================
# ✅ IMPORT CSV — APPEND în JSON
# =============================================================================
@CSV_IO.route("/<table_name>", methods=["POST"])
@allowed_users(["Angajat", "Administrator"])
def import_csv(table_name):
    table_name = table_name.lower()

    if table_name not in TABLE_SCHEMAS:
        return jsonify({"eroare": "Tabelul specificat nu există."}), 404

    full_match = request.form.get("full_match", "false").lower() == "true"

    # validare existență fișier
    if "file" not in request.files:
        return jsonify({"eroare": "Nu a fost trimis niciun fișier."}), 400

    file = request.files["file"]

    # ✅ validare extensie
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"eroare": "Fișier invalid. Se acceptă doar fișiere .csv."}), 400

    # ✅ validare mărime fișier
    file.seek(0, 2)  # du-te la final
    size = file.tell()
    file.seek(0)

    if size > MAX_FILE_SIZE:
        return jsonify({"eroare": "Fișierul este prea mare. Maxim 2MB este permis."}), 400

    # ✅ validare MIME
    if file.mimetype not in ["text/csv", "application/vnd.ms-excel"]:
        return jsonify({"eroare": "Tip de fișier invalid. Tipul MIME trebuie să fie text/csv."}), 400

    # ✅ citire CSV
    try:
        content = file.read().decode("utf-8")
    except:
        return jsonify({"eroare": "Fișierul CSV nu a putut fi decodat. Folosiți UTF-8."}), 400

    stream = io.StringIO(content)
    reader = csv.DictReader(stream)

    expected_fields = list(TABLE_SCHEMAS[table_name].keys())
    dto_class = get_dto_class(table_name)

    # ✅ validare structură CSV
    missing_fields = [f for f in expected_fields if f not in reader.fieldnames]
    extra_fields = [f for f in reader.fieldnames if f not in expected_fields]

    # Dacă full_match este True, verificăm că toate coloanele sunt exact cele așteptate
    if full_match:
        if missing_fields or extra_fields:
            return jsonify({
                "eroare": "Structura CSV nu corespunde 100% cu tabela.",
                "coloane_asteptate": expected_fields,
                "coloane_primite": reader.fieldnames,
                "coloane_lipsa": missing_fields,
                "coloane_in_plus": extra_fields
            }), 400

    # În continuare, dacă full_match este False, putem permite mici diferențe

    total = 0
    reusite = 0
    esecuri = 0
    erori = []
    importate = []

    # ✅ citește datele existente
    json_path = f"Prototip/{table_name}.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)[table_name]
    except:
        db_data = []  # dacă încă nu există, îl creăm

    # ✅ procesare rânduri CSV
    for row in reader:
        total += 1
        try:
            # Completează câmpurile lipsă cu valorile implicite din schema
            for key, default_value in TABLE_SCHEMAS[table_name].items():
                if key not in row or row[key] == "":
                    row[key] = default_value

            valid = dto_class(**row)
            obj = valid.dict()
            importate.append(obj)
            db_data.append(obj)
            reusite += 1
        except ValidationError as e:
            esecuri += 1
            erori.append({
                "rand": total,
                "date_initiale": row,
                "erori": [err["msg"] for err in e.errors()]
            })

    # ✅ salvare în JSON (APPEND — adăugăm fără să ștergem ce era)
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({table_name: db_data}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return jsonify({"eroare": f"Eroare la salvarea în JSON: {str(e)}"}), 500

    return jsonify({
        "totalRanduri": total,
        "reusite": reusite,
        "esecuri": esecuri,
        "importate": importate,
        "erori": erori
    })
# =============================================================================
# ✅ EXPORT CSV
# =============================================================================
@CSV_IO.route("/<table_name>", methods=["GET"])
@allowed_users(["Angajat", "Administrator"])
def export_csv(table_name):
    table_name = table_name.lower()

    if table_name not in TABLE_SCHEMAS:
        return jsonify({"eroare": "Tabelul specificat nu există."}), 404

    json_path = f"Prototip/{table_name}.json"

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)[table_name]
    except FileNotFoundError:
        return jsonify({"eroare": f"Fișierul {json_path} nu există."}), 404
    except json.JSONDecodeError:
        return jsonify({"eroare": "Fișierul JSON este corupt sau invalid."}), 500

    # Filtrarea câmpurilor sensibile pentru tabelul curent
    sensitive_fields = SENSITIVE_FIELDS.get(table_name, [])
    filtered_data = []

    for item in data:
        # Excludem câmpurile sensibile
        filtered_item = {key: value for key, value in item.items() if key not in sensitive_fields}
        filtered_data.append(filtered_item)

    output = io.StringIO()
    fieldnames = [key for key in filtered_data[0].keys()]  # Extragem din datele filtrate
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for item in filtered_data:
        writer.writerow(item)

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{table_name}.csv"
    )