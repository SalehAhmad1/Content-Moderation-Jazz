from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from analysis import analyze_video
import tempfile
import os
from typing import Optional

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_content(
    video: UploadFile = File(...),
    gemini_api: str = Form(...),
    detect_abusive: bool = Form(False),
    detect_violent: bool = Form(False),
    detect_nsfw: bool = Form(False),
    detect_political: bool = Form(False),
    detect_religious: bool = Form(False)
):
    # Save uploaded file temporarily
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video.filename)[1])
    try:
        content = await video.read()
        temp_file.write(content)
        temp_file.close()

        # Analyze the video with the additional flags for political and religious analysis
        transcript, abusive_table, violent_table, nsfw_audio_table, political_table, religious_table, video_nsfw_info, video_violence_info = analyze_video(
            gemini_api=gemini_api,
            detect_abusive=detect_abusive,
            detect_violent=detect_violent,
            detect_nsfw=detect_nsfw,
            detect_political=detect_political,
            detect_religious=detect_religious,
            video_path=temp_file.name
        )

        return {
            "transcript": transcript,
            "abusive_table": abusive_table,
            "violent_table": violent_table,
            "nsfw_audio_table": nsfw_audio_table,
            "political_table": political_table,
            "religious_table": religious_table,
            "video_nsfw_info": video_nsfw_info,
            "video_violence_info": video_violence_info
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)