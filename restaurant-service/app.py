# restaurant-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

# 1. Inisialisasi Aplikasi
app = Flask(__name__)

# Konfigurasi Database (MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/restaurant_service_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 2. Buat Model Database
class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    
    def to_dict(self):
        return { 'id': self.id, 'name': self.name, 'address': self.address }

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    # Ini adalah 'Foreign Key' yang menghubungkan Menu ke Restaurant
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)

    def to_dict(self):
        return { 'id': self.id, 'name': self.name, 'price': self.price }

# 3. Buat Endpoint (Kontrak API)

# Endpoint untuk membuat restoran baru
@app.route('/restaurants', methods=['POST'])
def create_restaurant():
    data = request.get_json()
    new_resto = Restaurant(name=data['name'], address=data['address'])
    db.session.add(new_resto)
    db.session.commit()
    return jsonify({'message': 'Restaurant created', 'restaurant': new_resto.to_dict()}), 201

# Endpoint untuk mendapatkan semua restoran
@app.route('/restaurants', methods=['GET'])
def get_all_restaurants():
    restos = Restaurant.query.all()
    return jsonify([resto.to_dict() for resto in restos]), 200

# Endpoint untuk menambah menu ke restoran
@app.route('/restaurants/<int:resto_id>/menu', methods=['POST'])
def add_menu_item(resto_id):
    # Cek dulu apakah restorannya ada
    if not Restaurant.query.get(resto_id):
        return jsonify({'error': 'Restaurant not found'}), 404
        
    data = request.get_json()
    new_menu = Menu(
        name=data['name'],
        price=data['price'],
        restaurant_id=resto_id
    )
    db.session.add(new_menu)
    db.session.commit()
    return jsonify({'message': 'Menu item added', 'menu': new_menu.to_dict()}), 201

# Endpoint untuk melihat semua menu dari satu restoran
@app.route('/restaurants/<int:resto_id>/menu', methods=['GET'])
def get_restaurant_menu(resto_id):
    if not Restaurant.query.get(resto_id):
        return jsonify({'error': 'Restaurant not found'}), 404
        
    menus = Menu.query.filter_by(restaurant_id=resto_id).all()
    return jsonify([menu.to_dict() for menu in menus]), 200

# Endpoint untuk mendapatkan detail 1 menu (PENTING untuk 'order-service')
# Ini adalah endpoint yang akan dikonsumsi oleh layanan lain.
@app.route('/menu/<int:menu_id>', methods=['GET'])
def get_menu_item(menu_id):
    menu = Menu.query.get(menu_id)
    
    if not menu:
        return jsonify({'error': 'Menu item not found'}), 404
        
    # Kita tambahkan restaurant_id di response agar 'order-service' tahu
    response = menu.to_dict()
    response['restaurant_id'] = menu.restaurant_id
    return jsonify(response), 200

# 4. Jalankan Aplikasi
if __name__ == '__main__':
    # Buat tabel database jika belum ada
    with app.app_context():
        db.create_all()
        
    # Jalankan di port 5002
    app.run(host='0.0.0.0', port=5002, debug=True)