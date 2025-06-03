import torch
import torchvision.transforms as transforms
import imageio
import os
import numpy as np
import torchvision.models as models
import torch.nn as nn

class CFG:
    epochs = 10
    batch_size = 1
    classes = ["Violence", "NonViolence"]

# Define PyTorch EfficientNet Model
class VideoClassifier(nn.Module):
    def __init__(self, num_classes=len(CFG.classes)):
        super(VideoClassifier, self).__init__()
        self.efficient_net = models.efficientnet_b0(pretrained=True)
        self.efficient_net.classifier[1] = nn.Linear(self.efficient_net.classifier[1].in_features, num_classes)
    
    def forward(self, x):
        batch_size, frames, C, H, W = x.shape
        x = x.view(batch_size * frames, C, H, W)
        x = self.efficient_net(x)
        x = x.view(batch_size, frames, -1)
        x = torch.mean(x, dim=1)
        return x
    
def format_frames(frame, output_size=(224, 224)):
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(output_size),
        transforms.ToTensor()
    ])
    return transform(frame)

def extract_frames(video_path, n_frames=30, frame_step=15, output_size=(224, 224)):
    reader = imageio.get_reader(video_path)
    frames = []
    for i, frame in enumerate(reader):
        if i % frame_step == 0:
            frame = format_frames(frame, output_size)
            frames.append(frame)
            if len(frames) == n_frames:
                break
    reader.close()
    if len(frames) < n_frames:
        padding = [torch.zeros_like(frames[0]) for _ in range(n_frames - len(frames))]
        frames.extend(padding)
    return torch.stack(frames)

def predict(video_path, model_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = VideoClassifier().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    frames = extract_frames(video_path)
    frames = frames.unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(frames)
        predicted_class = torch.argmax(outputs, dim=1).item()
    return CFG.classes[predicted_class]

def main(model_path, video_path):
    label = predict(video_path, model_path)
    return label