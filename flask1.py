from flask import Flask, jsonify,request
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import traceback
app = Flask(__name__)

client = MongoClient('mongodb+srv://israa:NutriTrack-123@cluster0.ff8mp.mongodb.net/')
db = client["NutriTrack"]
user_collection = db['USER']
meal_collection = db['MEALS']

@app.route("/")
def index():
    return '<h1>Hello, world!</h1>'

@app.route("/signup", methods = ['POST'])
def signup():
    try: 
        data = request.get_json()
        if not data:
            return jsonify({"error":"Invalid input"}),400
        username = data.get("username")
        password = data.get("password")
        gender = data.get("gender")
        fisrt_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        age = data.get("age")
        weight = data.get("weight")
        height = data.get("height")
        goal = data.get("goal")

        if not username or not password or not email: 
            return jsonify({"error":"Username, password, email are required"}),400


        if user_collection.find_one({'username':username}):
            return jsonify({"error":"user already exists"}),400
        user_collection.insert_one({
             "username": username,
              "fisrt_name" : fisrt_name,
              "last_name" : last_name , 
              "email" : email,
              "password": password,
              "age": age,
              "gender": gender,
              "weight": weight,
              "height": height,
              "goal": goal
         }) 
        return jsonify({"message": "user created successfly"}),201
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error":str(e)}),500

@app.route("/login", methods = ['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error":"Invalid input"}),400
        username = data.get('username')
        password = data.get('password')
        if not username or not password: 
            return jsonify({"error":"Username and password are required"}),400


        user = user_collection.find_one({'username':username})

        if not user:
            return jsonify({"user not found"}),404

        if not user['password'] == password:
            return jsonify({"message":"invalid password"}),401
        
        return jsonify ({"message":"login successfully"}),200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error":str(e)}),500
    
@app.route("/meals", methods = ['GET'])
def get_meals():
    try:
        meals = list(meal_collection.find({}, {"_id": 0 }))
        return jsonify({"meals":meals}),200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error":"An error occurred"})


if __name__ =='__main__':
     app.run(debug = True)