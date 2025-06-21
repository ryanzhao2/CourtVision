from ultralytics import YOLO

model = YOLO("../yolov8n.pt")

results = model.predict("input_videos/test.mp4", save=True, project="../output_videos", name="predict")

for box in results[0].boxes:
    print(box)
