# Content Moderation System
A comprehensive multimedia content moderation system that analyzes audio and video streams separately for detecting violence, abusive content, NSFW material, and other prohibited content.

## Overview
This system provides automated content moderation through deep learning models, with separate processing pipelines for audio and video analysis. The backend is built with Python, PyTorch, and FastAPI, while the frontend uses React and Vite for a responsive user interface.

## Backend Details
- **Framework**: FastAPI
- **ML Framework**: PyTorch
- **Processing**: Separate analysis pipelines for audio and video content
- **Detection Categories**: Violence, abusive content, NSFW content, and more
- **API**: RESTful endpoints for content submission and results retrieval

## Frontend Details
- **Framework**: React
- **Build Tool**: Vite
- **Features**:
  - Content upload interface
  - Real-time moderation status
  - Detailed analysis results dashboard
  - Content tagging visualization

## Setup Instructions
### Backend Setup
1. Clone the repository:
   ```
   git clone https://github.com/SalehAhmad1/PBxVECTORxJAZZ.git
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python3.10 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Frontend Setup
1. Install dependencies:
   ```
   npm install
   ```

## Running the Application
### Running the Backend
From the backend directory:
```
python3 main.py
```

The API will be available at `http://localhost:8000` by default.

### Running the Frontend
From the frontend directory:
```
npm run dev
```

The web interface will be available at `http://localhost:5173` by default.

## Remote Access with Ngrok
If you want to run the backend and frontend on separate devices or make the application accessible remotely, you can use Ngrok.

### Backend Remote Access
1. Install Ngrok on your backend device
2. Start your backend server:
   ```
   python3 main.py
   ```
3. Create an Ngrok tunnel to expose port 8000:
   ```
   ngrok http 8000
   ```
4. Copy the Ngrok URL provided (e.g., `https://a1b2c3d4.ngrok.io`)

### Frontend Remote Access
1. Install Ngrok on your frontend device
2. Update the API endpoint in `src/components/VideoUpload.jsx`:
   - Locate where `http://localhost:8000/analyze` is referenced
   - Replace it with the Ngrok URL from your backend (e.g., `https://a1b2c3d4.ngrok.io/analyze`)
3. Start your frontend server:
   ```
   npm run dev
   ```
4. Create an Ngrok tunnel to expose port 5173:
   ```
   ngrok http 5173
   ```
5. Access your application through the frontend Ngrok URL

Note: Ngrok free tier URLs expire after a session ends, so you'll need to update the frontend code with the new backend URL whenever you restart the Ngrok session.