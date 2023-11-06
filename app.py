import os
import requests
import io
import time
from PIL import Image
from flask import Flask, render_template, request, send_file, jsonify
from transformers import AutoTokenizer
from pymongo import MongoClient
from datetime import datetime
import json

# Connect to your local MongoDB (adjust the MongoDB URI as needed)
client = MongoClient("mongodb://localhost:27017/")
db = client["image_database"]  # Create or use an existing database
collection = db["generated_images"]  # Create or use an existing collection (similar to a table in SQL)

app = Flask(__name__)

# Define the API URL and authorization headers
#API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
#HEADERS = {"Authorization": "Bearer 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"}
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
HEADERS = {"Authorization": "Bearer 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"}

# Function to query the model using the provided payload
def query_model(payload):
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.content

# List of keywords that must be present in the input prompt
keywords = ["car", "design", "xuv", "muv", "sedan", "sports car", "car color", "car designing", "4 wheels car", "blue color car", "red color car"]

# Function to check and filter input text
def filter_input_text(input_text):
    # Check if any of the keywords are present in the input_text
    if any(keyword in input_text.lower() for keyword in keywords):
        return input_text
    else:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    image_path = None  # Initialize image_path
    if request.method == "POST":
        input_text = request.form["input_text"]
        
        # Check and filter the input text
        filtered_text = filter_input_text(input_text)
        
        if filtered_text:
            image_bytes = query_model({"inputs": filtered_text})

            # Store the image in MongoDB
            image_data = {
                "input_text": filtered_text,  # You can store additional data if needed
                "image_bytes": image_bytes,
                "created_at": datetime.utcnow(),
            }
            collection.insert_one(image_data)

            # Save the image to a temporary file
            timestamp = int(time.time())
            temp_image_path = f"static/temp_image_{timestamp}.png"
            with open(temp_image_path, "wb") as file:
                file.write(image_bytes)

            image_path = temp_image_path  # Set the image_path to the temporary image
        else:
            # Keywords not present, return an error message
            return render_template("error.html")

    return render_template("index.html", image_path=image_path)

@app.route("/download")
def download_image():
    image_path = request.args.get("image_path")
    return send_file(image_path, as_attachment=True, download_name="generated_image.png")

if __name__ == "__main__":
    app.run(port=8080)