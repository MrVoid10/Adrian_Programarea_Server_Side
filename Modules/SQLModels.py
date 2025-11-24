#SQLModels.py
from Modules.DBConn import db
from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, Text
from sqlalchemy.orm import relationship
import json
from datetime import datetime,date

class Camera(db.Model):
    __tablename__ = 'Camere'
    Id = db.Column(db.String(50), primary_key=True)
    Nume = db.Column(db.String(100), nullable=False)
    Pret = db.Column(db.Float, nullable=False)
    Moneda = db.Column(db.String(10), nullable=False)
    Imagine = db.Column(db.String(255))
    Descriere = db.Column(db.Text)

    # relationship with CamereDisponibile
    camere_disponibile = db.relationship("CameraDisponibila", back_populates="camera")


class CameraDisponibila(db.Model):
    __tablename__ = 'CamereDisponibile'
    Id = db.Column(db.String(50), primary_key=True)
    CameraId = db.Column(db.String(50), db.ForeignKey('Camere.Id'))
    Libera = db.Column(db.Boolean, default=True)

    camera = db.relationship("Camera", back_populates="camere_disponibile")


class Feedback(db.Model):
    __tablename__ = 'Feedback'
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    Message = db.Column(db.Text, nullable=False)
    DateSent = db.Column(db.DateTime, default=datetime.utcnow)

    # Normal Project

class Product(db.Model):
    __tablename__ = 'Products'

    id = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    descriere = db.Column(db.Text)
    pret = db.Column(db.Numeric(18, 2), nullable=False)
    categorie = db.Column(db.String(100))
    garantie = db.Column(db.Integer)
    status = db.Column(db.String(50))
    imagine = db.Column(db.Text)
    data_adaugare = db.Column(db.Date)

    # One product -> multiple stock rows
    stock_items = relationship("Stock", back_populates="product")

    # Many-to-many: Products <-> Orders (via OrderProducts)
    order_products = relationship("OrderProduct", back_populates="product")

    def __repr__(self):
        return f"<Product {self.id} {self.nume}>"


class Stock(db.Model):
    __tablename__ = 'Stock'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    produs_id = db.Column(db.Integer, db.ForeignKey('Products.id'))
    cantitate = db.Column(db.Integer, nullable=False, default=0)
    depozit = db.Column(db.String(255), nullable=False)

    product = relationship("Product", back_populates="stock_items")

    def __repr__(self):
        return f"<Stock {self.id} produs={self.produs_id} cantitate={self.cantitate}>"


class User(db.Model):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    nume = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Client')
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # One user -> many orders
    orders = relationship("Order", back_populates="client")

    def __repr__(self):
        return f"<User {self.id} {self.username}>"


class Order(db.Model):
    __tablename__ = 'Orders'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    data_comanda = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(50), nullable=False)

    client = relationship("User", back_populates="orders")

    # Many-to-many: Orders <-> Products (via OrderProducts)
    products = relationship("OrderProduct", back_populates="order")

    def __repr__(self):
        return f"<Order {self.id} client={self.client_id}>"


class OrderProduct(db.Model):
    __tablename__ = 'OrderProducts'

    order_id = db.Column(db.Integer, db.ForeignKey('Orders.id'), primary_key=True)
    produs_id = db.Column(db.Integer, db.ForeignKey('Products.id'), primary_key=True)
    cantitate = db.Column(db.Integer, nullable=False)
    pret_unitate = db.Column(db.Numeric(18, 2), nullable=False)

    # Many-to-many intermediate table relations
    order = relationship("Order", back_populates="products")
    product = relationship("Product", back_populates="order_products")

    def __repr__(self):
        return f"<OrderProduct order={self.order_id} produs={self.produs_id}>"

MODEL_MAP = {
    "products": Product,
    "orders": Order,
    "stock": Stock,
    "users": User,
    "order_product": OrderProduct,

    # dacă ai modele suplimentare neutilizate în proiect:
    "camera": Camera,
    "cameradisponibila": CameraDisponibila,
    "feedback": Feedback,
}