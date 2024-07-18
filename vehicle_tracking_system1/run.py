from flask import Flask, render_template, jsonify, request , redirect, url_for


app = Flask(__name__)


# Registering Blueprint
from routes.admin import admin_view



# connects the blueprint with the main application
app.register_blueprint(admin_view)


# Code routing to home page on / present in routes/admin.py
@app.route('/', methods=['GET'])
def home():
	return redirect( url_for('admin_routes.home'))



if __name__ == '__main__':
    app.run(debug=True)
