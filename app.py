# Yamkela Mathontsi
import hmac
import sqlite3
import datetime

from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS, cross_origin

import cloudinary
import cloudinary.uploader


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(seconds=4000)
CORS(app, resources={r"/api/*": {"origins": "*"}})


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect('Hstore.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            print(f"{data[0]}, {data[2]}, {data[3]}")
            new_data.append(User(data[0], data[2], data[3]))
    return new_data


def init_user_table():
    conn = sqlite3.connect("Hstore.db")
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")


def init_product_table():
    conn = sqlite3.connect("Hstore.db")
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS product(product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "product_img TEXT NOT NULL,"
                 "descrip TEXT NOT NULL,"
                 "category TEXT NOT NULL,"
                 "name TEXT NOT NULL,"
                 "price TEXT NOT NULL,"
                 "description TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


init_user_table()
init_product_table()
users = fetch_users()

username_table = { u.username: u for u in users }
userid_table = { u.id: u for u in users }


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)




jwt = JWT(app, authenticate, identity)


@app.route('/registration/', methods=["POST"])
@cross_origin()
def user_registration():
    response = {}

    if request.method == "POST":
        name = request.json['name']
        username = request.json['username']
        password = request.json['password']

        with sqlite3.connect("Hstore.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "name,"
                           "username,"
                           "password) VALUES(?, ?, ?)", (name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201

        return response


@app.route("/auth/", methods=["POST"])
@cross_origin()
def auth():
    response = {}

    if request.method == "POST":

        username = request.json['username']
        password = request.json['password']

        with sqlite3.connect("Hstore.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE username='{}' AND password='{}'".format(username, password))
            user_information = cursor.fetchone()

        if user_information:
            response["user_info"] = user_information
            response["message"] = "Success"
            response["status_code"] = 201
            return jsonify(response)

        else:
            response['message'] = "Unsuccessful login, try again"
            response['status_code'] = 401
            return jsonify(response)


@app.route('/add-product/', methods=["POST"])
def add_products():
    response = {}

    if request.method == "POST":
        category = request.form['category']
        name = request.form['name']
        descrip = request.form['descrip']
        description = request.form['description']
        price = request.form['price']

        # print(category, name, description, price)

        with sqlite3.connect("Hstore.db") as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO product("
                           "category,"
                            "name,"
                           "descrip,"
                           "description,"
                           "price) VALUES(?, ?, ?, ?, ?)", (category, name, descrip, description, price))
            connection.commit()
            response["message"] = "success"
            response["status_code"] = 201
        return response


@app.route('/view-products/')
def view_products():
    response = {}

    with sqlite3.connect("Hstore.db") as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM product")

        posts = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = posts
    return response


@app.route('/edit/<int:product_id>/', methods=["PUT"])
def updating_products(product_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('Hstore.db') as conn:
            print(request.json)
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("category") is not None:
                put_data["category"] = incoming_data.get("category")

                with sqlite3.connect('Hstore.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE product SET category =? WHERE product_id=?", (put_data["category"],
                                                                                              product_id))
            elif incoming_data.get("name") is not None:
                put_data["name"] = incoming_data.get("name")

                with sqlite3.connect('Hstore.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE product SET name =? WHERE product_id=?",
                                   (put_data["name"], product_id))

                    conn.commit()
                    response['message'] = "product update was successful"
                    response['status_code'] = 200

    return response


@app.route('/delete/<int:product_id>/')
def delete_products(product_id):
    response = {}

    with sqlite3.connect("Hstore.db") as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM product WHERE product_id=" + str(product_id))
        connection.commit()
        response['status_code'] = 200
        response['message'] = "Product successfully removed from your basket."
    return response


if __name__ == "__main__":
    app.debug = True
    app.run(port=5001)

