from flask import Blueprint, jsonify, request
from Modules.jwt_utils import allowed_users
from Modules.SQLModels import MODEL_MAP, db
from sqlalchemy import and_, or_
from pydantic import ValidationError
from Modules.DTOs import DeleteDTO,UpdateDTO,get_dto_class
api = Blueprint("api", __name__)

def serialize_sql_row(row):
    """Convert SQLAlchemy row → dict"""
    return {col.name: getattr(row, col.name) for col in row.__table__.columns}

# GET /search
@api.route("/search", methods=["GET"])
@api.route("/search/<string:table>", methods=["GET"])
@allowed_users(["Angajat", "Administrator"])
def search_data(table=None):
    data = request.get_json(silent=True) or request.args
    queries = {}

    # --- Determine queries ---
    if not table:
        if not data:
            return jsonify({"error": "Trebuie să specifici tabele și criterii"}), 400
        queries = data
    else:
        queries = {table.lower(): [data]}

    response = {}

    for tbl, filters in queries.items():
        model = MODEL_MAP.get(tbl.capitalize()) or MODEL_MAP.get(tbl)
        if not model:
            response[tbl] = {"error": f"Tabelul '{tbl}' nu există"}
            continue

        results_total = []

        for f in filters:
            conditions = []

            for col, val in f.items():
                if col == "string":
                    like_val = val.get("like", val).lower()
                    like_conditions = [model.__dict__[c.name].ilike(f"%{like_val}%")
                                       for c in model.__table__.columns
                                       if str(c.type).startswith("VARCHAR")]
                    conditions.append(or_(*like_conditions))
                    continue

                if col == "number":
                    min_v = val.get("min", None)
                    max_v = val.get("max", None)

                    num_cols = [c.name for c in model.__table__.columns
                                if "INT" in str(c.type).upper() or
                                   "FLOAT" in str(c.type).upper() or
                                   "DECIMAL" in str(c.type).upper()]

                    num_conditions = []

                    for nc in num_cols:
                        column = getattr(model, nc)
                        if min_v is not None:
                            num_conditions.append(column >= min_v)
                        if max_v is not None:
                            num_conditions.append(column <= max_v)

                    if num_conditions:
                        conditions.append(and_(*num_conditions))

                    continue

                # normal filters
                column = getattr(model, col, None)
                if not column:
                    continue

                if isinstance(val, dict):  # min/max or LIKE
                    if "like" in val:
                        conditions.append(column.ilike(f"%{val['like']}%"))
                    if "min" in val:
                        conditions.append(column >= val["min"])
                    if "max" in val:
                        conditions.append(column <= val["max"])
                else:
                    conditions.append(column == val)

            query = model.query.filter(and_(*conditions))
            results_total.extend(query.all())

        response[tbl] = {
            "count": len(results_total),
            "results": [serialize_sql_row(x) for x in results_total]
        }

    return jsonify(response), 200

# POST /add
@api.route("/add", methods=["POST"])
@api.route("/add/<string:table>", methods=["POST"])
@allowed_users(["Angajat", "Administrator"])
def add_data(table=None):
    data = request.get_json() if request.is_json else request.args
    if not data:
        return jsonify({"error": "Trebuie trimis un obiect JSON sau ca argumente"}), 400

    # dacă tabelul nu e specificat, preluăm primul key din JSON
    if not table:
        if isinstance(data, dict) and len(data) == 1:
            table, objects = next(iter(data.items()))
        else:
            return jsonify({"error": "Trebuie să specifici un tabel"}), 400
    else:
        objects = data

    table = table.lower()
    dto_class = get_dto_class(table)
    model_class = MODEL_MAP.get(table.capitalize()) or MODEL_MAP.get(table)
    
    if not dto_class or not model_class:
        return jsonify({"error": f"Nu există DTO sau model pentru tabelul '{table}'"}), 400

    # normalizează la listă
    objects = objects if isinstance(objects, list) else [objects]

    validated_objects = []
    errors = []

    for i, obj in enumerate(objects):
        try:
            dto = dto_class(**obj)
            validated_objects.append(dto.dict())
        except ValidationError as e:
            errors.append({"index": i, "error": e.errors()})
        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    if errors:
        return jsonify({"errors": errors}), 400

    added_ids = []

    for obj in validated_objects:
        instance = model_class(**obj)
        db.session.add(instance)
        db.session.flush()  # obținem ID-ul generat
        added_ids.append(instance.id)

    db.session.commit()

    return jsonify({
        "message": f"{len(added_ids)} obiect(e) adăugat(e) în '{table}'",
        "ids": added_ids
    }), 201

# PUT and PATCH /update
@api.route("/update", methods=["PUT", "PATCH"])
@api.route("/update/<string:table>", methods=["PUT", "PATCH"])
@allowed_users(["Angajat", "Administrator"])
def update_data(table=None):
    data = request.get_json() if request.is_json else request.args
    if not data:
        return jsonify({"error": "Trebuie trimis un obiect JSON sau ca argumente"}), 400

    if not table:
        if len(data) != 1:
            return jsonify({"error": "Trebuie să specifici un singur tabel în body"}), 400
        table, objects = next(iter(data.items()))
    else:
        objects = data

    table = table.lower()
    model_class = MODEL_MAP.get(table.capitalize()) or MODEL_MAP.get(table)
    if not model_class:
        return jsonify({"error": f"Nu există model pentru tabelul '{table}'"}), 400

    objects = objects if isinstance(objects, list) else [objects]
    updated_ids = []
    warnings = []

    for obj in objects:
        try:
            dto = UpdateDTO(**obj)
        except ValidationError as e:
            return jsonify({"error": e.errors()}), 400

        update_fields = dto.update
        filter_criteria = dto.filter

        if not update_fields:
            warnings.append("Nu există câmpuri de actualizat (cheia 'update' lipsește)")
            continue

        if not filter_criteria:
            warnings.append("Nu există filter specificat, obiectul nu a fost actualizat")
            continue

        query = db.session.query(model_class)

        # Aplicăm filtre
        for k, v in filter_criteria.items():
            col = getattr(model_class, k, None)
            if not col:
                continue

            if isinstance(v, dict):
                if "like" in v:
                    query = query.filter(col.ilike(f"%{v['like']}%"))
                else:
                    min_val = v.get("min", None)
                    max_val = v.get("max", None)
                    if min_val is not None:
                        query = query.filter(col >= min_val)
                    if max_val is not None:
                        query = query.filter(col <= max_val)
            else:
                query = query.filter(col == v)

        matched_items = query.all()
        if not matched_items:
            warnings.append(f"Nu s-a găsit niciun obiect pentru filter-ul specificat în '{table}'")
            continue

        # Aplicare update
        for item in matched_items:
            for key, value in update_fields.items():
                if key == "id":
                    continue
                if hasattr(item, key):
                    setattr(item, key, value)
            updated_ids.append(item.id)

    if updated_ids:
        db.session.commit()

    response = {
        "message": f"{len(updated_ids)} obiect(e) actualizat(e) în '{table}'",
        "ids": updated_ids
    }
    if warnings:
        response["warnings"] = warnings

    return jsonify(response), 200 if updated_ids else 404

# DELETE /detele
@api.route("/delete", methods=["DELETE"])
@api.route("/delete/<string:table>", methods=["DELETE"])
@allowed_users(["Angajat", "Administrator"])
def delete_data(table=None):
    data = request.get_json() if request.is_json else request.args
    if not data:
        return jsonify({"error": "Trebuie trimis un obiect JSON sau ca argumente"}), 400

    if not table:
        if len(data) != 1:
            return jsonify({"error": "Trebuie să specifici un singur tabel în body"}), 400
        table, objects = next(iter(data.items()))
    else:
        objects = data

    table = table.lower()
    model_class = MODEL_MAP.get(table.capitalize()) or MODEL_MAP.get(table)
    if not model_class:
        return jsonify({"error": f"Nu există model pentru tabelul '{table}'"}), 400

    objects = objects if isinstance(objects, list) else [objects]
    deleted_ids = []
    warnings = []

    for obj in objects:
        dto = DeleteDTO(**obj)
        filter_criteria = dto.filter

        query = db.session.query(model_class)

        # Aplicăm filtre
        for k, v in filter_criteria.items():
            col = getattr(model_class, k, None)
            if not col:
                continue

            if isinstance(v, dict):
                if "like" in v:
                    query = query.filter(col.ilike(f"%{v['like']}%"))
                else:
                    min_val = v.get("min", None)
                    max_val = v.get("max", None)
                    if min_val is not None:
                        query = query.filter(col >= min_val)
                    if max_val is not None:
                        query = query.filter(col <= max_val)
            else:
                query = query.filter(col == v)

        matched_items = query.all()
        if not matched_items:
            warnings.append(f"Nu s-a găsit niciun obiect pentru filter-ul specificat în '{table}'")
            continue

        # Ștergere obiecte
        for item in matched_items:
            deleted_ids.append(item.id)
            db.session.delete(item)

    if deleted_ids:
        db.session.commit()

    response = {
        "message": f"{len(deleted_ids)} obiect(e) șters(e) din '{table}'",
        "ids": deleted_ids
    }
    if warnings:
        response["warnings"] = warnings

    return jsonify(response), 200 if deleted_ids else 404

###############
# END OF CRUD #
###############
