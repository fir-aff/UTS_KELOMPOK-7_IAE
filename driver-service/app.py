# driver-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests # Untuk memanggil order-service
import os

# 1. Inisialisasi Aplikasi
app = Flask(__name__)

# Konfigurasi Database (MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/driver_service_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Definisikan URL layanan lain yang akan dipanggil
ORDER_SERVICE_URL = "http://127.0.0.1:5003"

# 2. Buat Model Database
class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Status bisa: 'available', 'on_trip'
    status = db.Column(db.String(50), nullable=False, default='available')

    def to_dict(self):
        return { 'id': self.id, 'name': self.name, 'status': self.status }

# 3. Buat Endpoint (Kontrak API)

# Endpoint HELPER untuk menambah driver baru (untuk testing)
@app.route('/drivers', methods=['POST'])
def create_driver():
    data = request.get_json()
    new_driver = Driver(name=data['name'], status='available')
    db.session.add(new_driver)
    db.session.commit()
    return jsonify({'message': 'Driver created', 'driver': new_driver.to_dict()}), 201

# Endpoint INTI: Mencari driver untuk pesanan baru
# Ini adalah endpoint 'PROVIDER' yang dipanggil oleh 'order-service'
@app.route('/drivers/request', methods=['POST'])
def find_driver_for_order():
    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({'error': 'Missing order_id'}), 400

    # === LANGKAH 1: Cari driver yang 'available' ===
    # Ini adalah simulasi sederhana. Kita ambil driver pertama yang available.
    available_driver = Driver.query.filter_by(status='available').first()

    if not available_driver:
        # Jika tidak ada driver, kirim error kembali ke order-service
        return jsonify({'error': 'No available drivers found'}), 404

    # === LANGKAH 2: Update status driver (di database ini) ===
    available_driver.status = 'on_trip'
    db.session.commit()
    app.logger.info(f"Driver {available_driver.name} assigned to order {order_id}")

    # === LANGKAH 3: Panggil balik order-service (Peran 'CONSUMER') ===
    # Memberi tahu 'order-service' bahwa pesanan sudah dikonfirmasi
    try:
        callback_url = f"{ORDER_SERVICE_URL}/orders/{order_id}/status"
        callback_payload = {
            "status": "CONFIRMED",
            "driver_id": available_driver.id
        }
        
        # Lakukan API call ke order-service
        response = requests.put(callback_url, json=callback_payload)
        response.raise_for_status() # Error jika status code bukan 2xx
        
        app.logger.info(f"Successfully updated order-service for order {order_id}")

    except requests.exceptions.RequestException as e:
        # JIKA GAGAL:
        # Ini masalah. Driver sudah kita 'booking', tapi order-service tidak tahu.
        # (Di dunia nyata, kita perlu mekanisme 'retry' atau 'rollback')
        # Untuk saat ini, kita kembalikan status driver ke 'available'
        available_driver.status = 'available'
        db.session.commit()
        app.logger.error(f"Failed to call order-service: {e}. Rolling back driver status.")
        # Kirim error kembali ke pemanggil (order-service)
        return jsonify({'error': f'Failed to confirm order with order-service: {e}'}), 503

    # === LANGKAH 4: Kirim response sukses kembali ke order-service ===
    return jsonify({
        'message': 'Driver assigned successfully',
        'driver_id': available_driver.id,
        'driver_name': available_driver.name
    }), 200


# 4. Jalankan Aplikasi
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
    # Jalankan di port 5004
    app.run(host='0.0.0.0', port=5004, debug=True)