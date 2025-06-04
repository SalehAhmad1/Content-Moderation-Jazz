import json
import re
import os
import torch
import tempfile
import whisper
from google import genai
from google.genai import types
from concurrent.futures import ThreadPoolExecutor
from nsfw_detector import main as nsfw_detector
from violence_detector import main as violence_detector
from prompts import (
    For_All_Sys_Instructions,
    Abusive_Content_Sys_Instructions,
    Violence_Sys_Instructions,
    NSFW_Sys_Instructions,
    Politics_Sys_Instructions,
    Religious_Sys_Instructions,
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[INFO] Using device: {device}")
whisper_model = whisper.load_model("medium", device=device)
print("[INFO] Whisper model loaded successfully.")

def calculate_cost(input_tokens, output_tokens):
    input_price = 0.075 if input_tokens <= 128000 else 0.15
    output_price = 0.30 if output_tokens <= 128000 else 0.60
    cost = ((input_tokens / 1_000_000.0) * input_price) + ((output_tokens / 1_000_000.0) * output_price)
    return round(cost, 8), round(cost, 8) * 280.0

def run_detection_models(video_path, violence_model_path, detect_nsfw, detect_violent):
    print("[INFO] Running detection models...")
    nsfw_result, violence_result = None, None
    with ThreadPoolExecutor() as executor:
        futures = {}
        if detect_nsfw:
            print("[INFO] Starting NSFW detection...")
            futures["nsfw"] = executor.submit(nsfw_detector, video_path=video_path)
        if detect_violent:
            print("[INFO] Starting Violence detection...")
            futures["violence"] = executor.submit(violence_detector, model_path=violence_model_path, video_path=video_path)
        nsfw_result = futures.get("nsfw").result() if "nsfw" in futures else None
        violence_result = futures.get("violence").result() if "violence" in futures else None
    print("[INFO] Detection models completed.")
    return nsfw_result, violence_result

def analyze_text_with_gemini(urdu_text, api_key, sys_instruct):
    print("[INFO] Sending text for Gemini analysis...")
    prompt = (
        "Analyze this Urdu transcript for harmful content: "
        f"{urdu_text}"
        " Do not generate any additional content other than the JSON result. "
        "Use this JSON schema: "
        "Result = { "
        "    'is_flagged': bool, "
        "    'tags': list[str], "
        "    'reasons': list[str], "
        "    'severity': str "
        "}"
        " Return: Result."
    )
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-1.5-flash-002',
            config=types.GenerateContentConfig(system_instruction=sys_instruct, temperature=0.0),
            contents=prompt,
        )
        print("[INFO] Gemini analysis complete.")
        return response
    except Exception as e:
        print(f"[ERROR] Gemini analysis failed: {e}")
        return f"Error in analysis: {e}"

def extract_audio(video_path):
    print(f"[INFO] Extracting audio from video: {video_path}")
    try:
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        command = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", temp_audio.name, "-y"]
        os.system(' '.join(command))
        print(f"[INFO] Audio extracted to: {temp_audio.name}")
        return temp_audio.name
    except Exception as e:
        print(f"[ERROR] Failed to extract audio: {e}")
        return None

def analyze_video(gemini_api, detect_abusive, detect_violent, detect_nsfw, detect_political, detect_religious, video_path):
    if not (detect_abusive or detect_violent or detect_nsfw or detect_political or detect_religious):
        error_msg = "Error: At least one detection option must be selected."
        print(f"[ERROR] {error_msg}")
        return error_msg, [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], "", ""

    if not os.path.exists(video_path):
        print(f"[ERROR] File not found: {video_path}")
        return "Error: File not found", [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], "", ""

    audio_file = extract_audio(video_path)
    print("[INFO] Transcribing audio with Whisper...")
    audio_transcript = whisper_model.transcribe(audio_file, language="ur").get("text", "")
    print("[INFO] Transcription complete.")

    abusive_table = [["N/A", "Not analyzed"]]
    violent_table = [["N/A", "Not analyzed"]]
    nsfw_audio_table = [["N/A", "Not analyzed"]]
    political_table = [["N/A", "Not analyzed"]]
    religious_table = [["N/A", "Not analyzed"]]
    video_nsfw_info = ""
    video_violence_info = ""

    if detect_abusive:
        print("[INFO] Analyzing abusive content...")
        response_abusive = analyze_text_with_gemini(audio_transcript, gemini_api, Abusive_Content_Sys_Instructions)
        abusive_table = parse_response_table(response_abusive)

    violence_is_flagged = None
    if detect_violent:
        print("[INFO] Analyzing violent content...")
        response_violent = analyze_text_with_gemini(audio_transcript, gemini_api, Violence_Sys_Instructions)
        violent_table = parse_response_table(response_violent)
        try:
            violence_is_flagged = json.loads(re.sub(r"^```(?:json)?\s*|```$", "", response_violent.text)).get("is_flagged")
        except:
            pass

    if detect_nsfw:
        print("[INFO] Analyzing NSFW content...")
        response_nsfw_audio = analyze_text_with_gemini(audio_transcript, gemini_api, NSFW_Sys_Instructions)
        nsfw_audio_table = parse_response_table(response_nsfw_audio)

    if detect_political:
        print("[INFO] Analyzing political content...")
        response_political = analyze_text_with_gemini(audio_transcript, gemini_api, Politics_Sys_Instructions)
        political_table = parse_response_table(response_political)

    if detect_religious:
        print("[INFO] Analyzing religious content...")
        response_religious = analyze_text_with_gemini(audio_transcript, gemini_api, Religious_Sys_Instructions)
        religious_table = parse_response_table(response_religious)

    if detect_nsfw or detect_violent:
        print("[INFO] Running video content detection...")
        violence_detector_model_path = './violence/code/runs/20250305_175848/video_classifier_epoch_2.pth'
        nsfw_result, violence_result = run_detection_models(video_path, violence_detector_model_path, detect_nsfw, detect_violent)
        if detect_nsfw:
            video_nsfw_info += f"{nsfw_result}\n"
        if detect_violent:
            if (violence_is_flagged is not None) and (violence_is_flagged != violence_result):
                video_violence_info += f"{'NonViolence' if violence_is_flagged==False else 'Violence'}\n"
            else:
                video_violence_info += f"{violence_result}\n"

    print("[INFO] Cleaning up temporary files...")
    os.remove(audio_file)
    os.remove(video_path)
    print("[INFO] Analysis complete.")

    return (audio_transcript, abusive_table, violent_table, nsfw_audio_table,
            political_table, religious_table, video_nsfw_info, video_violence_info)

def parse_response_table(response):
    if isinstance(response, str):
        print(f"[WARNING] Response is an error string: {response}")
        return [["Error", response]]
    try:
        token_usage = response.usage_metadata
        cost_usd, cost_pkr = calculate_cost(token_usage.prompt_token_count, token_usage.candidates_token_count)
        cleaned = re.sub(r"^```(?:json)?\s*|```$", "", response.text, flags=re.MULTILINE).strip()
        data = json.loads(cleaned)
        data["LLM Cost Breakdown"] = {
            "input_tokens": token_usage.prompt_token_count,
            "output_tokens": token_usage.candidates_token_count,
            "cost_usd": cost_usd,
            "cost_pkr": cost_pkr
        }
        table = []
        for key, value in data.items():
            if isinstance(value, dict):
                sub_val = "\n".join([f"{k}: {v}" for k, v in value.items()])
                table.append([key, sub_val])
            elif isinstance(value, list):
                table.append([key, "\n".join(map(str, value))])
            else:
                table.append([key, str(value)])
        return table
    except Exception as e:
        print(f"[ERROR] Failed to parse Gemini response: {e}")
        return [["Error", f"Parsing error: {e}"]]