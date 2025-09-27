from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
from dotenv import load_dotenv
from PIL import Image, ImageDraw
import tempfile
import io
import json
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)
CORS(app)

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

def process_with_gemini(image):
    """Process image directly with Gemini API for product detection"""
    try:
        if not model:
            return {"products": []}
            
        prompt = """Analyze this retail shelf image and detect all visible products.
        
        For each product you can clearly see:
        1. Read the product label/text carefully
        2. Identify the brand and product name
        3. Format as "Brand Product Name"
        4. Only include products where you can clearly read the text
        5. Skip any products that are unclear or partially visible
        
        Draw bounding boxes around detected products and return results in JSON format:
        {
            "products": [
                {"Product Name": "Brand Product Name"}
            ]
        }
        
        Focus on accuracy over quantity - only include products you're confident about."""
        
        response = model.generate_content([prompt, image])
        print("Raw Gemini Response:", response.text)
        
        try:
            # Clean the response text
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            # Remove any markdown formatting
            if cleaned_text.startswith("```"):
                lines = cleaned_text.split('\n')
                cleaned_text = '\n'.join(lines[1:-1])
            
            result = json.loads(cleaned_text)
            return result
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Cleaned text: {cleaned_text}")
            return {"products": []}
        
    except Exception as e:
        print(f"Error in Gemini processing: {str(e)}")
        return {"products": []}

def create_mock_bounding_boxes(image, num_products):
    """Create a mock processed image with bounding boxes"""
    # Create a copy of the image for drawing
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    # Get image dimensions
    width, height = img_copy.size
    
    # Create some mock bounding boxes based on number of products
    box_color = (0, 255, 0)  # Green
    box_width = 3
    
    # Simple grid-based mock boxes
    if num_products > 0:
        cols = min(3, num_products)
        rows = (num_products + cols - 1) // cols
        
        box_width_size = width // (cols + 1)
        box_height_size = height // (rows + 1)
        
        for i in range(min(num_products, 6)):  # Limit to 6 boxes
            col = i % cols
            row = i // cols
            
            x1 = (col + 1) * width // (cols + 1) - box_width_size // 2
            y1 = (row + 1) * height // (rows + 1) - box_height_size // 2
            x2 = x1 + box_width_size
            y2 = y1 + box_height_size
            
            # Ensure boxes are within image bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(width, x2), min(height, y2)
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=box_width)
    
    return img_copy

@app.route('/api/detect', methods=['POST'])
def detect_products():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Load image directly from file
        image = Image.open(file.stream)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Process image with Gemini for product detection
        print("Processing image with Gemini...")
        results = process_with_gemini(image)
        print("Gemini results:", json.dumps(results, indent=2))
        
        # Clean and process products
        all_products = []
        if results and 'products' in results:
            for product in results['products']:
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
        
        # Create processed image with mock bounding boxes
        processed_image = create_mock_bounding_boxes(image, len(product_list))
        
        # Convert processed image to base64
        img_buffer = io.BytesIO()
        processed_image.save(img_buffer, format='JPEG', quality=85)
        processed_image_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'processed_image': f"data:image/jpeg;base64,{processed_image_b64}",
            'detected_products': product_list
        })
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({'error': str(e)}), 500

# For Vercel serverless deployment
def handler(event, context):
    return app(event, context)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
