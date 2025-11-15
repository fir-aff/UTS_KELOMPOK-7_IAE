# api-gateway/app.py
from flask import Flask, request, Response, jsonify
import requests
from flask_cors import CORS 

app = Flask(__name__)

# Terapkan CORS untuk SEMUA rute /api/
# Ini PENTING untuk JWT
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Definisikan alamat dasar dari semua layanan Anda
SERVICE_MAP = {
    "user-service": "http://127.0.0.1:5001",
    "restaurant-service": "http://127.0.0.1:5002",
    "order-service": "http://127.0.0.1:5003",
    "driver-service": "http://127.0.0.1:5004"
}

# Tambahkan 'OPTIONS' ke daftar methods
@app.route('/api/<string:service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy_request(service_name, path):
    """
    Fungsi proxy generik.
    """
    
    # Blok untuk menangani CORS Preflight (request OPTIONS)
    if request.method == 'OPTIONS':
        response = jsonify({"message": "CORS preflight successful"})
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization") 
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        return response

    # 1. Tentukan URL tujuan
    if service_name not in SERVICE_MAP:
        return "Service not found", 404
        
    target_url = f"{SERVICE_MAP[service_name]}/{path}"
    
    app.logger.info(f"Gateway forwarding: {request.method} {request.full_path} -> {target_url}")

    # 2. Dapatkan data dari request yang masuk
    params = request.args
    # Salin SEMUA header dari request asli (termasuk 'Authorization')
    headers = {key: value for (key, value) in request.headers if key != 'Host'}
    
    data = request.get_data()
    
    # 3. Teruskan request ke layanan yang sesuai
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers, # headers yang disalin akan diteruskan ke layanan
            data=data,
            params=params,
            allow_redirects=False,
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to connect to service: {e}")
        return jsonify({"error": "Service unavailable", "service": service_name}), 503

    # 4. Buat dan kembalikan respons ke pengguna
    excluded_headers = ['content-encoding', 'transfer-encoding', 'connection']
    response = Response(resp.content, resp.status_code)
    
    for key, value in resp.headers.items():
        if key.lower() not in excluded_headers:
            response.headers[key] = value
            
    return response


@app.route('/')
def index():
    return "API Gateway is running! (v2.0 - Manual Proxy, CORS Enabled)"

# Endpoint Health Check
@app.route('/health', methods=['GET'])
def gateway_health_check():
    return jsonify({'status': 'healthy', 'service': 'api-gateway'}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)