from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
from boto3.dynamodb.conditions import Key, Attr
import uuid
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bcrypt import hashpw, gensalt, checkpw
import os
import random

app = Flask(__name__)  # ✅ Fix: __name__ not _name_
app.secret_key = os.urandom(24)

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# ✅ DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
user_table = dynamodb.Table('Users')
orders_table = dynamodb.Table('Orders')

# ✅ SNS
sns = boto3.client('sns', region_name='us-east-1')
SNS_TOPIC_ARN = 'YOUR_SNS_TOPIC_ARN'  # ⚠️ Replace with your real SNS ARN

# ✅ Email config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = 'mounika030721@gmail.com'
EMAIL_PASSWORD = 'ggzr vytt lqpr aplh'

# Product data with more items
veg_pickles = [
    {'id': 1, 'name': 'Mango Pickle', 'price': 250, 'weight': '500g','spice_level': 5,'description':'Traditional raw mango chunks spiced and sun-cured for that classic tangy punch.', 'image': '/static/images/mango.jpg','rating':5},
    {'id': 2, 'name': 'Lemon Pickle', 'price': 220, 'weight': '500g','spice_level': 3,'description':'Zesty lemon pieces pickled in salt and spices for a perfect balance of sour and spicy.', 'image': '/static/images/lemon.jpg','rating':4},
    {'id': 3, 'name': 'Tomato Pickle', 'price': 199, 'weight': '500g','spice_level': 4,'description':'Ripe tomatoes blended with fiery masala for a rich, tangy flavor explosion.', 'image': '/static/images/tomato.jpg','rating':5},
    {'id': 4, 'name': 'Amla Pickle', 'price': 180, 'weight': '500g','spice_level': 3,'description':'Sour gooseberries pickled for a punch.Rich in flavor and healthy goodness.', 'image': '/static/images/amla.jpg','rating':4},
    {'id': 5, 'name': 'Mixed Veg Pickle', 'price': 199, 'weight': '500g','spice_level': 4,'description':'A medley of crunchy vegetables marinated in bold Andhra-style spices.', 'image': '/static/images/mixed.jpg','rating':4},
    {'id': 6, 'name': 'Red Chilli Pickle', 'price': 180, 'weight': '500g','spice_level': 5,'description':'Whole red chilies stuffed and soaked in aromatic, spicy oil for heat lovers.', 'image': '/static/images/chilli.jpg','rating':5},
    {'id': 7, 'name': 'Garlic Pickle', 'price': 199, 'weight': '500g','spice_level': 3,'description':'Whole garlic pods steeped in tangy masala — a pungent, flavorful delight.', 'image': '/static/images/garlic.jpg','rating':5},
    {'id': 8, 'name': 'Gongura Pickle', 'price': 150, 'weight': '500g','spice_level': 4,'description':'Tangy gongura leaves (sorrel) blended with spice-rich oil — a true Andhra specialty.','image': '/static/images/gongura.jpg','rating':5}
]

non_veg_pickles = [
    {'id': 9, 'name': 'Prawn Pickle', 'price': 599, 'weight': '500g','spice_level': 3,'description':'Spicy, tangy prawns soaked in aromatic coastal masala.','image': '/static/images/prawn.jpg','rating':5},
    {'id': 10, 'name': 'Chicken Pickle', 'price': 450, 'weight': '500g','spice_level': 4,'description': 'Juicy chicken with bold Andhra spices.', 'image': '/static/images/chicken.jpg','rating':4},
    {'id': 11, 'name': 'Fish Pickle', 'price': 599, 'weight': '500g','spice_level': 4,'description':'Boneless fish in a sharp, spicy, and tangy masala mix.','image': '/static/images/fish.jpg','rating':4},
    {'id': 12, 'name': 'Mutton Pickle', 'price': 650, 'weight': '500g','spice_level': 3,'description':'Juicy mutton pieces blended with bold, fiery spices.', 'image': '/static/images/mutton.jpg','rating':4},
    {'id': 13, 'name': 'Crab Pickle', 'price': 699, 'weight': '500g','spice_level': 5,'description':'Delicate crab meat pickled in rich, zesty Andhra flavors.', 'image': '/static/images/crab.jpg','rating':5},
    {'id': 14, 'name': 'Gongura Mutton Pickle', 'price': 750, 'weight': '500g','spice_level': 2,'description':'Juicy mutton pieces cooked with tangy gongura leaves.A rich Andhra-style pickle with bold sour-spicy taste.','image': '/static/images/gongura mutton.jpg','rating':5}
]

snacks = [
    {'id': 15, 'name': 'Mixture', 'price': 99, 'weight': '250g','description':'A crunchy blend of sev, nuts, and spices — the ultimate anytime snack.', 'image': '/static/images/mixture.jpg','rating':5},
    {'id': 16, 'name': 'Murukku', 'price': 150, 'weight': '250g','description':'Crispy spiral sticks made from rice flour and sesame — delightfully addictive.', 'image':'/static/images/murukku.jpeg','rating':4},
    {'id': 17, 'name': 'Banana Chips', 'price': 99, 'weight': '250g', 'description':'Thinly sliced raw bananas fried to golden crispness with a hint of salt.','image': '/static/images/banana.jpeg','rating':4},
    {'id': 18, 'name': 'Ribbon Pakoda', 'price': 120, 'weight': '250g','description':'Flat, ribbon-shaped snack with a spicy, crunchy bite in every strip.','image': '/static/images/ribbon.jpg','rating':5},
    {'id': 19, 'name': 'Kara Sev', 'price': 80, 'weight': '250g','description':'Spiced chickpea flour noodles deep-fried for a fiery, crunchy treat.','image': '/static/images/sev.jpeg','rating':4},
    {'id': 21, 'name': 'Thattai', 'price': 80, 'weight': '200g','description':'Flat, crunchy discs made with rice flour, spices, and lentils — perfectly savory.', 'image': '/static/images/thattai.jpeg','rating':5},
]

@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/submit_review', methods=['POST'])
def submit_review():
    name = request.form['name']
    message = request.form['message']
    flash("Thanks for your review, " + name + "!")
    return redirect(url_for('home'))

def slugify(name):
    return name.lower().replace(" ", "-")

@app.route('/search')
def search():
    query = request.args.get('query', '').lower()
    results = []
    for item in veg_pickles:
        if query in item["name"].lower():
            slug = slugify(item["name"])
            results.append({"name": item["name"], "image": item["image"], "link": f"/veg_pickles#{slug}"})
    for item in non_veg_pickles:
        if query in item["name"].lower():
            slug = slugify(item["name"])
            results.append({"name": item["name"], "image": item["image"], "link": f"/non_veg_pickles#{slug}"})
    for item in snacks:
        if query in item["name"].lower():
            slug = slugify(item["name"])
            results.append({"name": item["name"], "image": item["image"], "link": f"/snacks#{slug}"})
    return render_template('search_results.html', query=query, results=results)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/veg_pickles')
def show_veg_pickles():
    return render_template('veg_pickles.html', products=veg_pickles)

@app.route('/non_veg_pickles')
def show_non_veg_pickles():
    return render_template('non_veg_pickles.html', products=non_veg_pickles)

@app.route('/snacks')
def show_snacks():
    return render_template('snacks.html', products=snacks)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    name = request.form['name']
    price = float(request.form['price'])
    weight = request.form['weight']

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']
    for item in cart:
        if item['name'] == name and item['weight'] == weight:
            item['quantity'] += 1
            break
    else:
        cart.append({'name': name, 'price': price, 'weight': weight, 'quantity': 1})

    session['cart'] = cart

    # ✅ Optional: Show a nice flash message
    flash(f"{name} added to cart!", "success")

    # ✅ ✅ ✅ ✅ The important part:
    return redirect(request.referrer or url_for('home'))


@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart_items=cart, total=total)

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    name = request.form['item_name']
    change = int(request.form['change'])
    cart = session.get('cart', [])
    for item in cart:
        if item['name'] == name:
            item['quantity'] += change
            if item['quantity'] <= 0:
                cart.remove(item)
            break
    session['cart'] = cart
    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    name = request.form['item_name']
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item['name'] != name]
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['fullname']
        email = request.form['email']
        address = request.form['address']
        city = request.form['city']
        pincode = request.form['pincode']
        phone = request.form['phone']
        payment = request.form['payment']
        upi_id = request.form.get('upi_id')
        card_number = request.form.get('card_number')

        cart_items = session.get('cart', [])
        total = sum(item['price'] for item in cart_items)

        order_id = str(uuid.uuid4())
        order_data = {
            'order_id': order_id,
            'name': name,
            'address': address,
            'city': city,
            'pincode': pincode,
            'phone': phone,
            'email': email,
            'payment': payment,
            'upi_id': upi_id,
            'card_number': card_number,
            'total': total,
            'items': cart_items
        }
        orders_table.put_item(Item=order_data)

        # ✅ SNS publish
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='New Order',
            Message=f"Order ID: {order_id}\nName: {name}\nTotal: ₹{total}"
        )

        # ✅ Send Email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = 'Order Confirmation - Pickle Paradise'
        body = f"""Thank you {name} for your order!
Order ID: {order_id}
Total Amount: ₹{total}
Payment Method: {payment}

We will ship your items soon!"""
        msg.attach(MIMEText(body, 'plain'))
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
            server.quit()
            print("Email sent successfully")
        except Exception as e:
            print(f"Failed to send email: {e}")

        session.pop('cart', None)
        return render_template('success.html', name=name, order_id=order_id)

    return render_template('checkout.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # ✅ Hash the password
        hashed_pw = hashpw(password.encode('utf-8'), gensalt())

        # ✅ Generate a unique User_id
        user_id = str(uuid.uuid4())

        # ✅ Save all required fields
        user_table.put_item(Item={
            'User_id': user_id,
            'email': email,
            'password': hashed_pw.decode('utf-8')
        })

        # ✅ Send welcome email
        send_email(email, "Welcome to Pickle Paradise", "Thank you for signing up!")

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # ✅ DynamoDB key must be the same as your table's PRIMARY KEY
        # If 'email' is not your primary key, you must query by index.
        response = user_table.scan(
            FilterExpression=Attr('email').eq(email)
        )
        items = response.get('Items', [])

        if items:
            user = items[0]
            hashed_pw = user['password'].encode('utf-8')

            if checkpw(password.encode('utf-8'), hashed_pw):
                session['user'] = email
                flash("Login successful!", "success")
                return redirect(url_for('home'))

        flash("Invalid credentials", "danger")

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out successfully!", "success")
    return redirect(url_for('index'))


def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email failed:", e)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=True)
