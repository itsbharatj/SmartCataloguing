from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import base64
from dotenv import load_dotenv
from PIL import Image
from pathlib import Path
import math
import json
import google.generativeai as genai
import tempfile
import io
from ultralytics import YOLO
import cv2
import numpy as np

load_dotenv()

app = Flask(__name__)
CORS(app)

class YOLOv11Detector:
    def __init__(self):
        # Load model from the same directory
        model_path = os.path.join(os.path.dirname(__file__), "YOLOv11_SKU.pt")
        if not os.path.exists(model_path):
            # Try alternative paths
            alt_paths = [
                "./YOLOv11_SKU.pt",
                "../YOLOv11_SKU.pt",
                "./utils/YOLOv11_SKU.pt"
            ]
            for path in alt_paths:
                if os.path.exists(path):
                    model_path = path
                    break
        
        self.model = YOLO(model_path)
    
    def process_image(self, image_path):
        """Process image and return bounding box image and cropped products"""
        # Run inference
        results = self.model(image_path)
        
        # Load original image
        image = cv2.imread(image_path)
        cropped_images = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # Draw bounding box on original image
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Crop the product
                    cropped = image[y1:y2, x1:x2]
                    if cropped.size > 0:
                        # Convert to PIL Image
                        cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
                        cropped_pil = Image.fromarray(cropped_rgb)
                        cropped_images.append(cropped_pil)
        
        # Convert processed image to PIL
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        processed_pil = Image.fromarray(image_rgb)
        
        return processed_pil, cropped_images

# Initialize components
detector = YOLOv11Detector()

# Initialize Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-8b')
else:
    model = None

def clean_product_name(name):
    """Clean product name by removing underscores and unwanted text"""
    if not name:
        return None
    
    name = str(name).strip()
    
    # List of terms that indicate an unknown product
    unknown_terms = [
        'unknown', 'error', 'unidentified', 'not clear', 'cannot identify'
    ]
    
    if any(term.lower() in name.lower() for term in unknown_terms):
        return None
    
    if len(name) < 3:
        return None
    
    cleaned_name = name.replace('_', ' ').strip()
    cleaned_name = ' '.join(cleaned_name.split())
    cleaned_name = cleaned_name.title()
    
    return cleaned_name

def process_batch_with_gemini(images):
    """Process a batch of PIL images with Gemini API"""
    try:
        if not model:
            return {"products": []}
            
        prompt = """Analyze these retail product images.
        
        For each image:
        1. Read the product label/text
        2. Identify the brand and product name
        3. Format as "Brand Product Name"
        4. If text is not clear, skip the product

        Return in JSON format:
        {
            "products": [
                {"Product Name": "Brand Product Name"}
            ]
        }"""
        
        content = [prompt] + images
        
        if len(images) == 0:
            return {"products": []}
        
        response = model.generate_content(content)
        print("Raw Gemini Response:", response.text)
        
        try:
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_text)
            return result
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            return {"products": []}
        
    except Exception as e:
        print(f"Error in batch processing: {str(e)}")
        return {"products": []}

@app.route('/api/detect', methods=['POST'])
def detect_products():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        # Process image and get PIL images
        processed_image, cropped_images = detector.process_image(temp_path)
        
        # Process cropped images in batches
        all_products = []
        BATCH_SIZE = 10  # Smaller batch size for serverless
        num_batches = math.ceil(len(cropped_images) / BATCH_SIZE)
        
        for batch_idx in range(num_batches):
            start_idx = batch_idx * BATCH_SIZE
            end_idx = min((batch_idx + 1) * BATCH_SIZE, len(cropped_images))
            
            batch_images = cropped_images[start_idx:end_idx]
            print(f"Processing batch {batch_idx + 1}/{num_batches}")
            
            # Process batch with Gemini
            batch_results = process_batch_with_gemini(batch_images)
            print("Batch results:", json.dumps(batch_results, indent=2))
            
            if batch_results and 'products' in batch_results:
                for product in batch_results['products']:
                    product_name = clean_product_name(product.get('Product Name'))
                    if product_name:
                        print(f"Adding product: {product_name}")
                        all_products.append({
                            'name': product_name
                        })
        
        # Get unique products
        unique_products = []
        seen = set()
        for product in all_products:
            if product['name'] not in seen:
                seen.add(product['name'])
                unique_products.append(product)
        
        # Sort products alphabetically
        product_list = sorted(unique_products, key=lambda x: x['name'])
        
        print("Final product list:", json.dumps(product_list, indent=2))
        
        # Convert processed image to base64
        img_buffer = io.BytesIO()
        processed_image.save(img_buffer, format='JPEG')
        processed_image_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return jsonify({
            'processed_image': f"data:image/jpeg;base64,{processed_image_b64}",
            'detected_products': product_list
        })
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({'error': str(e)}), 500

# For Vercel serverless deployment
def handler(request):
    with app.app_context():
        return app.full_dispatch_request()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
