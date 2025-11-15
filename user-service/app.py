# user-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
# BARU: Impor library JWT
from flask_jwt_extended import create_access_token, JWTManager

# 1. Inisialisasi Aplikasi
app = Flask(__name__)
bcrypt = Bcrypt(app)

# BARU: Konfigurasi JWT
# Ganti ini dengan kunci rahasia Anda sendiri di dunia nyata
app.config["JWT_SECRET_KEY"] = "kunci-rahasia-EAI-anda-yang-aman" 
jwt = JWTManager(app)

# Konfigurasi Database (MySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/user_service_db'
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
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        address=data.get('address')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201

# Endpoint untuk login (DIUBAH UNTUK JWT)
@app.route('/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        # BARU: Buat token jika login berhasil
        # Token ini berisi 'identity' (identitas) user, yaitu ID-nya
        # Frontend akan menyimpan token ini
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token)
    
    return jsonify({'error': 'Invalid credentials'}), 401

# Endpoint untuk mendapatkan SEMUA user (untuk admin/user list)
@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint untuk mendapatkan data user (dipanggil oleh order-service)
@app.route('/users/<int:id>', methods=['GET'])
def get_user_by_id(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

# Endpoint untuk UPDATE user (untuk Admin)
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    data = request.get_json()
    
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
    
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.address = data.get('address', user.address)
    
    if 'password' in data and data['password']:
         user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    db.session.commit()
    return jsonify({'message': 'User updated', 'user': user.to_dict()}), 200

# Endpoint untuk DELETE user (untuk Admin)
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200

# Endpoint untuk Seeding Data Awal
@app.route('/debug/seed', methods=['POST'])
def seed_users():
    try:
        db.session.query(User).delete()
        
        user1 = User(
            name='Ratna (User)',
            email='ratna@gmail.com',
            password=bcrypt.generate_password_hash('password123').decode('utf-8'),
            address='Jalan Jendral Sudirman No. 1'
        )
        user2 = User(
            name='Irfan (Admin)',
            email='irfan@gmail.com',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            address='Jalan Thamrin No. 10'
        )
        db.session.add_all([user1, user2])
        db.session.commit()
        return jsonify({'message': 'User database seeded!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
    app.run(host='0.0.0.0', port=5001, debug=True)