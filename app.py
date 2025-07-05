from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from datetime import datetime

from config import Config
from services.database_service import DatabaseService
from services.chatbot_service import ChatbotService
from services.auth_service import AuthService

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
CORS(app)
redis_client = redis.from_url(Config.REDIS_URL)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri=Config.RATELIMIT_STORAGE_URL
)

# Initialize services
db_service = DatabaseService()
chatbot_service = ChatbotService()

@app.route('/')
def home():
    """Home page"""
    user_info = session.get('user_info')
    return render_template('index.html', 
                         user=user_info, 
                         authenticated=bool(user_info))

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Authenticate user"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        account_number = data.get('account_number', '').strip()
        auth_code = data.get('auth_code', '').strip()
        
        if not all([name, account_number, auth_code]):
            return jsonify({'error': 'All fields are required'}), 400
        
        user = db_service.authenticate_user(name, account_number, auth_code)
        if user:
            token = user.generate_token()
            session['token'] = token
            session['user_info'] = {
                'name': user.name,
                'account_number': user.account_number,
                'balance': user.balance
            }
            
            return jsonify({
                'success': True,
                'message': 'Authentication successful',
                'token': token,
                'user': session['user_info']
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/chat', methods=['POST'])
@AuthService.token_required
@limiter.limit("20 per minute")
def chat():
    """Process chat message"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        user_info = session.get('user_info')
        response = chatbot_service.process_query(message, user_info['name'])
        
        # Handle different intents
        if response['intent'] == 'GET_BALANCE':
            account_number = response.get('account_number') or user_info['account_number']
            user = db_service.get_user_by_account(account_number)
            if user:
                response['data'] = {
                    'balance': user.balance,
                    'account_number': user.account_number,
                    'name': user.name
                }
                response['message'] = f"Account balance for {user.name}: ${user.balance:.2f}"
            else:
                response['message'] = "Account not found"
        
        elif response['intent'] == 'TRANSFER_MONEY':
            # Return transfer confirmation data
            response['requires_confirmation'] = True
            response['transfer_data'] = {
                'to_account': response.get('account_number'),
                'amount': response.get('amount', 0)
            }
        
        elif response['intent'] == 'ACCOUNT_INFO':
            user = db_service.get_user_by_account(user_info['account_number'])
            if user:
                response['data'] = user.to_dict()
                response['message'] = f"Account Information:\nName: {user.name}\nAccount: {user.account_number}\nBalance: ${user.balance:.2f}"
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': 'Failed to process message'}), 500

@app.route('/api/transfer/confirm', methods=['POST'])
@AuthService.token_required
@limiter.limit("10 per minute")
def confirm_transfer():
    """Confirm money transfer"""
    try:
        data = request.get_json()
        to_account = data.get('to_account', '').strip()
        amount = float(data.get('amount', 0))
        
        user_info = session.get('user_info')
        from_account = user_info['account_number']
        
        success, message = db_service.transfer_money(from_account, to_account, amount)
        
        if success:
            # Update session with new balance
            updated_user = db_service.get_user_by_account(from_account)
            session['user_info']['balance'] = updated_user.balance
            
            return jsonify({
                'success': True,
                'message': message,
                'new_balance': updated_user.balance
            })
        else:
            return jsonify({'error': message}), 400
            
    except ValueError:
        return jsonify({'error': 'Invalid amount'}), 400
    except Exception as e:
        return jsonify({'error': 'Transfer failed'}), 500

@app.route('/api/user/<account_number>')
@AuthService.token_required
def get_user_info(account_number):
    """Get user information by account number"""
    user = db_service.get_user_by_account(account_number)
    if user:
        return jsonify({
            'name': user.name,
            'account_number': user.account_number,
            'balance': user.balance
        })
    return jsonify({'error': 'User not found'}), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)