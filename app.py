import os
import random
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
def home():
    carousel_recipes = list(
        mongo.db.recipe_detail.find({"created_by": "admin"}))
    random.shuffle(carousel_recipes)
    
    recipes = list(mongo.db.recipe_detail.find())

    return render_template(
        "home.html",
        carousel_recipes=carousel_recipes,
        recipes=recipes)


@app.route("/get_recipe")
def get_recipe():
    recipes = mongo.db.recipe_detail.find()
    return render_template("get_recipe.html", recipes=recipes)


@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        gf_free = "on" if request.form.get("gf_free") else "off"
        recipe = {
            "category_name": request.form.get("category_name"),
            "recipe_name": request.form.get("recipe_name"),
            "servings": request.form.get("servings"),
            "prep_time": request.form.get("prep_time"),
            "cook_time": request.form.get("cook_time"),
            "gf_free": gf_free,
            "ingredients": request.form.getlist("ingredients"),
            "recipe_image": request.form.get("recipe_image"),
            "recipe_method": request.form.getlist("recipe_method"),
            "created_by": session["user"],
            "difficulty": request.form.getlist("difficulty"),
            "cuisine": request.form.get("cuisine")
        }

        mongo.db.recipe_detail.insert_one(recipe)
        flash("Recipe Successfully Added")
        return redirect(url_for("get_recipe"))
        
    categories = mongo.db.categories.find().sort("category_name", 1 )
    difficulty = mongo.db.difficulty.find().sort("difficulty", 1 )
    return render_template("add_recipe.html", categories=categories, difficulty=difficulty)


@app.route("/full_recipe/<recipe_id>")
def full_recipe(recipe_id):
    recipe = mongo.db.recipe_detail.find_one({"_id":ObjectId(recipe_id)})

    if session["user"]:
        return render_template(
            "full_recipe.html",
            recipe=recipe
        )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        # if username already exists: flash message
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        # update mongoDB users collection
        register = {
            "firstname": request.form.get("firstname").lower(),
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(request.form.get("username")))
                    return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    
    recipe = list(mongo.db.recipe_detail.find({"created_by": session['user']}))

    if session["user"]:
        return render_template(
            "profile.html",
            username=username,
            recipe=recipe)

    return redirect(url_for("login"))


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    tasks = list(mongo.db.recipe_detail.find({"$text": {"$search": query}}))
    return render_template("get_recipe.html", recipes=recipes)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
