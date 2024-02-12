from flask import Flask, render_template, jsonify, request
import psycopg2
import json
import traceback  # Import traceback module for detailed error information

app = Flask(__name__)

# Flask route to render the firstpage.html
@app.route('/')
def index():
    return render_template('firstpage.html')

# Flask route to fetch locations from the database
@app.route('/get_locations', methods=['POST'])
def get_locations():
    try:
        # Connect to PostgreSQL database using a with statement
        with psycopg2.connect(
                user="postgres",
                password="rvce1234",
                host="database-1.coccpvzcn43y.ap-southeast-1.rds.amazonaws.com",
                port=5432,
                database="postgres"
        ) as connection:
            # Create a cursor using a with statement
            with connection.cursor() as cursor:
                # Get table name from the form submission
                table_name = request.form.get('table_name')

                # Check if the table exists in the database
                cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)", (table_name,))
                table_exists = cursor.fetchone()[0]

                if not table_exists:
                    return jsonify({"error": f"Table '{table_name}' does not exist"}), 404

                # Fetch latitude, longitude, and timestamp from the database
                query = "SELECT latitude, longitude, timestamp FROM {}".format(table_name)
                cursor.execute(query)
                locations = cursor.fetchall()

        # Convert the locations to a list of dictionaries for JSON response
        locations_list = [{'latitude': lat, 'longitude': lon, 'timestamp': ts} for lat, lon, ts in locations]

        return jsonify(locations_list)

    except Exception as e:
        traceback.print_exc()  # Print detailed error information
        return jsonify({"error": "Internal Server Error"}), 500
# Flask route to handle form submission
@app.route('/map', methods=['GET', 'POST'])
def map():
    try:
        table_name = request.form.get('table_name')
        return render_template('map.html', table_name=table_name)
    except Exception as e:
        traceback.print_exc()  # Print detailed error information
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
