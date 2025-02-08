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


@app.route("/generatePlan", methods=["POST"])
def generatePlan():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400
    
    age = data.get("age")
    gender = data.get("gender")
    weight = data.get("weight")
    height = data.get("height")
    goal = data.get("goal")

    cohere_client = cohere.Client(api_key)
    meal_plan = {"plan": []}

    prompt = (
        f"Create a balanced 14-day meal plan focusing on the goal of {goal}. "
        f"Each day should include meals in the following categories: breakfast, lunch, dinner, snack_1, and snack_2. "
        f"Each meal should be healthy and tailored for an individual with age {age}, gender {gender}, "
        f"weight {weight}kg, and height {height}cm. The meals should have a good balance of protein, "
        f"carbs, and healthy fats, and should fit within a healthy calorie range. "
        f"Please include a description for each day and provide the following details for each meal: "
        f"- name: The name of the meal. "
        f"- calories: The calorie count. "
        f"- carbs: The carbohydrate content. "
        f"- fat: The fat content. "
        f"- protein: The protein content. "
        f"Here is the format you should follow for each day:\n"
        "Day 1:\n"
        "- Breakfast: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W])\n"
        "- Snack 1: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W])\n"
        "- Lunch: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W])\n"
        "- Snack 2: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W])\n"
        "- Dinner: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W])\n"
        "\nRepeat for 14 days."
    )

    # Make a single call to generate the full 14-day meal plan
    response = cohere_client.generate(
        model="command",
        prompt=prompt,
        max_tokens=3000,  # Increase tokens to accommodate detailed meal information
        temperature=0.7,
    )

    response_text = response.generations[0].text.strip()

    # Split the response text into days
    days = response_text.split("\n\n")  # Assuming days are separated by two newlines

    for day_index, day_text in enumerate(days, 1):
        daily_plan = {
            "day": str(day_index),
            "meals": []
        }

        # Split the day text into individual meals
        meals = day_text.split("\n")
        for meal in meals:
            if meal.strip():
                try:
                    # Extract meal category and details
                    category, meal_details = meal.split(": ", 1)
                    category = category.strip("- ").capitalize()

                    # Check if the meal_details contains parentheses before splitting
                    if "(" in meal_details and ")" in meal_details:
                        meal_name = meal_details.split("(")[0].strip()
                        details = meal_details.split("(")[1].strip(")").split(", ")
                        details_dict = {}
                        for detail in details:
                            key, value = detail.split(": ")
                            details_dict[key] = value
                    else:
                        # Handle case where parentheses are missing
                        print(f"Skipping meal due to missing details in: {meal}")
                        continue

                    # Generate a unique ID for the meal
                    meal_id = str(uuid.uuid4())

                    # Structure the meal data
                    meal_data = {
                        "category": category,
                        "meal": {
                            "_id": meal_id,
                            "calories": details_dict.get("calories", "N/A"),
                            "carbs": details_dict.get("carbs", "N/A"),
                            "fat": details_dict.get("fat", "N/A"),
                            "name": meal_name,
                            "protein": details_dict.get("protein", "N/A"),
                            "quantity": "1"  # Default quantity, can be adjusted
                        },
                        "mealId": meal_id
                    }

                    daily_plan["meals"].append(meal_data)
                except ValueError as e:
                    # Handle cases where the meal string doesn't match the expected format
                    print(f"Error parsing meal: {meal}. Error: {e}")
                    continue

        meal_plan["plan"].append(daily_plan)

    # Print the structured meal plan for debugging (can be removed later)
    print(meal_plan)

    # Return the final structured meal plan as JSON
    return jsonify(meal_plan), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)