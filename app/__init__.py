#===========================================================
# App Creation and Launch
#===========================================================

from flask import Flask, render_template, session, request, flash, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import html

from app.helpers.session import init_session
from app.helpers.db import connect_db
from app.helpers.errors import register_error_handlers, not_found_error


# Create the app
app = Flask(__name__)

# Setup a session for messages, etc.
init_session(app)

# Handle 404 and 500 errors
register_error_handlers(app)


#-----------------------------------------------------------
# Home page route
#-----------------------------------------------------------
@app.get("/")
def index():
    return render_template("pages/home.jinja")


#-----------------------------------------------------------
# About page route
#-----------------------------------------------------------
@app.get("/about/")
def about():
    return render_template("pages/about.jinja")


#-----------------------------------------------------------
# Sign-Up page route
#-----------------------------------------------------------
@app.get("/signup/")
def signup():
    return render_template("pages/signup.jinja")


#-----------------------------------------------------------
# Login page route
#-----------------------------------------------------------
@app.get("/login/")
def login():
    return render_template("pages/login.jinja")


#-----------------------------------------------------------
# Things page route - Show all the things, and new thing form
#-----------------------------------------------------------
@app.get("/things/")
def show_all_things():
    with connect_db() as client:
        # Get all the things from the DB
        sql = "SELECT id, name FROM things ORDER BY name ASC"
        result = client.execute(sql)
        things = result.rows

        # And show them on the page
        return render_template("pages/things.jinja", things=things)


#-----------------------------------------------------------
# Thing page route - Show details of a single thing
#-----------------------------------------------------------
@app.get("/thing/<int:id>")
def show_one_thing(id):
    with connect_db() as client:
        # Get the thing details from the DB
        sql = """
            SELECT things.id   AS t_id,
                   things.name AS t_name,
                   users.name  AS u_name,
                   users.id    AS u_id

            FROM things
            JOIN users ON things.user_id = users.id

            WHERE things.id=?
        """
        values = [id]
        result = client.execute(sql, values)

        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            thing = result.rows[0]
            return render_template("pages/thing.jinja", thing=thing)

        else:
            # No, so show error
            return not_found_error()


#-----------------------------------------------------------
# Route for adding a thing, using data posted from a form
#-----------------------------------------------------------
@app.post("/add")
def add_a_thing():
    # Get the data from the form
    name  = request.form.get("name")

    # Sanitise the inputs
    name = html.escape(name)

    # Get the user_id from the session
    user_id = session["user_id"]

    with connect_db() as client:
        # Add the thing to the DB
        sql = "INSERT INTO things (name, user_id) VALUES (?, ?)"
        values = [name, user_id]
        client.execute(sql, values)

        # Go back to the home page
        flash(f"Thing '{name}' added", "success")
        return redirect("/things")


#-----------------------------------------------------------
# Route for adding a user, using data posted from a form
#-----------------------------------------------------------
@app.post("/add-user")
def add_a_user():
    # Get the data from the form
    name      = request.form.get("name")
    username  = request.form.get("username")
    password  = request.form.get("password")

    # Sanitise the inputs
    name     = html.escape(name)
    username = html.escape(username)

    # Hash the password
    hash = generate_password_hash(password)

    with connect_db() as client:
        # Add the user to the DB
        sql = "INSERT INTO users (name, username, password_hash) VALUES (?, ?, ?)"
        values = [name, username, hash]
        client.execute(sql, values)

        # Go back to the home page
        flash(f"Thing '{name}' added", "success")
        return redirect("/")


#-----------------------------------------------------------
# Route for logging in a user, using data posted from a form
#-----------------------------------------------------------
@app.post("/login-user")
def login_user():
    # Get the data from the form
    username  = request.form.get("username")
    password  = request.form.get("password")

    # Sanitise the inputs
    username = html.escape(username)

    with connect_db() as client:
        # Try to find a matching record
        sql = """
            SELECT id, name, password_hash
            FROM users
            WHERE username=?
        """
        values = [username]
        result = client.execute(sql, values)

        # Check if we got a record
        if result.rows:
            # Yes, so user exists
            user = result.rows[0]
            hash = user["password_hash"]

            # Check if passwords match
            if check_password_hash(hash, password):
                # Yes, so save the details in the session
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                flash("Logged in successfully", "success")
                return redirect("/")


        # Go back to the home page
        flash("Incorrect credentials", "error")
        return redirect("/login")


#-----------------------------------------------------------
# Route for deleting a thing, Id given in the route
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
def delete_a_thing(id):
    with connect_db() as client:
        #get our user id from session
        user_id = session["user_id"]
        # Delete the thing from the DB
        sql = "DELETE FROM things WHERE id=? AND user_id=?"
        values = [id,user_id]
        client.execute(sql, values)

        # Go back to the home page
        flash("Thing deleted", "success")
        return redirect("/things")


#-----------------------------------------------------------
# Route user logout
#-----------------------------------------------------------
@app.get("/logout")
def logout():
    # Clear the session values
    session.pop("user_id")
    session.pop("user_name")
    # Back to the home page
    flash("You have been logged out!", "success")
    return redirect("/")