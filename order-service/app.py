# order-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from flasgger import Swagger # Import

app = Flask(__name__)
# Init Swagger
swagger = Swagger(app, template={
    "info": {
        "title": "Order Service API",
        "description": "API untuk manajemen pesanan",
        "version": "1.0.0"
    }
})

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/order_service_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

USER_SERVICE_URL = "http://127.0.0.1:5001"
RESTAURANT_SERVICE_URL = "http://127.0.0.1:5002"
DRIVER_SERVICE_URL = "http://127.0.0.1:5004"  # BARU: Menambahkan URL driver-service

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
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    menu_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_item = db.Column(db.Float, nullable=False)

@app.route('/orders', methods=['POST'])
def create_order():
    """
    Membuat pesanan baru
    ---
    tags:
      - Orders
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - items
          properties:
            user_id:
              type: integer
              description: ID User yang memesan (Non-JWT)
            items:
              type: array
              items:
                type: object
                properties:
                  menu_id:
                    type: integer
                  quantity:
                    type: integer
    responses:
      201:
        description: Pesanan berhasil dibuat
      400:
        description: Data tidak lengkap
      503:
        description: Service lain tidak merespons
    """
    data = request.get_json()
    user_id = data.get('user_id') # Non-JWT
    items_data = data.get('items')

    if not user_id or not items_data: return jsonify({'error': 'Missing data'}), 400

    # 1. Validasi User
    try:
        requests.get(f"{USER_SERVICE_URL}/users/{user_id}").raise_for_status()
    except: return jsonify({'error': 'User invalid'}), 503

    # 2. Hitung Harga
    total_price = 0
    order_items_to_create = []
    restaurant_address = "Jalan Padang No. 10" # Asumsi/Hardcode

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
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling restaurant-service: {e}")
        return jsonify({'error': f"Could not connect to restaurant-service: {e}"}), 503

    # === LANGKAH 3: Simpan Pesanan ke Database ===
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

    # === LANGKAH 4: Minta Driver (Memanggil driver-service) ===
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
            driver_data = driver_response.json()
            app.logger.info(f"Driver {driver_data.get('driver_name')} assigned for order {new_order.id}")

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling driver-service: {e}")

    # === LANGKAH 5: Kirim Response ===
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

# BARU: Endpoint untuk mendapatkan SEMUA pesanan (untuk Admin)
@app.route('/orders', methods=['GET'])
def get_all_orders():
    try:
        orders = Order.query.all()
        result = []
        for order in orders:
            result.append({
                'order_id': order.id,
                'user_id': order.user_id,
                'status': order.status,
                'total_price': order.total_price,
                'driver_id': order.driver_id
            })
        # Urutkan dari yang terbaru
        result.sort(key=lambda x: x['order_id'], reverse=True)
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Error getting all orders: {e}")
        return jsonify({'error': str(e)}), 500

# --- Endpoint 'Provider' untuk riwayat pesanan ---
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    """
    Melihat riwayat pesanan User
    ---
    tags:
      - Orders
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: List pesanan user
    """
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()
    result = []
    for o in orders:
        result.append({'order_id': o.id, 'status': o.status, 'total_price': o.total_price, 'driver_id': o.driver_id})
    return jsonify(result), 200

# --- Endpoint 'Provider' yang dipanggil oleh driver-service ---
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

# --- Endpoint untuk menyelesaikan pesanan (dipanggil oleh Frontend) ---
@app.route('/orders/<int:order_id>/complete', methods=['PUT'])
def complete_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    # 1. Ubah status order di database ini
    order.status = 'DELIVERED'
    db.session.commit()
    app.logger.info(f"Order {order.id} status updated to DELIVERED")

    # 2. Periksa apakah ada driver yang ditugaskan
    if order.driver_id:
        driver_id = order.driver_id
        app.logger.info(f"Order {order.id} was handled by driver {driver_id}. Releasing driver...")

        # 3. Panggil driver-service untuk membebaskan driver (Peran Consumer)
        try:
            callback_url = f"{DRIVER_SERVICE_URL}/drivers/{driver_id}/status"
            callback_payload = {"status": "available"}

            response = requests.put(callback_url, json=callback_payload)
            response.raise_for_status() # Error jika status code bukan 2xx

            app.logger.info(f"Successfully called driver-service to release driver {driver_id}")

        except requests.exceptions.RequestException as e:
            app.logger.error(f"Failed to call driver-service to release driver {driver_id}: {e}")

    return jsonify({'message': 'Order completed and driver released'}), 200

@app.route('/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
    
@app.route('/debug/seed', methods=['POST'])
def seed_orders():
    try:
        # Hapus data lama
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        
        # Kita asumsikan User ID 1 & Driver ID 1 sudah ada (dari seed service lain)
        
        # Order 1: Selesai (DELIVERED)
        o1 = Order(user_id=1, total_price=30000, status='DELIVERED', driver_id=1)
        db.session.add(o1)
        db.session.commit() # Commit agar o1 dapat ID
        
        # Item untuk Order 1
        i1 = OrderItem(order_id=o1.id, menu_id=1, quantity=2, price_per_item=15000)
        db.session.add(i1)
        
        # Order 2: Sedang Berjalan (CONFIRMED)
        o2 = Order(user_id=1, total_price=45000, status='CONFIRMED', driver_id=2)
        db.session.add(o2)
        db.session.commit()
        
        i2 = OrderItem(order_id=o2.id, menu_id=2, quantity=1, price_per_item=25000)
        i3 = OrderItem(order_id=o2.id, menu_id=1, quantity=1, price_per_item=20000)
        db.session.add_all([i2, i3])
        
        db.session.commit()
        return jsonify({'message': 'Order database seeded with dummy data!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 4. Jalankan Aplikasi
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    
    app.run(host='0.0.0.0', port=5003, debug=True)