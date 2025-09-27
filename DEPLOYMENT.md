# Product Recognition App

An AI-powered product recognition application that uses YOLO object detection and Google's Gemini API to identify products from shelf images.

## Features

- 🖼️ Upload images of product shelves
- 🎯 Automatic product detection using YOLOv11
- 🤖 Product identification using Google Gemini AI
- 📱 Responsive web interface
- ⚡ Fast processing and results display

## Tech Stack

### Frontend
- React.js with Vite
- Tailwind CSS
- React Dropzone for file uploads
- Framer Motion for animations

### Backend
- Flask (Python)
- YOLOv11 for object detection
- Google Gemini API for product identification
- OpenCV for image processing

## Local Development

### Prerequisites
- Node.js (v18 or higher)
- Python 3.8+
- Git

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd dotslash-repo
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Install backend dependencies:
```bash
cd ../backend
python -m venv dotslash
source dotslash/bin/activate  # On Windows: dotslash\Scripts\activate
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the backend directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

5. Run the application:

Start the backend:
```bash
cd backend
source dotslash/bin/activate
python app.py
```

Start the frontend (in a new terminal):
```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5174`

## Deployment on Vercel

### Prerequisites
- Vercel account
- GitHub repository

### Steps

1. **Push your code to GitHub:**
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with your GitHub account
   - Click "New Project"
   - Import your repository

3. **Configure Environment Variables:**
   In your Vercel project settings, add:
   - `GEMINI_API_KEY`: Your Google Gemini API key

4. **Deploy:**
   - Vercel will automatically detect the configuration from `vercel.json`
   - The build will process both frontend and backend
   - Your app will be live at `your-project-name.vercel.app`

### Important Notes for Deployment

- The backend runs as serverless functions on Vercel
- The YOLO model file is included in the deployment
- Environment variables must be set in Vercel dashboard
- The frontend automatically detects production vs development environments

## Project Structure

```
dotslash-repo/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   └── utils/          # Utility functions
│   └── package.json
├── backend/                 # Flask backend (for local development)
│   ├── app.py
│   ├── utils/
│   └── requirements.txt
├── api/                    # Serverless functions for production
│   ├── detect.py           # Main API endpoint
│   └── YOLOv11_SKU.pt     # YOLO model
├── vercel.json             # Vercel configuration
└── requirements.txt        # Python dependencies for serverless
```

## API Usage

### POST /api/detect
Upload an image for product detection.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: image file

**Response:**
```json
{
  "processed_image": "data:image/jpeg;base64,/9j/4AAQ...",
  "detected_products": [
    {
      "name": "Product Name 1"
    },
    {
      "name": "Product Name 2"
    }
  ]
}
```

## Configuration Files

### vercel.json
Configures Vercel deployment with:
- Static build for frontend
- Python serverless functions for backend
- Routing configuration

### Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key for product identification

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - see LICENSE file for details
