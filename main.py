from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS, cross_origin
from bson import json_util
import json

import os

from authlib.integrations.flask_oauth2 import ResourceProtector
from validator import Auth0JWTBearerTokenValidator

require_auth = ResourceProtector()
validator = Auth0JWTBearerTokenValidator(
    "dev-wth8xks0zqja4d1c.us.auth0.com",
    "shaormappFlask"
)
require_auth.register_token_validator(validator)

mongo_url = os.environ.get("DATABASE_URL", "mongodb+srv://wigleytrial:Aerht7pU7Xn8b11M@shaormappcluster.l7swt.mongodb.net/?retryWrites=true&w=majority&appName=shaormappCluster")
client = MongoClient(mongo_url)
db = client["sample_mflix"]
collection = db["movies"]
listaMeaDeFilme = collection.find().limit(25)

# creating the Flask application
app = Flask(__name__)
CORS(app)



@app.route('/', methods=['GET'])
def base():
    response = "macar un raspuns"
    return response
    

@app.route('/ceva', methods=['GET'])
@cross_origin()
@require_auth(None)
def ceva():
    response = json_util.dumps(listaMeaDeFilme), 201
    return response
    


@app.route('/altceva', methods=['GET'])
@cross_origin()
@require_auth(None)
def altceva():
    response = jsonify({"macar un raspuns": True}), 201
    return response
    

# Run the server
if __name__ == '__main__':
    app.run(debug=True, port=8069)

# @app.errorhandler(AuthError)
# def handle_auth_error(ex):
#     response = jsonify(ex.error)
#     response.status_code = ex.status_code
#     return response
