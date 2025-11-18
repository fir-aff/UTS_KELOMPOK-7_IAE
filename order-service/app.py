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
DRIVER_SERVICE_URL = "http://127.0.0.1:5004"

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
    order_items = []
    try:
        for item in items_data:
            resp = requests.get(f"{RESTAURANT_SERVICE_URL}/menu/{item['menu_id']}")
            if resp.status_code == 200:
                price = resp.json()['price']
                total_price += price * item['quantity']
                order_items.append(OrderItem(menu_id=item['menu_id'], quantity=item['quantity'], price_per_item=price))
    except: return jsonify({'error': 'Menu invalid'}), 503

    # 3. Simpan Order
    new_order = Order(user_id=user_id, total_price=total_price, status='PENDING')
    db.session.add(new_order); db.session.commit()
    
    for item in order_items:
        item.order_id = new_order.id
        db.session.add(item)
    db.session.commit()

    # 4. Panggil Driver
    try:
        requests.post(f"{DRIVER_SERVICE_URL}/drivers/request", json={"order_id": new_order.id})
    except: pass

    return jsonify({'message': 'Order created', 'order': {'order_id': new_order.id}}), 201

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

# ... (Tambahkan docstring serupa untuk endpoint status dan complete) ...
# ... (Pastikan endpoint health/seed tetap ada) ...

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=5003, debug=True)