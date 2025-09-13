from flask import Blueprint, jsonify, request, abort

api = Blueprint("api", __name__)

products = [
  {"id": 1, "name": "Laptop Dell XPS", "price": 5200, "category": "Laptop"},
  {"id": 2, "name": "Laptop ASUS TUF", "price": 4300, "category": "Laptop"},
  {"id": 3, "name": "Telefon Samsung S24", "price": 3700, "category": "Telefon"},
  {"id": 4, "name": "Telefon iPhone 15", "price": 6000, "category": "Telefon"},
  {"id": 5, "name": "PC Gaming Ryzen", "price": 7200, "category": "PC"},
  {"id": 6, "name": "PC Office Intel", "price": 2800, "category": "PC"},
  {"id": 7, "name": "Cabluri HDMI", "price": 50, "category": "Accesorii"},
  {"id": 8, "name": "Monitor LG 27''", "price": 1200, "category": "Monitor"},
  {"id": 9, "name": "Mouse Logitech G502", "price": 350, "category": "Periferice"},
  {"id": 10, "name": "Tastatură Redragon", "price": 200, "category": "Periferice"},
]

users = [
  {
    "id": 1,
    "username": "admin",
    "password": "admin123",
    "role": "Admin"
  },
  {
    "id": 2,
    "username": "employee",
    "password": "emp123",
    "role": "Angajat"
  },
  {
    "id": 3,
    "username": "client",
    "password": "client123",
    "role": "Client"
  }
]

# Nivel 5: GET /list #
@api.route("/list", methods=["GET"])
def get_list():
  return jsonify(products)

# Nivel 6: GET /details/{id}
@api.route("/details/<int:product_id>", methods=["GET"])
def get_details(product_id):
  product = next((p for p in products if p["id"] == product_id), None)
  if not product:
    abort(404, description="Produsul nu există")
  return jsonify(product)

# Nivel 8: căutare cu query params
@api.route("/search", methods=["GET"])
def search_products():
  name = request.args.get("name", "").lower()
  min_price = request.args.get("minPrice", type=int)
  max_price = request.args.get("maxPrice", type=int)

  results = products
  if name:
    results = [p for p in results if name in p["name"].lower()]
  if min_price is not None:
    results = [p for p in results if p["price"] >= min_price]
  if max_price is not None:
    results = [p for p in results if p["price"] <= max_price]

  return jsonify(results)

# Nivel 9: public vs admin
@api.route("/public/list", methods=["GET"])
def public_list():
  return jsonify([
    {"id": p["id"], "name": p["name"], "category": p["category"]}
    for p in products
  ])

# Nivel 10: doar admin
@api.route("/admin/reports", methods=["GET"])
@jwt_required()
def get_reports():
  claims = get_jwt()
  if claims.get("role") != "Admin":
    abort(403, description="Acces interzis")
  return {"report": "Raport tehnic complet"}