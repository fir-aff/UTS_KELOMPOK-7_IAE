# user-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

# 1. Inisialisasi Aplikasi
app = Flask(__name__)
bcrypt = Bcrypt(app)

# Konfigurasi Database (SQLite, file akan bernama user.db)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'user.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 2. Buat Model Database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        # Fungsi ini penting untuk mengubah data User menjadi JSON
        # Jangan sertakan password dalam response
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'address': self.address
        }

# 3. Buat Endpoint (Kontrak API)

# Endpoint untuk registrasi user baru
@app.route('/users/register', methods=['POST'])
def register_user():
    data = request.get_json()
    
    # Cek apakah email sudah ada
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Hash password
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        address=data.get('address') # .get() agar tidak error jika address tidak ada
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201

# Endpoint untuk mendapatkan data user (PENTING untuk 'order-service')
# Ini adalah endpoint yang akan dikonsumsi oleh layanan lain.
@app.route('/users/<int:id>', methods=['GET'])
def get_user_by_id(id):
    user = User.query.get(id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify(user.to_dict()), 200

# Endpoint untuk login (akan kita gunakan nanti untuk JWT)
@app.route('/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        # Login berhasil
        # (Nanti kita akan ganti ini dengan JWT Token)
        return jsonify({'message': 'Login successful', 'user_id': user.id}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

# 4. Jalankan Aplikasi
if __name__ == '__main__':
    # Buat tabel database jika belum ada
    with app.app_context():
        db.create_all()
        
    # Jalankan di port 5001 (port non-default agar tidak bentrok)
    app.run(host='0.0.0.0', port=5001, debug=True)