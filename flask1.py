from flask import Flask, jsonify,request
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import traceback
import cohere
import random

app = Flask(__name__)

client = MongoClient('mongodb+srv://israa:NutriTrack-123@cluster0.ff8mp.mongodb.net/')
db = client["NutriTrack"]
user_collection = db['USER']
meal_collection = db['MEALS']
plan_collection = db['PLAN']
api_key = "dT6zyIAY3MMPNZttCZAkYN0fiJJShRIUKeZupjYk"

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
    

def get_meals_list ():
    meals = meal_collection.find()
    meal_list = [meal for meal in meals]
    return meal_list

@app.route("/meals", methods = ['GET'])
def get_meals():
    try:
        meal_list = get_meals_list()
        return jsonify({"meals":meal_list}),200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error":"An error occurred"})

@app.route("/plan", methods = ["GET"])
def get_plan_goal_day():
    try:

        plans = plan_collection.find()
        plan_list = [plan for plan in plans]
        meal_list = get_meals_list()

        meal_lookup = {str(meal['_id']): meal for meal in meal_list}

        for plan in plan_list:
            for day in plan.get('Days', []):
                for meal_category in day.get('meals', []):
                    for meal in meal_category.get('meal', []):
                        meal_id = str(meal.get('mealId')) 
                        db_meal_id = meal_lookup.get(meal_id)
                        if db_meal_id:
                            meal['details'] = db_meal_id
                        else: 
                            meal['details'] = None

                    
        return jsonify({"plan":plan_list}),200
    

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error":"An error occurred"})



@app.route("/generatePlan", methods=["GET"])
def generatePlan():
    cohere_client = cohere.Client(api_key)
    meal_plan = {}
    meals_list = get_meals_list()

    categorized_meals = {
        "breakfast": [meal for meal in meals_list if meal["category"] == "breakfast"],
        "snack": [meal for meal in meals_list if meal["category"] == "snack"],
        "lunch": [meal for meal in meals_list if meal["category"] == "lunch"],
        "dinner": [meal for meal in meals_list if meal["category"] == "dinner"]
    }

    for day in range(1, 15):
        daily_plan = {}

        prompt = (
            f"Create a weight loss meal plan for Day {day}. Focus on healthy, low-calorie options with balanced nutrition."
            " Choose meals from the database categories: breakfast, snack, lunch, and dinner."
        )

        response = cohere_client.generate(
            model="command",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
        )
        response_text = response.generations[0].text.strip()
        
        # Choose meals for each category based on the database
        daily_plan["breakfast"] = random.choice(categorized_meals["breakfast"])["name"]
        daily_plan["snack_1"] = random.choice(categorized_meals["snack"])["name"]
        daily_plan["lunch"] = random.choice(categorized_meals["lunch"])["name"]
        daily_plan["snack_2"] = random.choice(categorized_meals["snack"])["name"]
        daily_plan["dinner"] = random.choice(categorized_meals["dinner"])["name"]

        meal_plan[f"Day {day}"] = {
            "plan_description": response_text,
            "meals": daily_plan
        }

    plan_collection.insert_one({"generated_plan": meal_plan})

    return jsonify(meal_plan), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)