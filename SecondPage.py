import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QSlider, QHBoxLayout, \
    QFileDialog, QLabel, QColorDialog, QFrame
from PyQt6 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import Qt

import time
import yfinance as yf
from pyqtgraph import mkPen
import pyqtgraph as pg

class RadarPlotWidget(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi, subplot_kw=dict(polar=True))
        super(RadarPlotWidget, self).__init__(fig)
        self.line_color = '#287fd5'
    def update_line_color(self, line_color):
        self.line_color = line_color
    def update_plot(self, data):
        self.ax.clear()
        self.angles = np.linspace(0, 2 * np.pi, len(data), endpoint=False)
        self.ax.plot(self.angles, data, color=self.line_color, linewidth=2)
        max_amplitude = np.max(np.abs(data))
        self.ax.set_ylim(-1.2 * max_amplitude, 1.2 * max_amplitude)
        self.draw()

class SecondPage(QtWidgets.QWidget):
    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Waveform Viewer')
        self.parent.setGeometry(100, 100, 1000, 600)

        with open("./Styles/second.qss", "r") as f:
            self.setStyleSheet(f.read())

        general_layout = QtWidgets.QVBoxLayout()

        general_radar_frame = QFrame()
        general_radar_frame.setObjectName("general_radar_frame")
        general_real_time_signal_frame = QFrame()
        general_real_time_signal_frame.setObjectName("general_real_time_signal_frame")
        # set fixed size full screen width and 400 height
        general_real_time_signal_frame.setFixedHeight(350)

        ################################################# Real Time Signal Widget ################################
        
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        general_real_time_signal_frame.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(20)

        self.isPaused = False
        self.isConnected = True

        self.leftFrame = QFrame()
        self.leftLayout = QtWidgets.QVBoxLayout()
        self.leftFrame.setLayout(self.leftLayout)
        self.leftLayout.setSpacing(20)

        self.back_to_first_page_button = QtWidgets.QPushButton()
        back_icon = QtGui.QIcon()
        back_icon.addPixmap(QtGui.QPixmap("./Icons/pics/bx--arrow-back.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.back_to_first_page_button.setIcon(back_icon)
        self.back_to_first_page_button.setMinimumHeight(30)
        self.back_to_first_page_button.setFixedWidth(50)
        general_layout.addWidget(self.back_to_first_page_button)

        self.graph_widget = pg.PlotWidget()
        self.graph_widget.showGrid(x=True, y=True)
        self.leftLayout.addWidget(self.graph_widget)

        # self.cineModeLayout = QtWidgets.QHBoxLayout()
        # self.cineModeLayout.setSpacing(5)
        # self.cineModeLayout.setContentsMargins(0, 0, 0, 0)
        # self.cineModeLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.pauseIcon = QtGui.QIcon()
        self.pauseIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--pause.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.playIcon = QtGui.QIcon()
        self.playIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--play.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)

        self.playPauseButton = QtWidgets.QPushButton()
        # self.playPauseButton.setFixedWidth(50)
        self.playPauseButton.setIcon(self.pauseIcon)
        self.playPauseButton.clicked.connect(self.play_pause)
        # self.cineModeLayout.addWidget(self.playPauseButton)
        # self.leftLayout.addLayout(self.cineModeLayout)

        self.mainLayout.addWidget(self.leftFrame)

        real_time_control_frame = QFrame()
        real_time_control_frame.setFixedWidth(250)
        real_time_control_layout = QtWidgets.QVBoxLayout()
        real_time_control_frame.setLayout(real_time_control_layout)
        real_time_control_layout.addWidget(self.playPauseButton)

        self.signalListWidget = QtWidgets.QListWidget()
        # self.signalListWidget.setFixedSize(250,250)
        self.signalListWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        # self.signalListWidget.setFixedSize(180, 250)
        self.signalListWidget.itemChanged.connect(self.update_play_button_state)
        real_time_control_layout.addWidget(self.signalListWidget)
        self.mainLayout.addWidget(real_time_control_frame)

        self.back_to_first_page_button.clicked.connect(self.back_to_first_page)
        self.playPauseButton.clicked.connect(self.connect_real_time_signal)
        
        ################################################# Radar Widget ################################


        self.radar_plot1 = RadarPlotWidget()
        self.radar_plot2 = RadarPlotWidget()
        self.timer1 = QtCore.QTimer(self)
        self.timer2 = QtCore.QTimer(self)
        self.timer1.timeout.connect(self.update_waveform1)
        self.timer2.timeout.connect(self.update_waveform2)
        self.init_plot_vars()

        main_layout = QtWidgets.QVBoxLayout()
        general_radar_frame.setLayout(main_layout)

        plots_layout = QtWidgets.QHBoxLayout()

        radar_1_frame = QFrame()
        radar_1_layout = QtWidgets.QVBoxLayout()
        radar_1_frame.setLayout(radar_1_layout)
        radar_1_layout.setSpacing(20)
        radar_1_layout.setObjectName("radar_1_layout")
        radar_1_layout.addWidget(self.radar_plot1)

        radar_2_frame = QFrame()
        radar_2_layout = QtWidgets.QVBoxLayout()
        radar_2_frame.setLayout(radar_2_layout)
        radar_2_layout.setSpacing(20)
        radar_2_layout.setObjectName("radar_2_layout")
        radar_2_layout.addWidget(self.radar_plot2)

        plots_layout.addWidget(radar_1_frame)
        plots_layout.addWidget(radar_2_frame)

        main_layout.addLayout(plots_layout)

        controls1 = self.create_controls(1)
        controls2 = self.create_controls(2)
        radar_1_layout.addLayout(controls1)
        radar_2_layout.addLayout(controls2)

        self.timer = QtCore.QTimer()  
        self.timer.setInterval(1000)  
        self.timer.timeout.connect(self.fetch_real_time_signal)

        general_layout.addWidget(general_real_time_signal_frame)
        general_layout.addWidget(general_radar_frame)
        self.setLayout(general_layout)

    def update_play_button_state(self):
        has_selected = any(item.checkState() == QtCore.Qt.CheckState.Checked for item in self.signalListWidget.findItems("*", QtCore.Qt.MatchFlag.MatchWildcard))
        self.playPauseButton.setEnabled(has_selected)

    def play_pause(self):
        if self.isPaused:
            self.timer.start()
            self.playPauseButton.setIcon(self.pauseIcon)
        else:
            self.timer.stop()
            self.playPauseButton.setIcon(self.playIcon)
        self.isPaused = not self.isPaused
        
    def connect_real_time_signal(self):
        if self.isConnected:
            itemIsExist = []
            newItem = "AAPL finance"
            item = QtWidgets.QListWidgetItem(newItem)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsSelectable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            
            for index in range(self.signalListWidget.count()):
                if self.signalListWidget.item(index).text() == newItem:
                    itemIsExist.append(True)      
                else:  
                    itemIsExist.append(False)
            if True in itemIsExist:
                pass
            else:
                self.signalListWidget.addItem(item)     
            
            self.times = []  
            self.prices = []  
            
            self.timer.start()
        else:
            self.timer.stop()
        self.isConnected = not self.isConnected

    def fetch_real_time_signal(self):
        ticker = yf.Ticker("AAPL")
        real_time_data = ticker.info
        currentTime = time.time()
        
        self.prices.append(real_time_data['currentPrice'])
        self.times.append(currentTime)
        
        if not hasattr(self, 'real_time_plot'):  
            pen = mkPen(color='blue', width=2, style=QtCore.Qt.PenStyle.SolidLine)
            self.real_time_plot = self.graph_widget.plot(self.times, self.prices, pen=pen)
        else:
            self.real_time_plot.setData(self.times, self.prices) 
  
    def back_to_first_page(self):
        self.parent.show_first_page()

    def init_plot_vars(self):
        self.row_idx1 = 0
        self.row_idx2 = 0
        self.is_playing1 = False
        self.is_playing2 = False
        self.timer_interval = 100
        self.data_chunk_size = 5

    def create_controls(self, plot_number):
        control_layout = QtWidgets.QHBoxLayout()
        control_layout.setSpacing(10)

        cine_control_layout = QtWidgets.QHBoxLayout()
        backward_button = QtWidgets.QPushButton()
        backwardIcon = QtGui.QIcon()

        backwardIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--backward.png"),
                                    QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        backward_button.setIcon(backwardIcon)

        if plot_number == 1:
            backward_button.clicked.connect(self.backward_waveform1)
        else:
            backward_button.clicked.connect(self.backward_waveform2)
        cine_control_layout.addWidget(backward_button)

        play_button = QtWidgets.QPushButton()
        playIcon = QtGui.QIcon()

        playIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--play.png"),
                                QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        play_button.setIcon(playIcon)

        if plot_number == 1:
            play_button.clicked.connect(self.play_waveform1)
        else:
            play_button.clicked.connect(self.play_waveform2)
        cine_control_layout.addWidget(play_button)

        forward_button = QtWidgets.QPushButton()
        forwardIcon = QtGui.QIcon()

        forwardIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--forward.png"),
                                   QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        forward_button.setIcon(forwardIcon)

        if plot_number == 1:
            forward_button.clicked.connect(self.forward_waveform1)
        else:
            forward_button.clicked.connect(self.forward_waveform2)
        cine_control_layout.addWidget(forward_button)

        pause_button = QtWidgets.QPushButton()
        pauseIcon = QtGui.QIcon()

        pauseIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--pause.png"),
                                 QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        pause_button.setIcon(pauseIcon)

        if plot_number == 1:
            pause_button.clicked.connect(self.pause_waveform1)
        else:
            pause_button.clicked.connect(self.pause_waveform2)
        cine_control_layout.addWidget(pause_button)

        control_layout.addLayout(cine_control_layout)

        upload_button = QtWidgets.QPushButton('Upload CSV')
        upload_button.setMinimumHeight(30)
        uploadIcon = QtGui.QIcon()
        uploadIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--upload.png"),
                                  QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        upload_button.setIcon(uploadIcon)
        if plot_number == 1:
            upload_button.clicked.connect(self.load_csv1)
        else:
            upload_button.clicked.connect(self.load_csv2)
        control_layout.addWidget(upload_button)

        line_color_button = QtWidgets.QPushButton('Fill Color')
        line_color_button.setMinimumHeight(30)
        if plot_number == 1:
            line_color_button.clicked.connect(self.choose_line_color1)
        else:
            line_color_button.clicked.connect(self.choose_line_color2)
        control_layout.addWidget(line_color_button)
        return control_layout
    
    def load_csv1(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            csv_data = pd.read_csv(file_name)
        if csv_data.shape[1] != 1:
            raise ValueError("CSV file must contain exactly 1 column.")
        self.waveform_data1 = csv_data.iloc[:, 0].to_numpy()
        self.row_idx1 = 1
        self.radar_plot1.update_plot(self.waveform_data1[:self.row_idx1])

    def load_csv2(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            csv_data = pd.read_csv(file_name)
        if csv_data.shape[1] != 1:
            raise ValueError("CSV file must contain exactly 1 column.")
        self.waveform_data2 = csv_data.iloc[:, 0].to_numpy()
        self.row_idx2 = 1
        self.radar_plot2.update_plot(self.waveform_data2[:self.row_idx2])

    def choose_line_color1(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.radar_plot1.update_line_color(color.name())

    def choose_line_color2(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.radar_plot2.update_line_color(color.name())

    def play_waveform1(self):
        self.is_playing1 = True
        self.timer1.start(self.timer_interval)

    def play_waveform2(self):
        self.is_playing2 = True
        self.timer2.start(self.timer_interval)

    def pause_waveform1(self):
        self.is_playing1 = False
        self.timer1.stop()

    def pause_waveform2(self):
        self.is_playing2 = False
        self.timer2.stop()

    def update_waveform1(self):
        if hasattr(self, 'waveform_data1') and len(self.waveform_data1) > 0:
            end_idx = self.row_idx1 + self.data_chunk_size
            if end_idx < len(self.waveform_data1):
                self.row_idx1 = end_idx
                self.radar_plot1.update_plot(self.waveform_data1[:self.row_idx1])
            else:
                self.pause_waveform1()

    def update_waveform2(self):
        if hasattr(self, 'waveform_data2') and len(self.waveform_data2) > 0:
            end_idx = self.row_idx2 + self.data_chunk_size
            if end_idx < len(self.waveform_data2):
                self.row_idx2 = end_idx
                self.radar_plot2.update_plot(self.waveform_data2[:self.row_idx2])
            else:
                self.pause_waveform2()

    def backward_waveform1(self):
        if hasattr(self, 'waveform_data1'):
            self.row_idx1 = max(0, self.row_idx1 - self.data_chunk_size)
            self.radar_plot1.update_plot(self.waveform_data1[:self.row_idx1])

    def backward_waveform2(self):
        if hasattr(self, 'waveform_data2'):
            self.row_idx2 = max(0, self.row_idx2 - self.data_chunk_size)
            self.radar_plot2.update_plot(self.waveform_data2[:self.row_idx2])

    def forward_waveform1(self):
        if hasattr(self, 'waveform_data1'):
            self.row_idx1 = min(len(self.waveform_data1), self.row_idx1 + self.data_chunk_size)
            self.radar_plot1.update_plot(self.waveform_data1[:self.row_idx1])

    def forward_waveform2(self):
        if hasattr(self, 'waveform_data2'):
            self.row_idx2 = min(len(self.waveform_data2), self.row_idx2 + self.data_chunk_size)
            self.radar_plot2.update_plot(self.waveform_data2[:self.row_idx2])

    def back_to_first_page(self):
        self.parent.show_first_page()

# if __name__ == '__main__':
#     app = QApplication([])
#     main_window = QMainWindow()
#     non_rec_page = NonRecPage(main_window)
#     main_window.setCentralWidget(non_rec_page)
#     main_window.show()
#     app.exec()