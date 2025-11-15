# order-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from flask_jwt_extended import get_jwt_identity, jwt_required, JWTManager

# 1. Inisialisasi Aplikasi
app = Flask(__name__)

# Konfigurasi Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/order_service_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Konfigurasi JWT (KUNCI BARU)
app.config["JWT_SECRET_KEY"] = "ini-pasti-berhasil-777" # HARUS SAMA PERSIS
jwt = JWTManager(app)

db = SQLAlchemy(app)

# 2. Buat Model Database
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='PENDING')
    driver_id = db.Column(db.Integer, nullable=True) 
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_item = db.Column(db.Float, nullable=False)

# URL Service
USER_SERVICE_URL = "http://127.0.0.1:5001"
RESTAURANT_SERVICE_URL = "http://127.0.0.1:5002"
DRIVER_SERVICE_URL = "http://127.0.0.1:5004"

# 3. Buat Endpoint

# Endpoint INTI: Membuat pesanan baru
@app.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity() 
    data = request.get_json()
    items_data = data.get('items')

    if not items_data:
        return jsonify({'error': 'Missing items'}), 400

    # === LANGKAH 1: Validasi User
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
        user_response.raise_for_status()
        user_data = user_response.json()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling user-service: {e}")
        return jsonify({'error': f"Could not connect to user-service: {e}"}), 503

    # === LANGKAH 2: Validasi Menu & Hitung Total Harga
    total_price = 0
    order_items_to_create = []
    restaurant_address = "" 

    try:
        for item in items_data:
            menu_id = item['menu_id']
            quantity = item['quantity']
            menu_response = requests.get(f"{RESTAURANT_SERVICE_URL}/menu/{menu_id}")
            if menu_response.status_code == 404:
                return jsonify({'error': f'Menu item with id {menu_id} not found'}), 404
            menu_response.raise_for_status()
            menu_data = menu_response.json()
            item_price = menu_data['price']
            total_price += item_price * quantity
            order_items_to_create.append(OrderItem(
                menu_id=menu_id,
                quantity=quantity,
                price_per_item=item_price
            ))
            restaurant_address = "Jalan Padang No. 10" # Asumsi dari 1 resto

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling restaurant-service: {e}")
        return jsonify({'error': f"Could not connect to restaurant-service: {e}"}), 503

    # === LANGKAH 3: Simpan Pesanan ke Database
    try:
        new_order = Order(
            user_id=user_id,
            total_price=total_price,
            status='PENDING'
        )
        for item in order_items_to_create:
            new_order.items.append(item)
        db.session.add(new_order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving to database: {e}")
        return jsonify({'error': 'Failed to save order to database'}), 500

    # === LANGKAH 4: Minta Driver
    try:
        driver_request_payload = {
            "order_id": new_order.id,
            "restaurant_address": restaurant_address,
            "user_address": user_data.get('address')
        }
        driver_response = requests.post(
            f"{DRIVER_SERVICE_URL}/drivers/request", 
            json=driver_request_payload
        )
        if driver_response.status_code == 404:
            app.logger.warn(f"No available drivers for order {new_order.id}")
        else:
            driver_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling driver-service: {e}")

    # === LANGKAH 5: Kirim Response
    created_order_json = {
        'order_id': new_order.id,
        'user_id': new_order.user_id,
        'status': new_order.status,
        'total_price': new_order.total_price,
        'user_name': user_data.get('name'),
        'items': [
            {'menu_id': item.menu_id, 'quantity': item.quantity} 
            for item in new_order.items
        ]
    }
    return jsonify({'message': 'Order created and driver search initiated', 'order': created_order_json}), 201


# Endpoint riwayat pesanan (Nama baru Anda)
@app.route('/orders/my-history', methods=['GET'])
@jwt_required()
def get_my_orders():
    user_id = get_jwt_identity()
    
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()
    if not orders:
        return jsonify({'message': 'No orders found for this user'}), 404
    
    result = []
    for order in orders:
        result.append({
            'order_id': order.id,
            'status': order.status,
            'total_price': order.total_price,
            'driver_id': order.driver_id
        })
    return jsonify(result), 200

# Endpoint untuk Admin (Mengambil SEMUA order)
@app.route('/orders', methods=['GET'])
def get_all_orders():
    orders = Order.query.order_by(Order.id.desc()).all()
    result = []
    for order in orders:
        result.append({
            'order_id': order.id,
            'user_id': order.user_id,
            'status': order.status,
            'total_price': order.total_price,
            'driver_id': order.driver_id
        })
    return jsonify(result), 200

# Endpoint Callback dari driver-service (Tidak perlu JWT)
@app.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
        
    data = request.get_json()
    new_status = data.get('status')
    driver_id = data.get('driver_id')
    
    if not new_status:
        return jsonify({'error': 'Missing new status'}), 400
        
    order.status = new_status
    if driver_id:
        order.driver_id = driver_id
        
    db.session.commit()
    return jsonify({'message': 'Order status updated', 'order_id': order.id, 'new_status': order.status}), 200

# Endpoint untuk Selesaikan Pesanan (dipanggil frontend)
@app.route('/orders/<int:order_id>/complete', methods=['PUT'])
@jwt_required() 
def complete_order(order_id):
    user_id = get_jwt_identity() 
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # (Bisa tambahkan cek admin/pemilik di sini)
    # if order.user_id != user_id:
    #     return jsonify({'error': 'Forbidden'}), 403
    
    order.status = 'DELIVERED'
    db.session.commit()
    app.logger.info(f"Order {order.id} status updated to DELIVERED by user {user_id}")
    
    if order.driver_id:
        try:
            callback_url = f"{DRIVER_SERVICE_URL}/drivers/{order.driver_id}/status"
            callback_payload = {"status": "available"}
            requests.put(callback_url, json=callback_payload)
            app.logger.info(f"Successfully called driver-service to release driver {order.driver_id}")
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Failed to call driver-service to release driver {order.driver_id}: {e}")

    return jsonify({'message': 'Order completed and driver released'}), 200

# Endpoint Health Check
@app.route('/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 503

# 4. Jalankan Aplikasi
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(host='0.0.0.0', port=5003, debug=True)