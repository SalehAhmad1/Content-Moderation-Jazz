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
whisper_model = whisper.load_model("medium", device=device)

def calculate_cost(input_tokens, output_tokens):
    input_price = 0.075 if input_tokens <= 128000 else 0.15  # Per million tokens
    output_price = 0.30 if output_tokens <= 128000 else 0.60  # Per million tokens
    cost = ((input_tokens / 1_000_000.0) * input_price) + ((output_tokens / 1_000_000.0) * output_price)
    return round(cost, 8), round(cost, 8) * 280.0

def run_detection_models(video_path, violence_model_path, detect_nsfw, detect_violent):
    nsfw_result, violence_result = None, None
    with ThreadPoolExecutor() as executor:
        futures = {}
        if detect_nsfw:
            futures["nsfw"] = executor.submit(nsfw_detector, video_path=video_path)
        if detect_violent:
            futures["violence"] = executor.submit(violence_detector, model_path=violence_model_path, video_path=video_path)
        nsfw_result = futures.get("nsfw").result() if "nsfw" in futures else None
        violence_result = futures.get("violence").result() if "violence" in futures else None
    return nsfw_result, violence_result

def analyze_text_with_gemini(urdu_text, api_key, sys_instruct):
    prompt = ("Analyze this Urdu transcript for harmful content: "
              f"{urdu_text}"
              " Do not generate any additional content other than the JSON result. "
              "Use this JSON schema: "
              "Result = { "
              "    'is_flagged': bool, "
              "    'tags': list[str], "
              "    'reasons': list[str], "
              "    'severity': str "
              "}"
              " Return: Result.")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-1.5-flash-002',
            config=types.GenerateContentConfig(system_instruction=sys_instruct, temperature=0.0),
            contents=prompt,
        )
        return response
    except Exception as e:
        return f"Error in analysis: {e}"
    
def extract_audio(video_path):
    """Extracts audio from video and saves it as MP3."""
    try:
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        command = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", temp_audio.name, "-y"]
        os.system(' '.join(command))
        return temp_audio.name
    except Exception as e:
        return None

def analyze_video(gemini_api, detect_abusive, detect_violent, detect_nsfw, detect_political, detect_religious, video_path):
    # Check if at least one detection option is selected
    if not (detect_abusive or detect_violent or detect_nsfw or detect_political or detect_religious):
        error_msg = "Error: At least one detection option must be selected."
        return error_msg, [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], "", ""
    
    # Ensure the file exists 
    if not os.path.exists(video_path):
        return "Error: File not found", [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], [["N/A", ""]], "", ""
    
    # Extract audio and transcribe using Whisper
    audio_file = extract_audio(video_path)
    audio_transcript = whisper_model.transcribe(audio_file, language="ur").get("text", "")
    
    # Initialize table variables for JSON outputs
    abusive_table = [["N/A", "Not analyzed"]]
    violent_table = [["N/A", "Not analyzed"]]
    nsfw_audio_table = [["N/A", "Not analyzed"]]
    political_table = [["N/A", "Not analyzed"]]
    religious_table = [["N/A", "Not analyzed"]]
    # Video detection outputs remain as text
    video_nsfw_info = ""
    video_violence_info = ""
    
    # Abusive Content Analysis (Audio)
    if detect_abusive:
        response_abusive = analyze_text_with_gemini(audio_transcript, gemini_api, Abusive_Content_Sys_Instructions)
        if not isinstance(response_abusive, str):
            token_usage = response_abusive.usage_metadata
            cost_usd, cost_pkr = calculate_cost(token_usage.prompt_token_count, token_usage.candidates_token_count)
            try:
                cleaned = re.sub(r"^```(?:json)?\s*|```$", "", response_abusive.text, flags=re.MULTILINE).strip()
                data = json.loads(cleaned)
                data["LLM Cost Breakdown"] = {
                    "input_tokens": token_usage.prompt_token_count,
                    "output_tokens": token_usage.candidates_token_count,
                    "cost_usd": cost_usd,
                    "cost_pkr": cost_pkr
                }
                abusive_table = []
                for key, value in data.items():
                    if isinstance(value, dict):
                        sub_val = "\n".join([f"{k}: {v}" for k, v in value.items()])
                        abusive_table.append([key, sub_val])
                    elif isinstance(value, list):
                        abusive_table.append([key, "\n".join(map(str, value))])
                    else:
                        abusive_table.append([key, str(value)])
            except Exception as e:
                abusive_table = [["Error", f"Parsing error: {e}"]]
        else:
            abusive_table = [["Error", response_abusive]]
    
    # Violent Content Analysis (Audio)
    violence_is_flagged = None
    if detect_violent:
        response_violent = analyze_text_with_gemini(audio_transcript, gemini_api, Violence_Sys_Instructions)
        if not isinstance(response_violent, str):
            token_usage = response_violent.usage_metadata
            cost_usd, cost_pkr = calculate_cost(token_usage.prompt_token_count, token_usage.candidates_token_count)
            try:
                cleaned = re.sub(r"^```(?:json)?\s*|```$", "", response_violent.text, flags=re.MULTILINE).strip()
                data = json.loads(cleaned)
                data["LLM Cost Breakdown"] = {
                    "input_tokens": token_usage.prompt_token_count,
                    "output_tokens": token_usage.candidates_token_count,
                    "cost_usd": cost_usd,
                    "cost_pkr": cost_pkr
                }
                violent_table = []
                for key, value in data.items():
                    if isinstance(value, dict):
                        sub_val = "\n".join([f"{k}: {v}" for k, v in value.items()])
                        violent_table.append([key, sub_val])
                    elif isinstance(value, list):
                        violent_table.append([key, "\n".join(map(str, value))])
                    else:
                        violent_table.append([key, str(value)])
                try:
                    violence_is_flagged = data.get("is_flagged")
                except Exception:
                    violence_is_flagged = None
            except Exception as e:
                violent_table = [["Error", f"Parsing error: {e}"]]
        else:
            violent_table = [["Error", response_violent]]
    
    # NSFW Content Analysis (Audio)
    if detect_nsfw:
        response_nsfw_audio = analyze_text_with_gemini(audio_transcript, gemini_api, NSFW_Sys_Instructions)
        if not isinstance(response_nsfw_audio, str):
            token_usage = response_nsfw_audio.usage_metadata
            cost_usd, cost_pkr = calculate_cost(token_usage.prompt_token_count, token_usage.candidates_token_count)
            try:
                cleaned = re.sub(r"^```(?:json)?\s*|```$", "", response_nsfw_audio.text, flags=re.MULTILINE).strip()
                data = json.loads(cleaned)
                data["LLM Cost Breakdown"] = {
                    "input_tokens": token_usage.prompt_token_count,
                    "output_tokens": token_usage.candidates_token_count,
                    "cost_usd": cost_usd,
                    "cost_pkr": cost_pkr
                }
                nsfw_audio_table = []
                for key, value in data.items():
                    if isinstance(value, dict):
                        sub_val = "\n".join([f"{k}: {v}" for k, v in value.items()])
                        nsfw_audio_table.append([key, sub_val])
                    elif isinstance(value, list):
                        nsfw_audio_table.append([key, "\n".join(map(str, value))])
                    else:
                        nsfw_audio_table.append([key, str(value)])
            except Exception as e:
                nsfw_audio_table = [["Error", f"Parsing error: {e}"]]
        else:
            nsfw_audio_table = [["Error", response_nsfw_audio]]
    
    # Political Content Analysis (Audio)
    if detect_political:
        response_political = analyze_text_with_gemini(audio_transcript, gemini_api, Politics_Sys_Instructions)
        if not isinstance(response_political, str):
            token_usage = response_political.usage_metadata
            cost_usd, cost_pkr = calculate_cost(token_usage.prompt_token_count, token_usage.candidates_token_count)
            try:
                cleaned = re.sub(r"^```(?:json)?\s*|```$", "", response_political.text, flags=re.MULTILINE).strip()
                data = json.loads(cleaned)
                data["LLM Cost Breakdown"] = {
                    "input_tokens": token_usage.prompt_token_count,
                    "output_tokens": token_usage.candidates_token_count,
                    "cost_usd": cost_usd,
                    "cost_pkr": cost_pkr
                }
                political_table = []
                for key, value in data.items():
                    if isinstance(value, dict):
                        sub_val = "\n".join([f"{k}: {v}" for k, v in value.items()])
                        political_table.append([key, sub_val])
                    elif isinstance(value, list):
                        political_table.append([key, "\n".join(map(str, value))])
                    else:
                        political_table.append([key, str(value)])
            except Exception as e:
                political_table = [["Error", f"Parsing error: {e}"]]
        else:
            political_table = [["Error", response_political]]
    
    # Religious Content Analysis (Audio)
    if detect_religious:
        response_religious = analyze_text_with_gemini(audio_transcript, gemini_api, Religious_Sys_Instructions)
        if not isinstance(response_religious, str):
            token_usage = response_religious.usage_metadata
            cost_usd, cost_pkr = calculate_cost(token_usage.prompt_token_count, token_usage.candidates_token_count)
            try:
                cleaned = re.sub(r"^```(?:json)?\s*|```$", "", response_religious.text, flags=re.MULTILINE).strip()
                data = json.loads(cleaned)
                data["LLM Cost Breakdown"] = {
                    "input_tokens": token_usage.prompt_token_count,
                    "output_tokens": token_usage.candidates_token_count,
                    "cost_usd": cost_usd,
                    "cost_pkr": cost_pkr
                }
                religious_table = []
                for key, value in data.items():
                    if isinstance(value, dict):
                        sub_val = "\n".join([f"{k}: {v}" for k, v in value.items()])
                        religious_table.append([key, sub_val])
                    elif isinstance(value, list):
                        religious_table.append([key, "\n".join(map(str, value))])
                    else:
                        religious_table.append([key, str(value)])
            except Exception as e:
                religious_table = [["Error", f"Parsing error: {e}"]]
        else:
            religious_table = [["Error", response_religious]]
    
    # Video Content Analysis (Detection Models)
    if detect_nsfw or detect_violent:
        violence_detector_model_path = './violence/code/runs/20250305_175848/video_classifier_epoch_2.pth'
        nsfw_result, violence_result = run_detection_models(video_path, violence_detector_model_path, detect_nsfw, detect_violent)
        if detect_nsfw:
            video_nsfw_info += f"{nsfw_result}\n"
        if detect_violent:
            if (violence_is_flagged is not None) and (violence_is_flagged != violence_result):
                video_violence_info += f"{'NonViolence' if violence_is_flagged==False else 'Violence'}\n"
            else:
                video_violence_info += f"{violence_result}\n"
    
    # Clean up temporary files
    os.remove(audio_file)
    os.remove(video_path)
    
    return (audio_transcript, abusive_table, violent_table, nsfw_audio_table,
            political_table, religious_table, video_nsfw_info, video_violence_info)