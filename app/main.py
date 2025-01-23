from flask import Flask, render_template, Response, request, redirect, url_for, send_file
from camera import VideoCamera
import threading
import cv2
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PROCESSED_FOLDER'] = 'processed/'

video_camera = None
global_frame = None

def update_frame():
    global global_frame, video_camera
    while True:
        if video_camera:
            frame = video_camera.get_frame()
            global_frame = frame

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_source', methods=['POST'])
def select_source():
    global video_camera
    source = request.form['source']
    if source == 'webcam':
        video_camera = VideoCamera(source=0)
    elif source == 'link':
        link = request.form['link']
        video_camera = VideoCamera(source=link)
    elif source == 'file':
        if 'file' not in request.files:
            return redirect(url_for('index'))
        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('index'))
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            return redirect(url_for('process_and_download', filename=file.filename))
    else:
        return redirect(url_for('index'))

    t = threading.Thread(target=update_frame)
    t.start()
    return redirect(url_for('index'))

def gen(camera, processed=False):
    global global_frame
    while True:
        if camera:
            try:
                frame = global_frame
                if frame is not None:
                    if processed:
                        frame = camera.process_frame(frame)
                        ret, jpeg = cv2.imencode('.jpg', frame)
                        if ret:
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
                    else:
                        ret, jpeg = cv2.imencode('.jpg', frame)
                        if ret:
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            except Exception as e:
                print(f"Error processing frame: {e}")

@app.route('/video_feed')
def video_feed():
    global video_camera
    if not video_camera:
        return "Video source not selected.", 400
    return Response(gen(video_camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/processed_video_feed')
def processed_video_feed():
    global video_camera
    if not video_camera:
        return "Video source not selected.", 400
    return Response(gen(video_camera, processed=True),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/process_and_download/<filename>')
def process_and_download(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    processed_file_path = os.path.join(app.config['PROCESSED_FOLDER'], f"processed_{filename}")

    # Create a VideoCamera instance for processing the file
    video_camera = VideoCamera(source=file_path)
    
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        return "Error: Could not open video file.", 500
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(processed_file_path, fourcc, fps, (width, height))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        processed_frame = video_camera.process_frame(frame)
        out.write(processed_frame)
    
    cap.release()
    out.release()
    
    return send_file(processed_file_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['PROCESSED_FOLDER']):
        os.makedirs(app.config['PROCESSED_FOLDER'])
    app.run(host='0.0.0.0', port=5000, debug=True)
