from flask import Blueprint, jsonify, request, abort
from Modules.misc import products,stock,users,orders,TABLE_SCHEMAS, load_table , save_table
from flask_jwt_extended import jwt_required, get_jwt
from Modules.jwt_utils import allowed_users

api = Blueprint("api", __name__)

# Nivel 5: GET /list #
@api.route("/list", methods=["GET"])
def get_list():
  return jsonify(products)

# Nivel 6: GET /details/{id} #
@api.route("/produse", methods=["GET"])
@api.route("/produse/<int:product_id>", methods=["GET"])
@api.route("/details/<int:product_id>", methods=["GET"]) # conditila la nivel 6 #
@allowed_users(["Client","Angajat", "Administrator"])  ##### verificare rol
def get_product_details(product_id):
  if product_id is None:
    return jsonify(products)
  
  product = next((p for p in products if p["id"] == product_id), None)
  if not product:
    abort(404, description="Produsul nu există")
  return jsonify(product)

# Nivel 7.1 GET /stoc/{id} #
@api.route("/stoc", methods=["GET"])
@api.route("/stoc/<int:product_id>", methods=["GET"])
@allowed_users(["Angajat", "Administrator"])  ##### verificare rol
def get_stock_details(product_id):
  if product_id is None:
    return jsonify(stoc)

  stoc = next((s for s in stock if s["produs_id"] == product_id), None)
  if not stoc:
    abort(404, description=f"Stocul pentru produsul cu id-ul:{product_id} nu există")
  return jsonify(stoc)

# Nivel 7.2 Get /comenzi/{id} #
@api.route("/comenzi", methods=["GET"])
@api.route("/comenzi/<int:order_id>", methods=["GET"])
@allowed_users(["Angajat", "Administrator"])  ##### verificare rol
def get_order_details(order_id=None):
  if order_id is None:
    return jsonify(orders)

  # Dupa ID
  order = next((o for o in orders if o["id"] == order_id), None)
  if not order:
    abort(404, description=f"Comanda cu id-ul {order_id} nu există")

  return jsonify(order)

@api.route("/comenzi/search", methods=["GET"])
@allowed_users(["Angajat", "Administrator"])  ##### verificare rol
def search_orders():
  id_query = request.args.get("id")
  produs_id_query = request.args.get("produs_id")
  name_query = request.args.get("name", "").lower()
  status_query = request.args.get("status", "").lower()
  min_price = request.args.get("min_price")
  max_price = request.args.get("max_price")
  exact_price = request.args.get("price")

  # Convertim la int sau float dacă există
  id_query = int(id_query) if id_query else None
  produs_id_query = int(produs_id_query) if produs_id_query else None
  min_price = float(min_price) if min_price else None
  max_price = float(max_price) if max_price else None
  exact_price = float(exact_price) if exact_price else None

  # Filtrăm comenzile
  result = []
  for o in orders:
    # Filtrare după id comandă
    if id_query and o["id"] != id_query:
      continue

    # Filtrare după client
    client = next((u for u in users if u["id"] == o["client_id"]), None)
    if name_query and client and name_query not in client["nume"].lower():
      continue

    # Filtrare după status
    if status_query and status_query != o["status"].lower():
      continue

    # Filtrare după produs_id
    if produs_id_query and all(item["produs_id"] != produs_id_query for item in o["produse"]):
      continue

    # Calculăm totalul comenzii
    total = sum(item["pret_unitate"] * item["cantitate"] for item in o["produse"])

    # Filtrare după preț
    if min_price is not None and total < min_price:
      continue
    if max_price is not None and total > max_price:
      continue
    if exact_price is not None and total != exact_price:
      continue

    result.append(o)

  return jsonify(result)

# Nivel 9 /add #
@api.route("/add", methods=["POST"])
@api.route("/add/<string:table>", methods=["POST"])
@allowed_users(["Angajat", "Administrator"])  ##### verificare rol
def add_data(table=None):
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
    items = load_table(table)
    schema = TABLE_SCHEMAS.get(table, {})
    if not schema:
        return jsonify({"error": f"Schema pentru '{table}' nu există"}), 400

    objects = objects if isinstance(objects, list) else [objects]
    added_ids, warnings = [], []

    for obj in objects:
        new_id = max((item.get("id", 0) for item in items), default=0) + 1
        new_obj = {**schema, **obj, "id": new_id}
        missing = [k for k in schema if k not in obj and k != "id"]
        if missing:
            warnings.append(f"Obiect id={new_id}: câmpuri lipsă completate automat: {', '.join(missing)}")
        items.append(new_obj)
        added_ids.append(new_id)

    save_table(table, items)
    response = {"message": f"{len(added_ids)} obiect(e) adăugat(e) în '{table}'", "ids": added_ids}
    if warnings:
        response["warnings"] = warnings

    return jsonify(response), 201

# Nivel 9 /delete cu resortare ID-uri
@api.route("/delete", methods=["DELETE"])
@api.route("/delete/<string:table>", methods=["DELETE"])
@allowed_users(["Angajat", "Administrator"])  ##### verificare rol
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
    items = load_table(table)
    if not isinstance(items, list):
        return jsonify({"error": f"Structura tabelului '{table}' este invalidă"}), 500

    objects = objects if isinstance(objects, list) else [objects]

    deleted_ids = []
    warnings = []

    for obj in objects:
        obj_id = obj.get("id")
        if obj_id is None:
            warnings.append("Un obiect nu are id specificat și nu a fost șters")
            continue

        match_found = any(item.get("id") == obj_id for item in items)
        if not match_found:
            warnings.append(f"Obiect cu id={obj_id} nu există în '{table}'")
            continue

        items = [item for item in items if item.get("id") != obj_id]
        deleted_ids.append(obj_id)

    # Resortăm ID-urile pentru a fi consecutive
    for index, item in enumerate(items, start=1):
        item["id"] = index

    save_table(table, items)

    response = {
        "message": f"{len(deleted_ids)} obiect(e) șters(e) din '{table}'",
        "ids": deleted_ids
    }
    if warnings:
        response["warnings"] = warnings

    return jsonify(response), 200 if deleted_ids else 404

# Nivel 9 /update #
@api.route("/update", methods=["PUT", "PATCH"])
@api.route("/update/<string:table>", methods=["PUT", "PATCH"])
@allowed_users(["Angajat", "Administrator"])  ##### verificare rol
def update_data(table=None):
    data = request.get_json() if request.is_json else request.args
    if not data:
        return jsonify({"error": "Trebuie trimis un obiect JSON sau ca argumente"}), 400

    # Deducem tabelul dacă nu e în URL
    if not table:
        if len(data) != 1:
            return jsonify({"error": "Trebuie să specifici un singur tabel în body"}), 400
        table, objects = next(iter(data.items()))
    else:
        objects = data

    table = table.lower()
    items = load_table(table)
    if not isinstance(items, list):
        return jsonify({"error": f"Structura tabelului '{table}' este invalidă"}), 500

    # Transformăm într-o listă dacă e un singur obiect
    objects = objects if isinstance(objects, list) else [objects]

    updated_ids = []
    warnings = []

    for obj in objects:
        update_fields = obj.get("update", obj)
        filter_criteria = obj.get("filter", {})
        obj_id = obj.get("id")
        obj_ids = obj.get("ids", [])

        matched_items = []

        # Căutăm după id
        if obj_id is not None:
            existing_obj = next((item for item in items if item.get("id") == obj_id), None)
            if existing_obj:
                matched_items.append(existing_obj)
            else:
                warnings.append(f"Obiect cu id={obj_id} nu există în '{table}'")
                continue

        # Căutăm după ids
        elif obj_ids:
            for i in obj_ids:
                existing_obj = next((item for item in items if item.get("id") == i), None)
                if existing_obj:
                    matched_items.append(existing_obj)
                else:
                    warnings.append(f"Obiect cu id={i} nu există în '{table}'")
        
        # Căutăm după filter avansat
        elif filter_criteria:
            for item in items:
                match = True
                for k, v in filter_criteria.items():
                    current_val = item.get(k)
                    if isinstance(v, dict):
                        # LIKE
                        if "like" in v:
                            if not isinstance(current_val, str) or v["like"].lower() not in current_val.lower():
                                match = False
                                break
                        # RANGE
                        min_val = v.get("min", float("-inf"))
                        max_val = v.get("max", float("inf"))
                        if isinstance(current_val, (int, float)):
                            if not (min_val <= current_val <= max_val):
                                match = False
                                break
                        else:
                            if "min" in v or "max" in v:
                                match = False
                                break
                    else:
                        # exact match
                        if current_val != v:
                            match = False
                            break
                if match:
                    matched_items.append(item)

            if not matched_items:
                warnings.append(f"Nu s-a găsit niciun obiect pentru filter-ul specificat în '{table}'")
                continue

        else:
            warnings.append("Un obiect nu are id, ids sau filter specificat și nu a fost actualizat")
            continue

        # Actualizăm obiectele potrivite
        for item in matched_items:
            for key, value in update_fields.items():
                if key == "id":
                    continue
                item[key] = value
            updated_ids.append(item.get("id"))

    # Salvăm lista actualizată
    save_table(table, items)

    response = {
        "message": f"{len(updated_ids)} obiect(e) actualizat(e) în '{table}'",
        "ids": updated_ids
    }
    if warnings:
        response["warnings"] = warnings

    return jsonify(response), 200 if updated_ids else 404

@api.route("/raport", methods=["GET"])
@allowed_users(["Administrator"])  ##### verificare rol
def generate_report():
    total_produse = len(products)
    total_comenzi = len(orders)
    
    valoare_totala_comenzi = 0
    for comanda in orders:
        for produs in comanda.get("produse", []):
            pret = produs.get("pret_unitate", 0)
            cantitate = produs.get("cantitate", 0)
            valoare_totala_comenzi += pret * cantitate

    raport = {
        "total_produse": total_produse,
        "total_comenzi": total_comenzi,
        "valoare_totala_comenzi": valoare_totala_comenzi
    }

    return jsonify(raport), 200
