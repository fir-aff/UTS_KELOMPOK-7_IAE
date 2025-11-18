# restaurant-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger # Import Swagger
import os

app = Flask(__name__)

# --- KONFIGURASI SWAGGER ---
swagger = Swagger(app, template={
    "info": {
        "title": "Restaurant Service API",
        "description": "API untuk manajemen Restoran dan Menu",
        "version": "1.0.0"
    }
})

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/restaurant_service_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    def to_dict(self): return { 'id': self.id, 'name': self.name, 'address': self.address }

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    # Ini adalah 'Foreign Key' yang menghubungkan Menu ke Restaurant
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)

    def to_dict(self):
        return { 'id': self.id, 'name': self.name, 'price': self.price, 'restaurant_id': self.restaurant_id }

# 3. Buat Endpoint (Kontrak API)

# --- CRUD untuk RESTORAN ---

@app.route('/restaurants', methods=['POST'])
def create_restaurant():
    """
    Membuat restoran baru
    ---
    tags:
      - Restaurant
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - address
          properties:
            name:
              type: string
            address:
              type: string
    responses:
      201:
        description: Restoran berhasil dibuat
    """
    data = request.get_json()
    new_resto = Restaurant(name=data['name'], address=data['address'])
    db.session.add(new_resto); db.session.commit()
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

# Endpoint untuk melihat semua menu dari satu restoran
@app.route('/restaurants/<int:resto_id>/menu', methods=['GET'])
def get_restaurant_menu(resto_id):
    """
    Mendapatkan semua menu dari satu restoran
    ---
    tags:
      - Menu
    parameters:
      - name: resto_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: List menu
    """
    menus = Menu.query.filter_by(restaurant_id=resto_id).all()
    return jsonify([menu.to_dict() for menu in menus]), 200

@app.route('/menu/<int:menu_id>', methods=['GET'])
def get_menu_item(menu_id):
    """
    Detail satu menu
    ---
    tags:
      - Menu
    parameters:
      - name: menu_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Detail menu
    """
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

@app.route('/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/debug/seed', methods=['POST'])
def seed_restaurants():
    try:
        db.session.query(Menu).delete()
        db.session.query(Restaurant).delete()
        
        r1 = Restaurant(name='Restoran Padang', address='Jl. Merdeka No 5')
        db.session.add(r1); db.session.commit()
        
        m1 = Menu(name='Rendang', price=20000, restaurant_id=r1.id)
        m2 = Menu(name='Ayam Pop', price=18000, restaurant_id=r1.id)
        
        r2 = Restaurant(name='Warung Tegal', address='Jl. Sudirman No 10')
        db.session.add(r2); db.session.commit()
        
        m3 = Menu(name='Nasi Oreg', price=10000, restaurant_id=r2.id)
        
        db.session.add_all([m1, m2, m3]); db.session.commit()
        return jsonify({'message': 'Restaurant database seeded!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
    app.run(host='0.0.0.0', port=5002, debug=True)