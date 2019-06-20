import sys
import cv2
import time
import threading
from random import randint
from functools import partial
from utils.RoI import get_regions_with_detection
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtRemoveInputHook, QTimer, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QLabel, QFileDialog
from PyQt5 import uic

Ui_MainWindow, QtBaseClass = uic.loadUiType('data/VisualUI.ui')


class MyApp(QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.camera = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
        self.WIDTH, self.HEIGHT = (850, 550)
        status, _ = self.camera.read()

        menu_bar = self.menuBar()
        action_menu = menu_bar.addMenu('&Actions')

        load_menu = action_menu.addMenu('&Load From')

        # From Camera
        self.camera_action = QAction('&Camera', self)

        if status == False:
            self.camera_action.setEnabled(False)

        self.camera_action.triggered.connect(self.start_cam)
        load_menu.addAction(self.camera_action)

        self.ui.detectButton.clicked.connect(self.detect_objects)

        # From Local
        self.local_action = QAction('&Local', self)
        self.local_action.triggered.connect(self.load_local)
        load_menu.addAction(self.local_action)

        # Save Current Frame
        self.save_frame_action = QAction('&Save Frame', self)
        self.save_frame_action.setShortcut("Ctrl+S")
        self.save_frame_action.triggered.connect(self.save_frame)
        action_menu.addAction(self.save_frame_action)

        # Some Working Variables
        self.CLOSE_ALL_THREAD = False
        self.RUN_FRAMES_FROM_CAMERA = True
        self.MODE = "CAM" # Can be "CAM" or "LOC"
        self.frame = None
        self.t1 = threading.Thread(target=self.runVideoFromCam, args=())
        self.t1.start()
        
    
    def detect_objects(self):
        threading.Thread(target=self.detect_objects_sub, args=()).start()

    def detect_objects_sub(self):
        if self.ui.detectButton.text() == "New\n":
            if self.MODE == "LOC":
                self.load_local()
                return
                
            self.start_cam()
            self.ui.detectButton.setText("DETECT\n")
            return

        self.pause_cam()
        self.ui.detectButton.setEnabled(False)
        self.ui.detectButton.setText("WAIT\n")
        print("[DEBUG] :: Getting RoI and Detecting Segments!")
        final_res = get_regions_with_detection(self.frame)
        print("[DEBUG] :: Drawing Boxes")

        for obj, proba, bbox in final_res:
            x, y, w, h = bbox
            color = (randint(0,255), randint(0,255), randint(0,255))
            self.frame = cv2.rectangle(self.frame, (x, y), (x+w, y+h), color, 2)
            self.frame = cv2.putText(self.frame, obj.upper()+' > '+str(proba*100)[:4], (x+10,y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        self.display_mat_frame(self.frame)
        self.ui.detectButton.setText("New\n")
        self.ui.detectButton.setEnabled(True)

    def closeEvent(self, event):
        self.CLOSE_ALL_THREAD = True

    def runVideoFromCam(self):
        """
        Type: EventListener
        Must Run Infinitely all time!
        Must be called Once Only!
        
        :return: None
        """

        while True:
            if self.CLOSE_ALL_THREAD:
                break

            if self.RUN_FRAMES_FROM_CAMERA:
                ret, self.frame = self.camera.read()
                self.frame = cv2.cvtColor(cv2.resize(self.frame, (self.WIDTH, self.HEIGHT)), cv2.COLOR_BGR2RGB)
                if ret:
                    self.display_mat_frame(self.frame)

    def display_mat_frame(self, mat_src):
        height, width, channels = mat_src.shape
        bytesPerLine = width * channels
        qImg = QImage(mat_src.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixmap01 = QPixmap.fromImage(qImg)
        pixmap_image = QPixmap(pixmap01)
        self.ui.frame_display.setPixmap(pixmap_image)

    def load_local(self):
        self.pause_cam()
        fileName, _ = QFileDialog.getOpenFileName(self,"Select Image File", "C:/Users/Public/Pictures/","All Picture Files (*.jpg *.png *jpeg *.tif)")
        if fileName == '':
            if self.MODE == "CAM":
                self.start_cam()
            return

        self.MODE = "LOC"
        self.frame = cv2.resize(cv2.cvtColor(cv2.imread(fileName), cv2.COLOR_BGR2RGB), (self.WIDTH, self.HEIGHT))
        self.display_mat_frame(self.frame)
        self.ui.detectButton.setText("DETECT\n")

    def save_frame(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save File', 'C:/Users/Public/Pictures/frame_'+str(time.time())+'.jpg', 'All Picture Files (*.jpg *.png *jpeg *.tif)')
        if filename == '':
            return
        
        cv2.imwrite(filename, self.frame)

    def pause_cam(self):
        self.RUN_FRAMES_FROM_CAMERA = False

    def start_cam(self):
        self.MODE = "CAM"
        self.RUN_FRAMES_FROM_CAMERA = True


if __name__ == '__main__':
    pyqtRemoveInputHook()
    app = QApplication(sys.argv)
    window = MyApp()
    window.setWindowTitle('Eye-o-Father | EOF')
    window.show()
    sys.exit(app.exec())
