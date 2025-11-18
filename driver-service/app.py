# driver-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from flasgger import Swagger # Import Swagger
import os

app = Flask(__name__)

# --- KONFIGURASI SWAGGER ---
swagger = Swagger(app, template={
    "info": {
        "title": "Driver Service API",
        "description": "API untuk manajemen Driver",
        "version": "1.0.0"
    }
})

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/driver_service_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ORDER_SERVICE_URL = "http://127.0.0.1:5003"

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='available')
    def to_dict(self): return { 'id': self.id, 'name': self.name, 'status': self.status }

# --- ENDPOINT ---

@app.route('/drivers', methods=['GET'])
def get_all_drivers():
    """
    Mendapatkan semua driver
    ---
    tags:
      - Driver
    responses:
      200:
        description: List semua driver
    """
    drivers = Driver.query.all()
    return jsonify([d.to_dict() for d in drivers]), 200

@app.route('/drivers', methods=['POST'])
def create_driver():
    """
    Mendaftarkan driver baru
    ---
    tags:
      - Driver
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: "Budi Supir"
    responses:
      201:
        description: Driver dibuat
    """
    data = request.get_json()
    new_driver = Driver(name=data['name'])
    db.session.add(new_driver); db.session.commit()
    return jsonify({'message': 'Created', 'driver': new_driver.to_dict()}), 201

@app.route('/drivers/<int:id>', methods=['PUT'])
def update_driver(id):
    """
    Update nama driver
    ---
    tags:
      - Driver
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            name:
              type: string
    responses:
      200:
        description: Driver di-update
    """
    driver = Driver.query.get(id)
    if not driver: return jsonify({'error': 'Not found'}), 404
    driver.name = request.json.get('name', driver.name)
    db.session.commit()
    return jsonify({'message': 'Driver created', 'driver': new_driver.to_dict()}), 201

# BARU: Endpoint untuk mendapatkan SEMUA driver (untuk Admin)
@app.route('/drivers', methods=['GET'])
def get_all_drivers():
    try:
        drivers = Driver.query.all()
        return jsonify([driver.to_dict() for driver in drivers]), 200
    except Exception as e:
        app.logger.error(f"Error getting all drivers: {e}")
        return jsonify({'error': str(e)}), 500
    
# Endpoint INTI: Mencari driver untuk pesanan baru
# Ini adalah endpoint 'PROVIDER' yang dipanggil oleh 'order-service'
@app.route('/drivers/request', methods=['POST'])
def find_driver_for_order():
    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({'error': 'Missing order_id'}), 400

    # === LANGKAH 1: Cari driver yang 'available' ===
    available_driver = Driver.query.filter_by(status='available').first()

    if not available_driver:
        return jsonify({'error': 'No available drivers found'}), 404

    # === LANGKAH 2: Update status driver (di database ini) ===
    available_driver.status = 'on_trip'
    db.session.commit()
    app.logger.info(f"Driver {available_driver.name} assigned to order {order_id}")

    # === LANGKAH 3: Panggil balik order-service (Peran 'CONSUMER') ===
    try:
        callback_url = f"{ORDER_SERVICE_URL}/orders/{order_id}/status"
        callback_payload = {
            "status": "CONFIRMED",
            "driver_id": available_driver.id
        }
        
        response = requests.put(callback_url, json=callback_payload)
        response.raise_for_status() # Error jika status code bukan 2xx
        
        app.logger.info(f"Successfully updated order-service for order {order_id}")

    except requests.exceptions.RequestException as e:
        available_driver.status = 'available'
        db.session.commit()
        app.logger.error(f"Failed to call order-service: {e}. Rolling back driver status.")
        return jsonify({'error': f'Failed to confirm order with order-service: {e}'}), 503

    # === LANGKAH 4: Kirim response sukses kembali ke order-service ===
    return jsonify({
        'message': 'Driver assigned successfully',
        'driver_id': available_driver.id,
        'driver_name': available_driver.name
    }), 200

# Endpoint untuk mengubah status driver secara manual (dipanggil oleh order-service)
@app.route('/drivers/<int:driver_id>/status', methods=['PUT'])
def update_driver_status(driver_id):
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404

    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ['available', 'on_trip']:
        return jsonify({'error': 'Invalid status value. Must be "available" or "on_trip"'}), 400

    driver.status = new_status
    db.session.commit()

    app.logger.info(f"Driver {driver.id} status updated to {new_status} by external request")
    return jsonify({'message': 'Driver status updated', 'driver': driver.to_dict()}), 200

# BARU: Endpoint untuk UPDATE driver (edit nama)
@app.route('/drivers/<int:driver_id>', methods=['PUT'])
def update_driver_details(driver_id):
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404

    data = request.get_json()
    driver.name = data.get('name', driver.name)
    # (status diubah oleh endpoint lain, jadi kita hanya update nama)

    db.session.commit()
    return jsonify({'message': 'Driver updated', 'driver': driver.to_dict()}), 200

# BARU: Endpoint untuk DELETE driver
@app.route('/drivers/<int:driver_id>', methods=['DELETE'])
def delete_driver(driver_id):
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404

    # Cek jika driver sedang 'on_trip'
    if driver.status == 'on_trip':
        return jsonify({'error': 'Cannot delete driver while on trip'}), 400

    db.session.delete(driver)
    db.session.commit()

    return jsonify({'message': 'Driver deleted'}), 200

@app.route('/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/debug/seed', methods=['POST'])
def seed_drivers():
    try:
        db.session.query(Driver).delete()
        db.session.add_all([Driver(name='Pak Budi'), Driver(name='Bu Siti'), Driver(name='Mas Anton')])
        db.session.commit()
        return jsonify({'message': 'Driver database seeded!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
    app.run(host='0.0.0.0', port=5004, debug=True)