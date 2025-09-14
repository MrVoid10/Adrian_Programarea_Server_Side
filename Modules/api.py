from flask import Blueprint, jsonify, request, abort
from Modules.misc import products,stock,users,orders

api = Blueprint("api", __name__)

# Nivel 5: GET /list #
@api.route("/list", methods=["GET"])
def get_list():
  return jsonify(products)

# Nivel 6: GET /details/{id} #
@api.route("/produse", methods=["GET"])
@api.route("/produse/<int:product_id>", methods=["GET"])
@api.route("/details/<int:product_id>", methods=["GET"]) # conditila la nivel 6 #
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
def get_order_details(order_id=None):
  if order_id is None:
    return jsonify(orders)

  # Dupa ID
  order = next((o for o in orders if o["id"] == order_id), None)
  if not order:
    abort(404, description=f"Comanda cu id-ul {order_id} nu există")

  return jsonify(order)

@api.route("/comenzi/search", methods=["GET"])
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


# Nivel 9: public vs admin
# @api.route("/public/list", methods=["GET"])
# def public_list():
#   return jsonify([
#     {"id": p["id"], "name": p["name"], "category": p["category"]}
#     for p in products
#   ])

# # Nivel 10: doar admin
# @api.route("/admin/reports", methods=["GET"])
# def get_reports():
#   if claims.get("role") != "Admin":
#     abort(403, description="Acces interzis")
#   return {"report": "Raport tehnic complet"}