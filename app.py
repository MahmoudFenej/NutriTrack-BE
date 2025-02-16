from flask import Flask, jsonify,request
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import traceback
import cohere
from flask import jsonify
app = Flask(__name__)

client = MongoClient('mongodb+srv://israa:NutriTrack-123@cluster0.ff8mp.mongodb.net/')
db = client["NutriTrack"]
user_collection = db['USER']
meal_collection = db['MEALS']
plan_collection = db['PLAN']
generateplan_collection = db['GENERATE_PLAN']
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

@app.route("/login", methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input"}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        user = user_collection.find_one({'username': username})

        if not user:
            return jsonify({"error": "User not found"}), 404

        if user['password'] != password:
            return jsonify({"error": "Invalid password"}), 401

        user.pop('password', None)

        user['_id'] = str(user['_id'])

        return jsonify(user), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

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


@app.route("/plan", methods=["POST"])
def get_plan_goal_day():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input"}), 400

        user_id = data.get("user_id")
        goal = data.get("goal")

        plans = None

        if user_id:
            plans = generateplan_collection.find_one({"user_id": user_id})
            if plans:
                plans["_id"] = str(plans["_id"])
                return jsonify({"plan": [plans]}), 200
        if goal:
            plans = list(plan_collection.find({"goal": goal}))
            for plan in plans:
                plan["_id"] = str(plan["_id"])
        
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

            return jsonify({"plan": plans}), 200


        return jsonify({"plan": plans}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


cohere_client = cohere.Client(api_key)

def generatePlan(data):
    print("started")
    age = data.get("age")
    gender = data.get("gender")
    weight = data.get("weight")
    height = data.get("height")
    goal = data.get("goal")
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    prompt = (
        f"Create a balanced 14-day meal plan focusing on the goal of {goal}. "
        f"Each day should include meals: breakfast, lunch, dinner, snack_1, and snack_2. "
        f"Each meal should be healthy for an individual with age {age}, gender {gender}, "
        f"weight {weight}kg, and height {height}cm, with a balance of protein, carbs, and healthy fats. "
        f"Provide meal details including name, calories, carbs, fat, protein, and portion size if available.\n"
        f"Format:\n"
        "Day 1:\n"
        "- Breakfast: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W], portion: [amount])\n"
        "- Snack 1: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W], portion: [amount])\n"
        "- Lunch: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W], portion: [amount])\n"
        "- Snack 2: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W], portion: [amount])\n"
        "- Dinner: [meal_name] (calories: [X], carbs: [Y], fat: [Z], protein: [W], portion: [amount])\n"
        "\nRepeat for 14 days."
    )

    response = cohere_client.generate(
        model="command",
        prompt=prompt,
        max_tokens=3000,
        temperature=0.7,
    )

    response_text = response.generations[0].text.strip()

    print("Cohere Response:\n", response_text)

    days = [d.strip() for d in response_text.split("\n\n") if d.strip()]
    current_day = 1  

    plan_days = []  # This will be a list of day objects

    for day_text in days:
        if not day_text.lower().startswith(f"day {current_day}"):
            print(f"Expected 'Day {current_day}' but got: {day_text[:15]}")
            continue 

        daily_meals = []
        total_calories = 0  # Initialize total calories for the day

        meals = day_text.split("\n")
        for meal in meals:
            meal = meal.strip()
            if meal:
                try:
                    if ": " not in meal:
                        print(f"Skipping malformed meal entry: {meal}")
                        continue

                    category, meal_details = meal.split(": ", 1)
                    category = category.strip("- ").capitalize()

                    if "(" in meal_details and ")" in meal_details:
                        meal_name, details_string = meal_details.split("(", 1)
                        meal_name = meal_name.strip()
                        details_string = details_string.strip(")")

                        details_dict = {}
                        for detail in details_string.split(", "):
                            if ": " in detail:
                                key, value = detail.split(": ")
                                details_dict[key.lower()] = value
                            else:
                                print(f"Skipping malformed detail: {detail}")

                        portion = details_dict.get("portion", "1 serving")

                        calorie_value = details_dict.get("calories", "0")
                        try:
                            calorie_value = int(calorie_value)
                        except ValueError:
                            calorie_value = 0  

                        # Add to total calories for the day
                        total_calories += calorie_value

                        print(f"Parsed meal: {meal_name}, Calories: {calorie_value}")

                        meal_object = {
                            "quantity": portion,
                            "details": {
                                "calories": details_dict.get("calories", "N/A"),
                                "carbs": details_dict.get("carbs", "N/A"),
                                "fat": details_dict.get("fat", "N/A"),
                                "name": meal_name,
                                "protein": details_dict.get("protein", "N/A")
                            }
                        }

                        daily_meals.append({
                            "category": category,
                            "meal": [meal_object]
                        })

                    else:
                        print(f"Skipping meal due to missing details: {meal}")

                except ValueError as e:
                    print(f"Error parsing meal: {meal}. Error: {e}")
                    continue

        if daily_meals: 
            # Wrap the day's meals in an object with day number and total calories
            day_object = {
                "day": current_day,
                "meals": daily_meals,
                "total_calories": total_calories
            }
            plan_days.append(day_object)  # Append the day object to the list
            current_day += 1 

    final_plan = {
        "goal": goal,
        "description": f"14-day meal plan for {goal} tailored to a {age}-year-old {gender} weighing {weight}kg and {height}cm tall.",
        "Days": plan_days,  # Now Days is a list of day objects
        "user_id": user_id
    }

    # Check if a plan already exists for the user
    existing_plan = generateplan_collection.find_one({"user_id": user_id})
    
    if existing_plan:
        # Update the existing plan
        generateplan_collection.update_one(
            {"user_id": user_id},  # Filter
            {"$set": final_plan}   # Update fields
        )
    else:
        # Insert a new plan
        result = generateplan_collection.insert_one(final_plan)
        final_plan["_id"] = str(result.inserted_id)  # Convert ObjectId to string

    # Convert ObjectId to string in the final_plan
    if "_id" in final_plan:
        final_plan["_id"] = str(final_plan["_id"])

    print(final_plan)


import threading

@app.route("/generatePlan", methods=["POST"])
def generate_plan():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    thread = threading.Thread(target=generatePlan, args=(data,))
    thread.start()

    return jsonify({"message": "Processing started"}), 202
if __name__ == '__main__':
    app.run(debug=True)