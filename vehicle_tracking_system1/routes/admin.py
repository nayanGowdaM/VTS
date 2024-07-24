from flask import Blueprint, render_template, redirect
from flask import jsonify, request
import traceback
import psycopg2
from utils.utils import convert_jsonb_to_list, auth


admin_view = Blueprint('admin_routes', __name__, template_folder='../templates')  

@admin_view.route('/')
def home():
    # return render_template('home.html')
    return render_template('home.html')

@admin_view.route('/firstpage')
def firstpage():
    # return render_template('home.html')
    return render_template('firstpage.html')


@admin_view.route('/login', methods=['GET','POST'])
def login():
	if request.method == 'POST':
		_form = request.form
		username = str(_form["username"])
		password = str(_form["password"])

		if len(username)<1 or len(password)<1:
			return render_template('login.html', error="Email and password are required")
		
        
        # d = user_manager.signin(email, hash(password))

		if auth( username, password):
			return redirect("/firstpage")
        

		return render_template('login.html', error="Email or password incorrect")


	return render_template('login.html')



@admin_view.route('/get_locations', methods=['POST'])
def get_locations():
    try:
        # Connect to PostgreSQL database
        with psycopg2.connect(
                user="postgres",
                password="rvce1234",
                host="database-1.cnco44k2w5r9.ap-south-1.rds.amazonaws.com",
                port=5432,
                database="postgres"
        ) as connection:
            with connection.cursor() as cursor:
                vehicle_id = request.form.get('vehicle_id')
                date = request.form.get('date')
                # Using .format() to dynamically inject table name and date into the query
                query = "SELECT location_data FROM {} WHERE date = '{}'".format(vehicle_id, date)
                cursor.execute(query)
                records = cursor.fetchall()
                converted_data = convert_jsonb_to_list(records[0])
        return jsonify(converted_data)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Internal Server Error"}), 500



@admin_view.route('/map', methods=['GET', 'POST'])
def map():
    try:
        vehicle_id = request.form.get('vehicle_id')
        return render_template('map.html', vehicle_id=vehicle_id)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Internal Server Error"}), 500
