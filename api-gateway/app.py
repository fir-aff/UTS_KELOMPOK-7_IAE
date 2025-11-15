# api-gateway/app.py
from flask import Flask, request, Response, jsonify
import requests
from flask_cors import CORS # BARU: Impor CORS

app = Flask(__name__)

# BARU: Terapkan CORS untuk semua rute /api/
# Ini mengizinkan browser Anda (frontend) untuk memanggil gateway
# Allow Authorization header and credentials so browser can send JWTs
CORS(app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"])

# Definisikan alamat dasar dari semua layanan Anda
SERVICE_MAP = {
    "user-service": "http://127.0.0.1:5001",
    "restaurant-service": "http://127.0.0.1:5002",
    "order-service": "http://127.0.0.1:5003",
    "driver-service": "http://127.0.0.1:5004"
}

@app.route('/api/<string:service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_request(service_name, path):
    if service_name not in SERVICE_MAP:
        return "Service not found", 404

    target_url = f"{SERVICE_MAP[service_name]}/{path}"
    app.logger.info(f"Gateway forwarding: {request.method} {request.full_path} -> {target_url}")

    params = request.args
    headers = {key: value for (key, value) in request.headers if key != 'Host'}
    data = request.get_data()

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=data,
            params=params,
            allow_redirects=False,
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to connect to service: {e}")
        return jsonify({"error": "Service unavailable", "service": service_name}), 503

    excluded_headers = ['content-encoding', 'transfer-encoding', 'connection']
    response = Response(resp.content, resp.status_code)

    for key, value in resp.headers.items():
        if key.lower() not in excluded_headers:
            response.headers[key] = value

    return response

@app.route('/')
def index():
    return "API Gateway is running! (v2.0 - Manual Proxy with CORS)"

# Endpoint Health Check
@app.route('/health', methods=['GET'])
def gateway_health_check():
    return jsonify({'status': 'healthy', 'service': 'api-gateway'}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)