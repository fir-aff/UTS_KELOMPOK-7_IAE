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
    return jsonify({'message': 'Updated'}), 200

@app.route('/drivers/<int:id>', methods=['DELETE'])
def delete_driver(id):
    """
    Hapus driver
    ---
    tags:
      - Driver
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Driver dihapus
      400:
        description: Gagal hapus (Driver sedang on_trip)
    """
    driver = Driver.query.get(id)
    if not driver: return jsonify({'error': 'Not found'}), 404
    if driver.status == 'on_trip': return jsonify({'error': 'Cannot delete busy driver'}), 400
    db.session.delete(driver); db.session.commit()
    return jsonify({'message': 'Deleted'}), 200

@app.route('/drivers/<int:id>/status', methods=['PUT'])
def update_status(id):
    """
    Update status driver (Internal/Admin)
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
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              enum: ['available', 'on_trip']
    responses:
      200:
        description: Status di-update
    """
    driver = Driver.query.get(id)
    if driver:
        driver.status = request.json.get('status')
        db.session.commit()
    return jsonify({'message': 'Status updated'}), 200

@app.route('/drivers/request', methods=['POST'])
def find_driver():
    """
    Mencari driver untuk pesanan (Internal)
    ---
    tags:
      - Internal Logic
    description: Endpoint ini dipanggil oleh Order Service untuk mencari driver available
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            order_id:
              type: integer
    responses:
      200:
        description: Driver ditemukan dan di-assign
      404:
        description: Tidak ada driver available
    """
    order_id = request.json.get('order_id')
    driver = Driver.query.filter_by(status='available').first()
    if driver:
        driver.status = 'on_trip'
        db.session.commit()
        try:
            requests.put(f"{ORDER_SERVICE_URL}/orders/{order_id}/status", json={"status": "CONFIRMED", "driver_id": driver.id})
        except: 
            driver.status = 'available' # Rollback if call fails
            db.session.commit()
            return jsonify({'error': 'Failed to contact order service'}), 503
        return jsonify({'message': 'Driver assigned', 'driver_id': driver.id}), 200
    return jsonify({'error': 'No drivers available'}), 404

# --- HEALTH & SEED ---

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
    with app.app_context(): db.create_all()
    app.run(host='0.0.0.0', port=5004, debug=True)