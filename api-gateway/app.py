# api-gateway/app.py
from flask import Flask, request, Response
import requests
from flask_cors import CORS

app = Flask(__name__)
# Izinkan semua origin (domain) untuk mengakses /api/
# Ini akan memperbaiki error CORS di browser
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Definisikan alamat dasar dari semua layanan Anda
SERVICE_MAP = {
    "user-service": "http://127.0.0.1:5001",
    "restaurant-service": "http://127.0.0.1:5002",
    "order-service": "http://127.0.0.1:5003",
    "driver-service": "http://127.0.0.1:5004"
}

@app.route('/api/<string:service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_request(service_name, path):
    """
    Fungsi proxy generik.
    Akan mengambil /api/<service_name>/<path>
    dan meneruskannya ke http://<service_url>/<path>
    """
    
    # 1. Tentukan URL tujuan
    if service_name not in SERVICE_MAP:
        return "Service not found", 404
        
    target_url = f"{SERVICE_MAP[service_name]}/{path}"
    
    app.logger.info(f"Gateway forwarding: {request.method} {request.full_path} -> {target_url}")

    # 2. Dapatkan data dari request yang masuk
    # (termasuk query params seperti ?id=1)
    params = request.args
    headers = {key: value for (key, value) in request.headers if key != 'Host'}
    
    # Dapatkan body (JSON) jika ada
    data = request.get_data()
    
    # 3. Teruskan request ke layanan yang sesuai
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=data,
            params=params,
            allow_redirects=False,
            timeout=5 # Batas waktu 5 detik
        )
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to connect to service: {e}")
        return jsonify({"error": "Service unavailable", "service": service_name}), 503

    # 4. Buat dan kembalikan respons ke pengguna
    # Kita perlu menyalin header dan status code dari respons layanan
    
    # Daftar header yang tidak boleh disalin
    excluded_headers = ['content-encoding', 'transfer-encoding', 'connection']
    
    # Buat respons Flask
    response = Response(resp.content, resp.status_code)
    
    # Salin header yang relevan dari respons layanan
    for key, value in resp.headers.items():
        if key.lower() not in excluded_headers:
            response.headers[key] = value
            
    return response

@app.route('/health', methods=['GET'])
def gateway_health_check():
    # Cukup periksa apakah gateway itu sendiri berjalan
    return jsonify({'status': 'healthy', 'service': 'api-gateway'}), 200

@app.route('/')
def index():
    return "API Gateway is running! (v2.0 - Manual Proxy)"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)