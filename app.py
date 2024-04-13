from flask import Flask,render_template,request, url_for,flash,redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from cryptography.fernet import Fernet
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
import util
import numpy as np
import pandas as pd
import os

load_dotenv()

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = os.getenv('DB_SECRET_KEY')
client = MongoClient('localhost', 27017)
db = client['prediction_palace']  
users_collection = db['users']
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')


class User(UserMixin):
    def __init__(self, id):
        self.id = id

model=util.load_model()
df=util.load_data()

models=util.load_model_car()
car=pd.read_csv('artefacts/cleancar.csv')

key_file = "encryption.key"

# Check if the key file exists
if os.path.exists(key_file):
    # Load the key
    with open(key_file, "rb") as file:
        encryption_key = file.read()
else:
    # Generate a new key
    encryption_key = Fernet.generate_key()
    # Save the key
    with open(key_file, "wb") as file:
        file.write(encryption_key)

fernet = Fernet(encryption_key)        


@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data is not None:
        print(User(user_id))
        return User(user_id)
    else:
        return None


def encrypt_data(data):
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data

def decrypt_data(encrypted_data):
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    return decrypted_data

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.route('/',methods=['GET'])
def home():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the username and password match
        user = users_collection.find_one({'email':email,'username': username})
        if user:
            # Decrypt the password stored in the database
            db_password = decrypt_data(user['password'])
            if password == db_password:
                login_user(User(str(user['_id'])))
                flash('Login successful.', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Invalid username and password. Please try again.', 'danger')
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the username already exists
        if users_collection.find_one({'username': username}):
            flash('Username already exists. Choose a different one.', 'danger')
        else:
            if password :
                password=encrypt_data(password)
                users_collection.insert_one({'email':email,'username': username, 'password': password})
                flash('Registration successful. You can now log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Please choose your password')
        
    print(url_for('register'))    

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    user = users_collection.find_one({'_id': ObjectId(current_user.id)})
    if user is not None:
        return render_template('profile.html', email=user['email'], username=user['username'])
    else:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

@app.route("/laptop",methods=['POST','GET'])
@login_required
def predict_laptop_price():
    if request.method == 'POST':
        company = request.form.get('myBrowser1')
        typename = request.form.get('myBrowser2')
        ram = request.form.get('myBrowser3')
        weight = request.form.get('myBrowser4')
        touchscreen = request.form.get('myBrowser5')
        ips = request.form.get('myBrowser6')
        ppi = request.form.get('myBrowser7')
        cpu=request.form.get('myBrowser8')
        hdd = request.form.get('myBrowser9')
        ssd = request.form.get('myBrowser10')
        gpu = request.form.get('myBrowser11')
        os = request.form.get('myBrowser12')

        features = [company, typename, ram, weight, touchscreen, ips, ppi,cpu, hdd, ssd, gpu, os]

        query=np.array(features,dtype=object)

        query=query.reshape(1,12)

        # Make a prediction
        prediction = np.exp(model.predict(query)[0])

        return render_template('app.html', prediction=prediction)
    
    else:
        company = df['Company'].unique().tolist()
        typename = df['TypeName'].unique().tolist()
        ram = df['Ram'].unique().tolist()
        touchscreen = df['Touchscreen'].unique().tolist()
        ips = df['IPS'].unique().tolist()
        cpu_brand = df['Cpu_Brand'].unique().tolist()
        hdd = df['HDD'].unique().tolist()
        ssd = df['SSD'].unique().tolist()
        gpu = df['Gpu_brand'].unique().tolist()
        os = df['os'].unique().tolist()

        return render_template('app.html', company=company,typename=typename,ram=ram,touchscreen=touchscreen,ips=ips,hdd=hdd,ssd=ssd,cpu_brand=cpu_brand,gpu=gpu,os=os)


@app.route("/car",methods=['POST','GET'])
@login_required
def predict_car_price():
    if request.method == 'POST':
        company = request.form.get('myBrowser1')
        car_model = request.form.get('myBrowser2')
        year = int(request.form.get('myBrowser3'))
        fuel_type = request.form.get('myBrowser4')
        kms_driven = request.form.get('myBrowser5')

        # Make a prediction
        prediction = models.predict(pd.DataFrame([[car_model,company,year,kms_driven,fuel_type]],colums=['name','company','year','kms_driven','fuel_type']))

        return str(prediction[0])
    
    else:
        company = sorted(car['company'].unique().tolist())
        car_model = sorted(car['name'].unique().tolist())
        year = sorted(car['year'].unique().tolist())
        fuel_type = sorted(car['fuel_type'].unique().tolist())


        return render_template('app1.html',company=company,car_models=car_model,year=year,fuel_type=fuel_type)


if __name__=='__main__':
    app.run(debug=True)    