import os
import jwt
import datetime
from flask import Flask, request, jsonify, send_file, render_template
from dotenv import load_dotenv
from core_engine import generate_pdf

load_dotenv()
app = Flask(__name__)
# Trên mây, nếu quên set JWT_SECRET_KEY, app sẽ dùng chuỗi mặc định này để không bị sập
app.config['SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-2026")

def verify_token(token):
    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        return decoded
    except Exception:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth', methods=['POST'])
def authenticate():
    data = request.json
    user_pin = data.get('pin', '')
    valid_pins = os.getenv("AUTHORIZED_PINS", "").split(",")
    
    if user_pin in valid_pins:
        token = jwt.encode({
            "pin": user_pin,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"status": "success", "token": token})
    
    return jsonify({"status": "error", "message": "Mã PIN không hợp lệ hoặc đã bị thu hồi"}), 401

@app.route('/api/generate', methods=['POST'])
def generate():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Truy cập bị từ chối. Thiếu Token."}), 401
    
    token = auth_header.split(" ")[1]
    user_data = verify_token(token)
    
    if not user_data:
        return jsonify({"error": "Phiên làm việc đã hết hạn. Vui lòng tải lại trang và nhập mã PIN."}), 401

    profile = request.json
    try:
        output_pdf_path = generate_pdf(profile)
        return send_file(output_pdf_path, as_attachment=True, download_name=f"BanDo_Pytago_{profile.get('ten', 'User')}.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)