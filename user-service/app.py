# user-service/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flasgger import Swagger

app = Flask(__name__)

# --- KONFIGURASI SWAGGER ---
swagger = Swagger(app, template={
    "info": {
        "title": "User Service API",
        "description": "Dokumentasi Lengkap API User Service (CRUD)",
        "version": "1.0.0"
    }
})

bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/user_service_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email, 'address': self.address}

# --- ENDPOINTS ---

@app.route('/users/register', methods=['POST'])
def register_user():
    """
    Mendaftarkan pengguna baru
    ---
    tags:
      - User Management
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [name, email, password]
          properties:
            name: {type: string, example: "Budi"}
            email: {type: string, example: "budi@email.com"}
            password: {type: string, example: "pass123"}
            address: {type: string, example: "Jakarta"}
    responses:
      201: {description: User created}
      400: {description: Email exists}
    """
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first(): return jsonify({'error': 'Email already exists'}), 400
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(name=data['name'], email=data['email'], password=hashed_password, address=data.get('address'))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201

# BARU: Endpoint untuk CREATE user (untuk Admin)
@app.route('/users', methods=['POST'])
def create_user_by_admin():
    data = request.get_json()
    
    # Cek apakah data minimal ada
    if not data or not 'email' in data or not 'name' in data:
        return jsonify({'error': 'Missing required data: name and email'}), 400

    # Cek apakah email sudah ada
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Buat password default untuk user baru
    # Anda bisa ganti 'password123' dengan yang lain
    hashed_password = bcrypt.generate_password_hash('password').decode('utf-8')
    
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        address=data.get('address')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created by admin', 'user': new_user.to_dict()}), 201

# BARU: Endpoint untuk mendapatkan SEMUA user (untuk dropdown)
@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    """
    Login pengguna
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email: {type: string, example: "budi@email.com"}
            password: {type: string, example: "pass123"}
    responses:
      200: {description: Login success}
      401: {description: Invalid credentials}
    """
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

# BARU: Endpoint untuk UPDATE user (untuk Admin)
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    # Cek jika email baru sudah dipakai user lain
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

    # Update data
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.address = data.get('address', user.address)

    # (Opsional: Update password jika ada)
    if 'password' in data and data['password']: # Cek jika password tidak kosong
         user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    db.session.commit()
    return jsonify({'message': 'User updated', 'user': user.to_dict()}), 200

# BARU: Endpoint untuk DELETE user (untuk Admin)
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # (Tambahan: Kita harus cek/menghapus order terkait user ini,
    # tapi untuk sekarang kita hapus langsung)

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted'}), 200

@app.route('/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 503

@app.route('/debug/seed', methods=['POST'])
def seed_users():
    try:
        db.session.query(User).delete()
        # Buat 2 user default
        u1 = User(name='Ratna User', email='ratna@gmail.com', password=bcrypt.generate_password_hash('password123').decode('utf-8'), address='Jl. Mawar No 1')
        u2 = User(name='Budi Admin', email='budi@gmail.com', password=bcrypt.generate_password_hash('admin123').decode('utf-8'), address='Jl. Melati No 2')
        db.session.add_all([u1, u2])
        db.session.commit()
        return jsonify({'message': 'User database seeded!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
# 4. Jalankan Aplikasi
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)