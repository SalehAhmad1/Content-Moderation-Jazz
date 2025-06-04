import os
import cv2
import torch
import matplotlib.pyplot as plt
from transformers import ViTImageProcessor, AutoModelForImageClassification, pipeline
from PIL import Image
import shutil
# from ultralytics import YOLO

# class HumanDetector:
#     def __init__(self, model_path="yolo11n.pt"):
#         self.model = YOLO(model_path)
#         self.device = "cuda" if torch.cuda.is_available() else "cpu"
#         self.model.to(self.device)

#     def detect_person(self, image_path):
#         results = self.model(image_path)
        
#         for result in results:
#             names = [result.names[cls.item()] for cls in result.boxes.cls.int()]
#             if "person" in names:
#                 return True  # Person detected
#         return False  # No person detected

# Load Model 1: ViT-based NSFW detector
print("Loading ViT-based NSFW detector...")
processor = ViTImageProcessor.from_pretrained('AdamCodd/vit-base-nsfw-detector')
model = AutoModelForImageClassification.from_pretrained('AdamCodd/vit-base-nsfw-detector')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"ViT model loaded on {device}.")

# Load Model 2: NSFW image classifier
print("Loading pipeline-based NSFW image classifier...")
pipe = pipeline("image-classification", model="quentintaranpino/nsfw-image-classifier")
print("Pipeline model loaded.")

# NSFW Threshold for Model 2
threshold = 0.60

def extract_frames(video_path, output_dir, frame_interval=1):
    """Extracts frames from a video at a specified interval."""
    print("Extracting frames from video...")
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    extracted_frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_path = os.path.join(output_dir, f"frame_{frame_count}.jpg")
            cv2.imwrite(frame_path, frame)
            extracted_frames.append(frame_path)
            print(f"Extracted frame {frame_count} to {frame_path}")

        frame_count += 1

    cap.release()
    print(f"Total frames extracted: {len(extracted_frames)}")
    return extracted_frames

def process_images_vit(image_paths, batch_size=256):
    """Processes images using the ViT-based NSFW model in batches."""
    print("Processing images using ViT-based model...")
    vit_predictions = {}
    n = len(image_paths)

    for i in range(0, n, batch_size):
        batch_paths = image_paths[i:i+batch_size]
        print(f"Processing ViT batch {i // batch_size + 1} with {len(batch_paths)} images...")
        # Load and convert images in batch
        images = [Image.open(path).convert("RGB") for path in batch_paths]
        inputs = processor(images=images, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
        logits = outputs.logits  # Shape: (batch_size, num_classes)

        # Process each image in the batch
        for j, path in enumerate(batch_paths):
            predicted_class_idx = logits[j].argmax().item()
            predicted_label = model.config.id2label[predicted_class_idx]
            vit_predictions[path] = predicted_label
            print(f"ViT prediction for {path}: {predicted_label}")

    print("ViT processing complete.")
    return vit_predictions

def process_images_pipeline(image_paths, batch_size=256):
    """Processes images using the pipeline-based NSFW classifier in batches."""
    print("Processing images using pipeline-based classifier...")
    pipeline_predictions = {}
    n = len(image_paths)

    for i in range(0, n, batch_size):
        batch_paths = image_paths[i:i+batch_size]
        print(f"Processing pipeline batch {i // batch_size + 1} with {len(batch_paths)} images...")
        # Load images in batch
        images = [Image.open(path).convert("RGB") for path in batch_paths]
        # The pipeline can process a list of images
        results = pipe(images)

        # When batch size is greater than 1, results is a list of lists:
        for path, result in zip(batch_paths, results):
            # If result is a list (for multi-label outputs) then extract scores
            scores = {entry['label']: entry['score'] for entry in result} if isinstance(result, list) else {result['label']: result['score']}
            nsfw_score = scores.get("UNSAFE", 0) + scores.get("QUESTIONABLE", 0)
            final_label = "NSFW" if nsfw_score > threshold else "SFW"
            pipeline_predictions[path] = final_label
            if final_label == "NSFW":
                print(f"Pipeline prediction for {path}: {final_label} (score: {nsfw_score})")
            else:
                print(f"Pipeline prediction for {path}: {final_label} (score: {1.0-nsfw_score})")

    print("Pipeline processing complete.")
    return pipeline_predictions

def count_predictions(pred_dict):
    """
    Count 'sfw' and 'nsfw' labels in a given dictionary.
    """
    counts = {"sfw": 0, "nsfw": 0}
    for label in pred_dict.values():
        if label.lower() == "sfw":
            counts["sfw"] += 1
        elif label.lower() == "nsfw":
            counts["nsfw"] += 1
    return counts

def empty_cuda():
    # Empty GPU memory after ViT processing
    if torch.cuda.is_available():
        print("Emptying CUDA cache...")
        torch.cuda.empty_cache()
        print("CUDA cache emptied.")

def main(video_path, frame_interval=1):
    """Main function: Extracts frames, runs models, and determines NSFW status."""
    print(f"Starting NSFW detection for video: {video_path}")
    output_dir = "video_frames"
    # Remove the directory if it exists, otherwise create it
    if os.path.exists(output_dir):
        print("Removing existing frames directory...")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    frames = extract_frames(video_path, output_dir, frame_interval)

    if not frames:
        print("No frames extracted. Exiting.")
        return "Error"

    print("Running ViT-based model on extracted frames...")
    vit_results = process_images_vit(frames, batch_size=512)

    empty_cuda()

    print("Running pipeline-based classifier on extracted frames...")
    pipeline_results = process_images_pipeline(frames, batch_size=512)
    
    # Combine the predictions for each frame
    combined_results = {}
    for frame in vit_results.keys():
        label_vit = vit_results.get(frame, "sfw").lower()
        label_pipe = pipeline_results.get(frame, "sfw").lower()
        
        # If either prediction is nsfw, mark the frame as nsfw.
        if label_vit == "nsfw" or label_pipe == "nsfw":
            combined_results[frame] = "nsfw"
        else:
            combined_results[frame] = "sfw"

    # Count the combined results
    counts = {"sfw": 0, "nsfw": 0}
    for label in combined_results.values():
        if label == "sfw":
            counts["sfw"] += 1
        elif label == "nsfw":
            counts["nsfw"] += 1

    print("Counts:", counts)

    total_frames = counts["sfw"] + counts["nsfw"]
    nsfw_percentage = counts["nsfw"] / total_frames if total_frames > 0 else 0

    if nsfw_percentage >= 0.05:
        final_decision = "NSFW (Not Safe For Work)"
    else:
        final_decision = "SFW (Safe For Work)"

    print("Final Decision:", final_decision)
    empty_cuda()
    return final_decision