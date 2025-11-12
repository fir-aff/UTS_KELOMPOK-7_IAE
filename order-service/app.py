# order-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os

# 1. Inisialisasi Aplikasi
app = Flask(__name__)

# Konfigurasi Database (MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/order_service_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Definisikan URL layanan lain.
USER_SERVICE_URL = "http://127.0.0.1:5001"
RESTAURANT_SERVICE_URL = "http://127.0.0.1:5002"
DRIVER_SERVICE_URL = "http://127.0.0.1:5004"  # BARU: Menambahkan URL driver-service

# 2. Buat Model Database (Tidak ada perubahan di sini)
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='PENDING')
    # BARU: Tambahkan kolom untuk driver_id
    driver_id = db.Column(db.Integer, nullable=True) 
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_item = db.Column(db.Float, nullable=False)


# 3. Buat Endpoint (Kontrak API)

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data.get('user_id')
    items_data = data.get('items')

    if not user_id or not items_data:
        return jsonify({'error': 'Missing user_id or items'}), 400

    # === LANGKAH 1: Validasi User (Memanggil user-service) ===
    try:
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
        if user_response.status_code == 404:
            return jsonify({'error': 'User not found'}), 404
        user_response.raise_for_status()
        user_data = user_response.json()
        app.logger.info(f"User data: {user_data['name']}")
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling user-service: {e}")
        return jsonify({'error': f"Could not connect to user-service: {e}"}), 503

    # === LANGKAH 2: Validasi Menu & Hitung Total Harga (Memanggil restaurant-service) ===
    total_price = 0
    order_items_to_create = []
    restaurant_address = "" # BARU: Kita butuh alamat resto untuk driver

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
            
            # BARU: Ambil alamat restoran (Kita asumsikan 1 pesanan hanya dari 1 resto)
            # (Ini perlu request tambahan, tapi kita bisa akali dengan endpoint /menu/id)
            # Untuk simplifikasi, kita hardcode dulu. Di dunia nyata, /menu/id akan mengembalikan data resto.
            restaurant_address = "Jalan Padang No. 10" # Alamat dari Step 2

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling restaurant-service: {e}")
        return jsonify({'error': f"Could not connect to restaurant-service: {e}"}), 503

    # === LANGKAH 3: Simpan Pesanan ke Database ===
    try:
        new_order = Order(
            user_id=user_id,
            total_price=total_price,
            status='PENDING' # Status awal
        )
        for item in order_items_to_create:
            new_order.items.append(item)
        db.session.add(new_order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving to database: {e}")
        return jsonify({'error': 'Failed to save order to database'}), 500

    # === LANGKAH 4: BARU - Minta Driver (Memanggil driver-service) ===
    try:
        driver_request_payload = {
            "order_id": new_order.id,
            "restaurant_address": restaurant_address,
            "user_address": user_data.get('address') # Alamat user dari user-service
        }
        
        driver_response = requests.post(
            f"{DRIVER_SERVICE_URL}/drivers/request", 
            json=driver_request_payload
        )
        
        # Jika tidak ada driver, status order tetap 'PENDING'
        if driver_response.status_code == 404:
            app.logger.warn(f"No available drivers for order {new_order.id}")
            # Tidak return error, pesanan tetap dibuat tapi menunggu driver
        else:
            driver_response.raise_for_status() # Error jika bukan 404 atau 2xx
            driver_data = driver_response.json()
            app.logger.info(f"Driver {driver_data.get('driver_name')} assigned for order {new_order.id}")

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling driver-service: {e}")
        # Pesanan sudah dibuat, tapi gagal panggil driver.
        # Kita bisa biarkan statusnya 'PENDING' dan coba lagi nanti (antrian)
        # Untuk saat ini, kita biarkan saja.

    # === LANGKAH 5: Kirim Response (Format respons akhir) ===
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

# --- Endpoint 'Provider' untuk riwayat pesanan ---
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_by_user(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
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

# --- BARU: Endpoint 'Provider' yang dipanggil oleh driver-service ---
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
    
    app.logger.info(f"Order {order_id} status updated to {new_status} by driver {driver_id}")
    
    return jsonify({'message': 'Order status updated', 'order_id': order.id, 'new_status': order.status}), 200


# 4. Jalankan Aplikasi
if __name__ == '__main__':
    with app.app_context():
        # db.drop_all() # Hati-hati, ini akan menghapus data lama
        db.create_all() # Jalankan ini untuk menambah kolom 'driver_id'
        
    # Jalankan di port 5003
    app.run(host='0.0.0.0', port=5003, debug=True)