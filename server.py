from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# ملف قاعدة البيانات
DB_FILE = 'licenses.json'
API_SECRET = os.environ.get('API_SECRET', 'change_me_in_production')

def load_licenses():
    """تحميل التراخيص من الملف"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_licenses(data):
    """حفظ التراخيص في الملف"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

@app.route('/')
def home():
    """الصفحة الرئيسية - للتأكد أن السيرفر شغال"""
    return jsonify({
        'status': 'running',
        'message': 'POS License Server is running',
        'version': '1.0'
    })

@app.route('/health')
def health():
    """فحص صحة السيرفر"""
    return jsonify({'status': 'healthy'})

@app.route('/verify', methods=['POST'])
def verify_license():
    """التحقق من صلاحية الترخيص"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'valid': False, 'error': 'No data provided'}), 400
        
        license_key = data.get('license_key')
        if not license_key:
            return jsonify({'valid': False, 'error': 'No license key'}), 400
        
        licenses = load_licenses()
        
        if license_key in licenses:
            license_info = licenses[license_key]
            
            try:
                expiry = datetime.strptime(license_info['expiry_date'], '%Y-%m-%d')
            except:
                return jsonify({'valid': False, 'error': 'Invalid date format'}), 400
            
            if datetime.now() <= expiry and license_info.get('status') == 'active':
                # تحديث آخر استخدام
                licenses[license_key]['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_licenses(licenses)
                
                return jsonify({
                    'valid': True,
                    'customer_name': license_info.get('customer_name', 'Unknown'),
                    'expiry_date': license_info['expiry_date']
                })
        
        return jsonify({'valid': False})
    
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500

@app.route('/add_license', methods=['POST'])
def add_license():
    """إضافة ترخيص جديد"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        if data.get('api_secret') != API_SECRET:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        required_fields = ['license_key', 'customer_name', 'expiry_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing {field}'}), 400
        
        licenses = load_licenses()
        licenses[data['license_key']] = {
            'customer_name': data['customer_name'],
            'expiry_date': data['expiry_date'],
            'status': 'active',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_used': None
        }
        
        if save_licenses(licenses):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update_license', methods=['POST'])
def update_license():
    """تحديث ترخيص موجود"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        if data.get('api_secret') != API_SECRET:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        licenses = load_licenses()
        
        if data['license_key'] in licenses:
            licenses[data['license_key']].update({
                'customer_name': data.get('customer_name', licenses[data['license_key']]['customer_name']),
                'expiry_date': data.get('expiry_date', licenses[data['license_key']]['expiry_date']),
                'status': data.get('status', licenses[data['license_key']]['status'])
            })
            
            if save_licenses(licenses):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to save'}), 500
        
        return jsonify({'success': False, 'error': 'License not found'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_licenses', methods=['POST'])
def get_licenses():
    """الحصول على جميع التراخيص"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        if data.get('api_secret') != API_SECRET:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        return jsonify(load_licenses())
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
