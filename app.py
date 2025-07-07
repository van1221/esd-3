from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import uuid
import datetime
# from werkzeug.security import generate_password_hash, check_password_hash # For secure password handling in a real app
# from flask_socketio import SocketIO, emit # For real-time updates in a real app

app = Flask(__name__)
app.secret_key = 'YOUR_SECURE_SECRET_KEY_HERE' # !! REPLACE THIS WITH A LONG, RANDOM, AND SECURE KEY !!

# --- Simulated Database (In a real application, use a proper database like PostgreSQL, MySQL, MongoDB) ---
users = {} # Stores user information
charging_stations = { # Stores charging station data
    "station_001": {"name": "Green Charge Hub - Kolkata", "location": "Salt Lake Sector V, Kolkata", "latitude": 22.5726, "longitude": 88.3639, "total_ports": 8, "available_ports": 5, "cost_per_kwh": 0.25, "status": "online"},
    "station_002": {"name": "EcoCharge Point - Howrah", "location": "Howrah Station Road, Howrah", "latitude": 22.5872, "longitude": 88.3106, "total_ports": 4, "available_ports": 4, "cost_per_kwh": 0.30, "status": "online"},
    "station_003": {"name": "PowerUp Park - Rajarhat", "location": "New Town, Rajarhat, Kolkata", "latitude": 22.5726, "longitude": 88.4639, "total_ports": 6, "available_ports": 0, "cost_per_kwh": 0.28, "status": "busy"}
}
reservations = {} # Stores reservation details
transactions = {} # Stores payment transaction records

# --- Utility Functions ---
def generate_unique_id():
    return str(uuid.uuid4())

def hash_password(password):
    # In a real application, use a secure library like werkzeug.security.generate_password_hash
    return password # Placeholder

def check_password(hashed_password, password):
    # In a real application, use a secure library like werkzeug.security.check_password_hash
    return hashed_password == password # Placeholder

# --- Web Routes (for browser-based interaction) ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        for user_id_check, user_data_check in users.items():
            if user_data_check['username'] == username or user_data_check['email'] == email:
                return render_template('register.html', error='Username or Email already exists.')
        user_id = generate_unique_id()
        users[user_id] = {
            'username': username,
            'password_hash': hash_password(password),
            'email': email,
            'phone': '',
            'personalized_profile': {'preferred_charging_speed': 'fast', 'notification_email': True},
            'vehicles': []
        }
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for user_id, user_data in users.items():
            if user_data['username'] == username and check_password(user_data['password_hash'], password):
                session['user_id'] = user_id
                return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    user_data = users.get(user_id)
    return render_template('dashboard.html', user=user_data)

@app.route('/stations')
def view_stations():
    return render_template('stations.html', stations=charging_stations)

@app.route('/station/<station_id>')
def station_details(station_id):
    station = charging_stations.get(station_id)
    if not station:
        return "Station not found", 404
    return render_template('station_details.html', station=station)

@app.route('/reserve/<station_id>', methods=['GET', 'POST'])
def reserve_charging(station_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    station = charging_stations.get(station_id)
    if not station:
        return "Station not found", 404

    if request.method == 'POST':
        user_id = session['user_id']
        if station['available_ports'] > 0:
            reservation_id = generate_unique_id()
            reservations[reservation_id] = {
                'user_id': user_id,
                'station_id': station_id,
                'port_number': station['total_ports'] - station['available_ports'] + 1,
                'start_time': datetime.datetime.now().isoformat(),
                'end_time': '',
                'status': 'pending'
            }
            station['available_ports'] -= 1 # Simulate port occupation
            # In a real app, you would also notify mobile apps via WebSockets about availability change
            return redirect(url_for('my_reservations'))
        else:
            return render_template('reserve.html', station=station, error='No ports currently available.')
    return render_template('reserve.html', station=station)

@app.route('/my_reservations')
def my_reservations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    user_reservations = [res for res_id, res in reservations.items() if res['user_id'] == user_id]
    # Augment reservations with station names for display
    for res in user_reservations:
        res['station_name'] = charging_stations.get(res['station_id'], {}).get('name', 'Unknown Station')
    return render_template('my_reservations.html', reservations=user_reservations)

@app.route('/payment/<reservation_id>', methods=['GET', 'POST'])
def process_payment(reservation_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    reservation = reservations.get(reservation_id)
    if not reservation or reservation['user_id'] != session['user_id'] or reservation['status'] == 'completed':
        return "Reservation not found, not authorized, or already paid.", 404

    station = charging_stations.get(reservation['station_id'])
    if not station:
        return "Associated station not found.", 404

    # Placeholder for actual charging duration/kWh calculation
    estimated_amount = station['cost_per_kwh'] * 20 # Simulate 20 kWh charge

    if request.method == 'POST':
        # This is where you would integrate with a payment gateway (Stripe, Razorpay, etc.)
        # For demonstration, we'll simulate a successful payment.
        payment_token = request.form.get('payment_token') # In a real scenario, this would come from the client-side payment form
        if payment_token: # Simulate successful payment if token is present
            transaction_id = generate_unique_id()
            transactions[transaction_id] = {
                'user_id': session['user_id'],
                'reservation_id': reservation_id,
                'amount': estimated_amount,
                'status': 'completed',
                'timestamp': datetime.datetime.now().isoformat()
            }
            reservation['status'] = 'completed'
            # Restore port availability after charging session completion/payment
            station['available_ports'] += 1
            # In a real app, notify mobile apps via WebSockets about availability change
            return redirect(url_for('payment_success', transaction_id=transaction_id))
        else:
            return render_template('payment.html', reservation=reservation, estimated_amount=estimated_amount, error='Payment failed or cancelled.')

    return render_template('payment.html', reservation=reservation, estimated_amount=estimated_amount)

@app.route('/payment_success/<transaction_id>')
def payment_success(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    transaction = transactions.get(transaction_id)
    if not transaction or transaction['user_id'] != session['user_id'] or transaction['status'] != 'completed':
        return "Transaction not found or not authorized.", 404
    return render_template('payment_success.html', transaction=transaction)

@app.route('/profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    user_data = users.get(user_id)

    if request.method == 'POST':
        user_data['email'] = request.form.get('email', user_data['email'])
        user_data['phone'] = request.form.get('phone', user_data['phone'])
        user_data['personalized_profile']['preferred_charging_speed'] = request.form.get('preferred_charging_speed', user_data['personalized_profile'].get('preferred_charging_speed'))
        user_data['personalized_profile']['notification_email'] = 'notification_email' in request.form
        return redirect(url_for('user_profile'))
    return render_template('profile.html', user=user_data)

@app.route('/vehicles', methods=['GET', 'POST'])
def vehicle_details():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    user_data = users.get(user_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            vehicle_make = request.form['make']
            vehicle_model = request.form['model']
            vehicle_year = request.form['year']
            user_data['vehicles'].append({'make': vehicle_make, 'model': vehicle_model, 'year': vehicle_year})
        elif action == 'delete':
            vehicle_index = int(request.form['index'])
            if 0 <= vehicle_index < len(user_data['vehicles']):
                user_data['vehicles'].pop(vehicle_index)
        return redirect(url_for('vehicle_details'))
    return render_template('vehicles.html', vehicles=user_data['vehicles'])


# --- API Endpoints (for mobile apps and potentially dynamic web updates) ---

@app.route('/api/stations', methods=['GET'])
def api_get_stations():
    # Return a list of all stations with their current availability
    return jsonify(charging_stations)

@app.route('/api/station/<station_id>', methods=['GET'])
def api_get_station_details(station_id):
    station = charging_stations.get(station_id)
    if station:
        return jsonify(station)
    return jsonify({'error': 'Station not found'}), 404

@app.route('/api/reserve', methods=['POST'])
def api_create_reservation():
    # Mobile app sends user_id, station_id, desired_time (start, end)
    # In a real app, validate user token, check time slot availability
    data = request.json
    user_id = data.get('user_id') # In a real app, get from auth token
    station_id = data.get('station_id')
    
    if not user_id or not station_id:
        return jsonify({'error': 'Missing user_id or station_id'}), 400
    
    station = charging_stations.get(station_id)
    if not station or station['available_ports'] <= 0:
        return jsonify({'error': 'Station not found or no ports available'}), 400

    reservation_id = generate_unique_id()
    reservations[reservation_id] = {
        'user_id': user_id,
        'station_id': station_id,
        'port_number': station['total_ports'] - station['available_ports'] + 1,
        'start_time': datetime.datetime.now().isoformat(),
        'end_time': '',
        'status': 'pending'
    }
    station['available_ports'] -= 1
    # In a real app, emit WebSocket event to update all connected clients about station availability
    return jsonify({'message': 'Reservation created', 'reservation_id': reservation_id}), 201

@app.route('/api/user/reservations/<user_id>', methods=['GET'])
def api_get_user_reservations(user_id):
    # In a real app, validate user token matches user_id
    user_reservations = []
    for res_id, res in reservations.items():
        if res['user_id'] == user_id:
            res_copy = res.copy() # Avoid modifying original dict
            res_copy['station_name'] = charging_stations.get(res['station_id'], {}).get('name', 'Unknown Station')
            user_reservations.append(res_copy)
    return jsonify(user_reservations)

@app.route('/api/user/profile/<user_id>', methods=['GET'])
def api_get_user_profile(user_id):
    # In a real app, validate user token
    user_data = users.get(user_id)
    if user_data:
        # Avoid sending password hash
        profile_data = {k: v for k, v in user_data.items() if k != 'password_hash'}
        return jsonify(profile_data)
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/user/profile/<user_id>', methods=['PUT'])
def api_update_user_profile(user_id):
    # In a real app, validate user token
    user_data = users.get(user_id)
    if not user_data:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.json
    user_data['email'] = data.get('email', user_data['email'])
    user_data['phone'] = data.get('phone', user_data['phone'])
    user_data['personalized_profile']['preferred_charging_speed'] = data.get('preferred_charging_speed', user_data['personalized_profile'].get('preferred_charging_speed'))
    user_data['personalized_profile']['notification_email'] = data.get('notification_email', user_data['personalized_profile'].get('notification_email'))
    
    return jsonify({'message': 'Profile updated successfully', 'profile': user_data}), 200

# Placeholder for payment API - actual integration is complex
@app.route('/api/process_payment', methods=['POST'])
def api_process_payment():
    data = request.json
    reservation_id = data.get('reservation_id')
    amount = data.get('amount')
    payment_method_details = data.get('payment_method_details') # e.g., token from Stripe SDK
    user_id = data.get('user_id') # From auth token in real app

    if not reservation_id or not amount or not payment_method_details or not user_id:
        return jsonify({'error': 'Missing payment details'}), 400

    # In a real app, call payment gateway API here
    # Example: stripe.Charge.create(amount=amount, currency='usd', source=payment_method_details['token'])
    
    # Simulate success
    transaction_id = generate_unique_id()
    transactions[transaction_id] = {
        'user_id': user_id,
        'reservation_id': reservation_id,
        'amount': amount,
        'status': 'completed',
        'timestamp': datetime.datetime.now().isoformat()
    }
    # Update reservation and station availability
    if reservation_id in reservations:
        reservations[reservation_id]['status'] = 'completed'
        station_id = reservations[reservation_id]['station_id']
        if station_id in charging_stations:
            charging_stations[station_id]['available_ports'] += 1 # Free up port
            # Emit WebSocket event for real-time update
    
    return jsonify({'message': 'Payment processed successfully', 'transaction_id': transaction_id}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) # Listen on all interfaces
