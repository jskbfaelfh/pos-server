from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# ملف قاعدة البيانات
DB_FILE = 'licenses.json'
API_SECRET = os.environ.get('API_SECRET', 'change_me_in_production')

def load_licenses():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_licenses(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/verify', methods=['POST'])
def verify_license():
    data = request.json
    license_key = data.get('license_key')
    
    licenses = load_licenses()
    
    if license_key in licenses:
        license_info = licenses[license_key]
        expiry = datetime.strptime(license_info['expiry_date'], '%Y-%m-%d')
        
        if datetime.now() <= expiry and license_info['status'] == 'active':
            # تحديث آخر استخدام
            licenses[license_key]['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_licenses(licenses)
            
            return jsonify({
                'valid': True,
                'customer_name': license_info['customer_name'],
                'expiry_date': license_info['expiry_date']
            })
    
    return jsonify({'valid': False})

@app.route('/add_license', methods=['POST'])
def add_license():
    data = request.json
    
    if data.get('api_secret') != API_SECRET:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    licenses = load_licenses()
    licenses[data['license_key']] = {
        'customer_name': data['customer_name'],
        'expiry_date': data['expiry_date'],
        'status': 'active',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_used': None
    }
    save_licenses(licenses)
    
    return jsonify({'success': True})

@app.route('/update_license', methods=['POST'])
def update_license():
    data = request.json
    
    if data.get('api_secret') != API_SECRET:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    licenses = load_licenses()
    
    if data['license_key'] in licenses:
        licenses[data['license_key']].update({
            'customer_name': data['customer_name'],
            'expiry_date': data['expiry_date'],
            'status': data['status']
        })
        save_licenses(licenses)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'License not found'})

@app.route('/get_licenses', methods=['POST'])
def get_licenses():
    data = request.json
    
    if data.get('api_secret') != API_SECRET:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    return jsonify(load_licenses())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))