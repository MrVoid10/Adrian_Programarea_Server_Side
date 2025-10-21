from flask import Blueprint, jsonify, request, abort
from Modules.misc import products,stock,users,orders,TABLE_SCHEMAS, load_table , save_table, capitalize_name, get_dto_class,UpdateDTO,DeleteDTO
from Modules.jwt_utils import allowed_users
from pydantic import ValidationError

api = Blueprint("api", __name__)

# Nivel 7 --- Search "GET" --- #
@api.route("/search", methods=["GET"])
@api.route("/search/<string:table>", methods=["GET"])
@allowed_users(["Angajat", "Administrator"])
def search_data(table=None):
  data = request.get_json(silent=True) or request.args
  queries = {}

  if not table:
    if data and len(data) > 0:
      queries = data
    else:
      return jsonify({"error": "Trebuie să specifici tabele și criterii în body JSON sau query params"}), 400
  else:
    if data:
      queries = {table.lower(): data if isinstance(data, list) else [data]}
    else:
      queries = {table.lower(): [request.args.to_dict()]}

  response = {}

  for tbl, filters in queries.items():
    items = load_table(tbl)
    if not isinstance(items, list):
      response[tbl] = {"error": f"Structura tabelului '{tbl}' este invalidă"}
      continue

    matched = []
    for f in filters:
      for item in items:
        ok = True
        for k, v in f.items():

          # ------------------ string global ------------------
          if k == "string":
            if isinstance(v, dict) and "like" in v:
              val = v["like"].lower()
              if not any(isinstance(cv, str) and val in cv.lower() for cv in item.values()):
                ok = False
                break
            elif isinstance(v, str):
              if not any(isinstance(cv, str) and v.lower() in cv.lower() for cv in item.values()):
                ok = False
                break
            continue
          # ---------------------------------------------------

          # ------------------ number global ------------------
          if k == "number":
            if isinstance(v, dict):
              min_val = v.get("min", float("-inf"))
              max_val = v.get("max", float("inf"))
              if not any(
                isinstance(cv, (int, float)) and min_val <= cv <= max_val
                for cv in item.values()
              ):
                ok = False
                break
            elif isinstance(v, (int, float)):
              if not any(isinstance(cv, (int, float)) and cv == v for cv in item.values()):
                ok = False
                break
            continue
          # ---------------------------------------------------

          current_val = item.get(k)
          if isinstance(v, dict):
            if "like" in v:
              if not isinstance(current_val, str) or v["like"].lower() not in current_val.lower():
                ok = False
                break
            min_val = v.get("min", float("-inf"))
            max_val = v.get("max", float("inf"))
            if isinstance(current_val, (int, float)):
              if not (min_val <= current_val <= max_val):
                ok = False
                break
            else:
              if "min" in v or "max" in v:
                ok = False
                break
          else:
            if current_val != v:
              ok = False
              break
        if ok:
          matched.append(item)

    response[tbl] = {"count": len(matched), "results": matched}

  return jsonify(response), 200

# Nivel 8 --- Adaugare "POST" --- #
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
    if not dto_class:
        return jsonify({"error": f"Nu există DTO pentru tabelul '{table}'"}), 400

    # normalizează la listă
    objects = objects if isinstance(objects, list) else [objects]

    validated_objects = []
    errors = []

    for i, obj in enumerate(objects):
        try:
            dto = dto_class(**obj)
            validated_objects.append(dto.dict())
        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    if errors:
        return jsonify({"errors": errors}), 400

    # încărcăm datele existente și adăugăm id-uri
    items = load_table(table)
    added_ids = []
    for obj in validated_objects:
        new_id = max((item.get("id", 0) for item in items), default=0) + 1
        if "id" in obj:
            obj["id"] = new_id
        items.append(obj)
        added_ids.append(new_id)

    save_table(table, items)
    return jsonify({
        "message": f"{len(added_ids)} obiect(e) adăugat(e) în '{table}'",
        "ids": added_ids
    }), 201

# Nivel 8 --- Modificari "PUT & PATCH" --- #
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
  items = load_table(table)
  if not isinstance(items, list):
    return jsonify({"error": f"Structura tabelului '{table}' este invalidă"}), 500

  objects = objects if isinstance(objects, list) else [objects]

  updated_ids = []
  warnings = []

  for obj in objects:
    try:
      dto = UpdateDTO(**obj)
    except ValidationError as e:
      return jsonify({"error": e.errors()}), 400
    
    # update_fields = obj.get("update")
    # filter_criteria = obj.get("filter", {})

    update_fields = dto.update
    filter_criteria = dto.filter

    if not update_fields:
      warnings.append("Nu există câmpuri de actualizat (cheia 'update' lipsește)")
      continue

    if not filter_criteria:
      warnings.append("Nu există filter specificat, obiectul nu a fost actualizat")
      continue

    matched_items = []

    for item in items:
      match = True
      for k, v in filter_criteria.items():
        current_val = item.get(k)

        # String: aplica like dacă e string
        if isinstance(current_val, str):
          if isinstance(v, dict) and "like" in v:
            like_val = v["like"]
            if like_val and like_val.lower() not in current_val.lower():
              match = False
              break
          elif isinstance(v, str) and v.lower() not in current_val.lower():
            match = False
            break

        # Numeric: aplica egalitate sau min/max
        elif isinstance(current_val, (int, float)):
          if isinstance(v, dict):
            min_val = v.get("min", float("-inf"))
            max_val = v.get("max", float("inf"))
            if not (min_val <= current_val <= max_val):
              match = False
              break
          elif isinstance(v, (int, float)):
            if current_val != v:
              match = False
              break

        # Alte tipuri: verificare egalitate simplă
        else:
          if current_val != v:
            match = False
            break

      if match:
        matched_items.append(item)

    if not matched_items:
      warnings.append(f"Nu s-a găsit niciun obiect pentru filter-ul specificat în '{table}'")
      continue

    # Aplicare update
    for item in matched_items:
      for key, value in update_fields.items():
        if key == "id":  # nu schimbăm ID-ul
          continue
        item[key] = value
      updated_ids.append(item.get("id"))

  save_table(table, items)

  response = {
    "message": f"{len(updated_ids)} obiect(e) actualizat(e) în '{table}'",
    "ids": updated_ids
  }
  if warnings:
    response["warnings"] = warnings

  return jsonify(response), 200 if updated_ids else 404

# Nivel 8 --- Stergerea "DELETE" --- #
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
  items = load_table(table)
  if not isinstance(items, list):
    return jsonify({"error": f"Structura tabelului '{table}' este invalidă"}), 500

  objects = objects if isinstance(objects, list) else [objects]

  deleted_ids = []
  warnings = []

  for obj in objects:
    dto = DeleteDTO(obj)
    filter_criteria = dto.filter

    matched_items = []

    for item in items:
      match = True

      for k, v in filter_criteria.items():
        # universal string "like"
        if k == "string" and isinstance(v, dict):
          like_val = v.get("like")
          string_match = False
          for field, val in item.items():
            if isinstance(val, str) and like_val and like_val.lower() in val.lower():
              string_match = True
              break
          if not string_match:
            match = False
            break

        # universal number min/max
        elif k == "number" and isinstance(v, dict):
          min_val = v.get("min", float("-inf"))
          max_val = v.get("max", float("inf"))
          number_match = False
          for field, val in item.items():
            if isinstance(val, (int, float)) and min_val <= val <= max_val:
              number_match = True
              break
          if not number_match:
            match = False
            break

        # filtrare pe câmp numeric specific
        elif isinstance(v, dict) and ("min" in v or "max" in v):
          current_val = item.get(k)
          min_val = v.get("min", float("-inf"))
          max_val = v.get("max", float("inf"))
          if not (isinstance(current_val, (int, float)) and min_val <= current_val <= max_val):
            match = False
            break

        # filtrare exact pe câmp
        else:
          current_val = item.get(k)
          if current_val != v:
            match = False
            break

      if match:
        matched_items.append(item)

    if not matched_items:
      warnings.append(f"Nu s-a găsit niciun obiect pentru filter-ul specificat în '{table}'")
      continue

    for item in matched_items:
      items = [i for i in items if i.get("id") != item.get("id")]
      deleted_ids.append(item.get("id"))

  # recalculăm ID-urile
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

# Nivel 10 --- Raport "Administrator Only" --- #
@api.route("/raport", methods=["GET"])
@allowed_users(["Administrator"])
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

# Laboratorul 2: --- Endpoint cu useri si transformarea lor in majuscula --- #
@api.route("/users_Capitalization", methods=["GET"])
@allowed_users(["Angajat", "Administrator"])
@capitalize_name
def users_Capitalization(users_list):
  return jsonify({
    "count": len(users_list),
    "results": users_list
  }), 200

@api.route("/capital_search", methods=["GET"])
@api.route("/capital_search/<string:table>", methods=["GET"])
@allowed_users(["Angajat", "Administrator"])
def capital_search(table=None):
  data = request.get_json(silent=True)
  if not data:
    if table:
      data = {table.lower(): [request.args.to_dict()]}
    else:
      data = {"users": [request.args.to_dict()]}
  elif isinstance(data, list) and table:
    data = {table.lower(): data}
  elif isinstance(data, list) and not table:
    data = {"users": data}
  elif isinstance(data, dict) and table:
    data = {table.lower(): [data]}

  response = {}
  for tbl, filters in data.items():
    items = load_table(tbl)
    if not isinstance(items, list):
      response[tbl] = {"error": f"Structura tabelului '{tbl}' este invalidă"}
      continue

    modified_list = []
    original_list = []

    for item in items:
      include_item = True
      modified_fields = {}
      for f in filters:
        for k, v in f.items():
          if k == "capital":
            if isinstance(v, str) and v in item and isinstance(item[v], str):
              modified_fields[v] = item[v].upper()
            continue

          if k == "string":
            if isinstance(v, dict) and "like" in v:
              val = v["like"].lower()
              if not any(isinstance(cv, str) and val in cv.lower() for cv in item.values()):
                include_item = False
                break
            elif isinstance(v, str):
              if not any(isinstance(cv, str) and v.lower() in cv.lower() for cv in item.values()):
                include_item = False
                break
            continue

          if k == "number":
            if isinstance(v, dict):
              min_val = v.get("min", float("-inf"))
              max_val = v.get("max", float("inf"))
              if not any(isinstance(cv, (int, float)) and min_val <= cv <= max_val for cv in item.values()):
                include_item = False
                break
            elif isinstance(v, (int, float)):
              if not any(isinstance(cv, (int, float)) and cv == v for cv in item.values()):
                include_item = False
                break
            continue

          current_val = item.get(k)
          if isinstance(v, dict):
            if "like" in v:
              if not isinstance(current_val, str) or v["like"].lower() not in current_val.lower():
                include_item = False
                break
            min_val = v.get("min", float("-inf"))
            max_val = v.get("max", float("inf"))
            if isinstance(current_val, (int, float)):
              if not (min_val <= current_val <= max_val):
                include_item = False
                break
            else:
              if "min" in v or "max" in v:
                include_item = False
                break
          else:
            if current_val != v:
              include_item = False
              break
        if not include_item:
          break

      if include_item and modified_fields:
        modified_list.append(modified_fields)
        original_fields = {k: item[k] for k in modified_fields.keys()}
        original_list.append(original_fields)

    response[tbl] = {
      "modified": {"count": len(modified_list), "results": modified_list},
      "original": {"count": len(original_list), "results": original_list}
    }

  return jsonify(response), 200

################################################################################
# LEGACY #
################################################################################
# Nivel 5: GET /list #
@api.route("/list", methods=["GET"])
def get_list():
  return jsonify(products)

# Nivel 6: GET /details/{id} #
@api.route("/produse", methods=["GET"])
@api.route("/produse/<int:product_id>", methods=["GET"])
@api.route("/details/<int:product_id>", methods=["GET"]) # conditila la nivel 6 #
@allowed_users(["Client","Angajat", "Administrator"])
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
@allowed_users(["Angajat", "Administrator"])
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
@allowed_users(["Angajat", "Administrator"])
def get_order_details(order_id=None):
  if order_id is None:
    return jsonify(orders)

  # Dupa ID
  order = next((o for o in orders if o["id"] == order_id), None)
  if not order:
    abort(404, description=f"Comanda cu id-ul {order_id} nu există")

  return jsonify(order)

@api.route("/comenzi/search", methods=["GET"])
@allowed_users(["Angajat", "Administrator"])
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
