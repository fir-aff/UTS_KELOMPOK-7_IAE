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

@app.route('/users/<int:id>', methods=['GET'])
def get_user_by_id(id):
    """
    Get user by ID
    ---
    tags:
      - User Management
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200: {description: User found}
      404: {description: User not found}
    """
    user = User.query.get(id)
    if not user: return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    """
    Get all users
    ---
    tags:
      - User Management
    responses:
      200: {description: List of users}
    """
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

# --- INI YANG KEMARIN HILANG (PUT & DELETE) ---

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    """
    Update data user
    ---
    tags:
      - User Management
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
            name: {type: string}
            email: {type: string}
            address: {type: string}
    responses:
      200: {description: User updated}
      404: {description: User not found}
    """
    user = User.query.get(id)
    if not user: return jsonify({'error': 'User not found'}), 404
    data = request.get_json()
    
    # Cek email duplikat jika email diubah
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

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    """
    Hapus user
    ---
    tags:
      - User Management
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200: {description: User deleted}
      404: {description: User not found}
    """
    user = User.query.get(id)
    if not user: return jsonify({'error': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200

# --- SYSTEM ENDPOINTS ---

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health Check
    ---
    tags:
      - System
    responses:
      200: {description: OK}
    """
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

@app.route('/debug/seed', methods=['POST'])
def seed_users():
    """
    Reset & Seed Database
    ---
    tags:
      - System
    responses:
      201: {description: Seeded}
    """
    try:
        db.session.query(User).delete()
        user1 = User(name='Ratna User', email='ratna@gmail.com', password=bcrypt.generate_password_hash('password123').decode('utf-8'), address='Jl. Mawar No 1')
        user2 = User(name='Budi Admin', email='budi@gmail.com', password=bcrypt.generate_password_hash('admin123').decode('utf-8'), address='Jl. Melati No 2')
        db.session.add_all([user1, user2])
        db.session.commit()
        return jsonify({'message': 'User database seeded!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)