import cv2
from simple_facerec import SimpleFacerec

class VideoCamera:
    def __init__(self, source=0):
        self.video = cv2.VideoCapture(source)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.video.isOpened():
            raise Exception("Could not open video stream")
        self.sfr = SimpleFacerec()
        self.sfr.load_encoding_images("images")

    def __del__(self):
        if self.video.isOpened():
            self.video.release()

    def get_frame(self):
        ret, frame = self.video.read()
        if not ret:
            return None
        return frame

    def process_frame(self, frame):
        try:
            face_locations, face_names, keypoints_list = self.sfr.detect_known_faces(frame)
            for face_loc, name, keypoints in zip(face_locations, face_names, keypoints_list):
                y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

                # Draw facial features
                for key, point in keypoints.items():
                    cv2.circle(frame, (point[0], point[1]), 2, (0, 255, 0), -1)
            return frame
        except Exception as e:
            print(f"Error in process_frame: {e}")
            return frame
