# order-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from flasgger import Swagger
import os

app = Flask(__name__)

# --- KONFIGURASI SWAGGER ---
swagger = Swagger(app, template={
    "info": {
        "title": "Order Service API (Non-JWT)",
        "description": "API untuk manajemen Pesanan",
        "version": "1.0.0"
    }
})

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/order_service_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# URL Service
USER_SERVICE_URL = "http://127.0.0.1:5001"
RESTAURANT_SERVICE_URL = "http://127.0.0.1:5002"
DRIVER_SERVICE_URL = "http://127.0.0.1:5004"

# 2. Buat Model Database
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='PENDING')
    driver_id = db.Column(db.Integer, nullable=True) 
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    menu_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_item = db.Column(db.Float, nullable=False)

# 3. Buat Endpoint

@app.route('/orders', methods=['POST'])
def create_order():
    """
    Membuat pesanan baru
    ---
    tags: [Orders]
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id: {type: integer, example: 1}
            items:
              type: array
              items:
                type: object
                properties:
                  menu_id: {type: integer, example: 1}
                  quantity: {type: integer, example: 2}
    responses:
      201: {description: Pesanan berhasil dibuat}
      503: {description: Service lain (User/Resto) tidak terhubung}
    """
    data = request.get_json()
    user_id = data.get('user_id') # Mengambil user_id dari body
    items_data = data.get('items')

    if not user_id or not items_data:
        return jsonify({'error': 'Missing user_id or items'}), 400

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
            restaurant_address = "Jalan Padang No. 10" # Asumsi

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


# Endpoint riwayat pesanan (Versi NON-JWT)
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    """
    Melihat riwayat pesanan User
    ---
    tags: [Orders]
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
    responses:
      200: {description: List pesanan user}
      404: {description: User tidak punya pesanan}
    """
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
    """
    Get semua order (Admin)
    ---
    tags: [Orders (Admin)]
    responses:
      200: {description: List semua order}
    """
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

# Endpoint Callback dari driver-service
@app.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """
    Update status order (Dipanggil Driver Service)
    ---
    tags: [Internal]
    parameters:
      - name: order_id
        in: path
        type: integer
      - name: body
        in: body
        schema:
          type: object
          properties:
            status: {type: string}
            driver_id: {type: integer}
    responses:
      200: {description: Status diupdate}
    """
    order = Order.query.get(order_id)
    if not order: return jsonify({'error': 'Order not found'}), 404
    data = request.get_json()
    order.status = data.get('status', order.status)
    order.driver_id = data.get('driver_id', order.driver_id)
    db.session.commit()
    return jsonify({'message': 'Order status updated'}), 200

# Endpoint untuk Selesaikan Pesanan
@app.route('/orders/<int:order_id>/complete', methods=['PUT'])
def complete_order(order_id):
    """
    Menyelesaikan pesanan (Dipanggil Frontend)
    ---
    tags: [Orders]
    parameters:
      - name: order_id
        in: path
        type: integer
    responses:
      200: {description: Order selesai, driver dibebaskan}
    """
    order = Order.query.get(order_id)
    if not order: return jsonify({'error': 'Order not found'}), 404
    
    order.status = 'DELIVERED'
    db.session.commit()
    app.logger.info(f"Order {order.id} status updated to DELIVERED")
    
    if order.driver_id:
        try:
            requests.put(f"{DRIVER_SERVICE_URL}/drivers/{order.driver_id}/status", json={"status": "available"})
            app.logger.info(f"Successfully called driver-service to release driver {order.driver_id}")
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Failed to call driver-service: {e}")

    return jsonify({'message': 'Order completed and driver released'}), 200

# Endpoint Health Check
@app.route('/health', methods=['GET'])
def health_check():
    """
    Health Check
    ---
    tags: [System]
    responses:
      200: {description: OK}
    """
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

# Endpoint Seeding
@app.route('/debug/seed', methods=['POST'])
def seed_orders():
    """
    Reset & Seed Database
    ---
    tags: [System]
    responses:
      201: {description: Seeded}
    """
    try:
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        
        # Asumsi User ID 1 & Driver ID 1 ada
        o1 = Order(user_id=1, total_price=30000, status='DELIVERED', driver_id=1)
        db.session.add(o1); db.session.commit()
        db.session.add(OrderItem(order_id=o1.id, menu_id=1, quantity=2, price_per_item=15000))
        
        o2 = Order(user_id=1, total_price=25000, status='CONFIRMED', driver_id=2)
        db.session.add(o2); db.session.commit()
        db.session.add(OrderItem(order_id=o2.id, menu_id=2, quantity=1, price_per_item=25000))

        db.session.commit()
        return jsonify({'message': 'Order database seeded!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 4. Jalankan Aplikasi
if __name__ == '__main__':
    with app.app_context(): db.create_all() 
    app.run(host='0.0.0.0', port=5003, debug=True)