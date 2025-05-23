from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Suppress TensorFlow Warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Load Trained Model
MODEL_PATH = "Landside_classification.h5"
if os.path.exists(MODEL_PATH):
    model = tf.keras.models.load_model(MODEL_PATH)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    print("Model Loaded Successfully!")
else:
    print("Error: Model file not found!")

# Pest Labels & Information
labels = ['Landslide', 'non-Landslide']



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')
        email = request.form['email']
        address = request.form['address']

        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (name, username, password, email, address) VALUES (?, ?, ?, ?, ?)",
                      (name, username, password, email, address))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username or email already exists. Please choose a different one."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):  # user[3] is the password column
            session['user_id'] = user[0]  # user[0] is the user id
            return redirect(url_for('predict'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Route for Prediction Page
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Load & Preprocess Image
            img = cv2.imread(filepath)
            img = cv2.resize(img, (224, 224))
            img = img / 255.0
            img = np.expand_dims(img, axis=0)

            # Make Prediction
            prediction = model.predict(img)
            predicted_class = labels[np.argmax(prediction)]
           

            return render_template('result.html', 
                                   prediction=predicted_class, 
                                   filepath=filepath)

    return render_template('predict.html')

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
