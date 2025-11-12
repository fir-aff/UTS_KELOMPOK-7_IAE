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
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)

    def to_dict(self):
        return { 'id': self.id, 'name': self.name, 'price': self.price, 'restaurant_id': self.restaurant_id }

# 3. Buat Endpoint (Kontrak API)

# --- CRUD untuk RESTORAN ---

@app.route('/restaurants', methods=['POST'])
def create_restaurant():
    data = request.get_json()
    new_resto = Restaurant(name=data['name'], address=data['address'])
    db.session.add(new_resto)
    db.session.commit()
    return jsonify({'message': 'Restaurant created', 'restaurant': new_resto.to_dict()}), 201

@app.route('/restaurants', methods=['GET'])
def get_all_restaurants():
    restos = Restaurant.query.all()
    return jsonify([resto.to_dict() for resto in restos]), 200

@app.route('/restaurants/<int:id>', methods=['PUT'])
def update_restaurant(id):
    resto = Restaurant.query.get(id)
    if not resto:
        return jsonify({'error': 'Restaurant not found'}), 404
    
    data = request.get_json()
    resto.name = data.get('name', resto.name)
    resto.address = data.get('address', resto.address)
    
    db.session.commit()
    return jsonify({'message': 'Restaurant updated', 'restaurant': resto.to_dict()}), 200

@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    resto = Restaurant.query.get(id)
    if not resto:
        return jsonify({'error': 'Restaurant not found'}), 404
    
    Menu.query.filter_by(restaurant_id=id).delete()
    db.session.delete(resto)
    db.session.commit()
    
    return jsonify({'message': 'Restaurant and its menus deleted'}), 200

# --- CRUD untuk MENU ---

@app.route('/restaurants/<int:resto_id>/menu', methods=['POST'])
def add_menu_item(resto_id):
    if not Restaurant.query.get(resto_id):
        return jsonify({'error': 'Restaurant not found'}), 404
        
    data = request.get_json()
    if not data.get('name') or not data.get('price'):
         return jsonify({'error': 'Name and price are required'}), 400

    new_menu = Menu(
        name=data['name'],
        price=data['price'],
        restaurant_id=resto_id
    )
    db.session.add(new_menu)
    db.session.commit()
    return jsonify({'message': 'Menu item added', 'menu': new_menu.to_dict()}), 201

@app.route('/restaurants/<int:resto_id>/menu', methods=['GET'])
def get_restaurant_menu(resto_id):
    if not Restaurant.query.get(resto_id):
        return jsonify({'error': 'Restaurant not found'}), 404
        
    menus = Menu.query.filter_by(restaurant_id=resto_id).all()
    return jsonify([menu.to_dict() for menu in menus]), 200

@app.route('/menu/<int:menu_id>', methods=['GET'])
def get_menu_item(menu_id):
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({'error': 'Menu item not found'}), 404
    return jsonify(menu.to_dict()), 200

@app.route('/menu/<int:menu_id>', methods=['PUT'])
def update_menu_item(menu_id):
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({'error': 'Menu item not found'}), 404
        
    data = request.get_json()
    menu.name = data.get('name', menu.name)
    menu.price = data.get('price', menu.price)
    
    db.session.commit()
    return jsonify({'message': 'Menu item updated', 'menu': menu.to_dict()}), 200

@app.route('/menu/<int:menu_id>', methods=['DELETE'])
def delete_menu_item(menu_id):
    menu = Menu.query.get(menu_id)
    if not menu:
        return jsonify({'error': 'Menu item not found'}), 404
        
    db.session.delete(menu)
    db.session.commit()
    
    return jsonify({'message': 'Menu item deleted'}), 200

# 4. Jalankan Aplikasi
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
    app.run(host='0.0.0.0', port=5002, debug=True)