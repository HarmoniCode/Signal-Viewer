import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QSlider, QHBoxLayout, \
    QFileDialog, QLabel, QColorDialog, QFrame
from PyQt6 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import Qt


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


class NonRecPage(QtWidgets.QWidget):
    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Waveform Viewer')
        self.parent.setGeometry(100, 100, 1000, 600)

        self.radar_plot = RadarPlotWidget()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_waveform)

        self.init_plot_vars()

        main_layout = QtWidgets.QVBoxLayout()

        horizontal_control = QtWidgets.QHBoxLayout()
        backIcon = QtGui.QIcon()
        backIcon.addPixmap(QtGui.QPixmap("./control/pics/bx--arrow-back.png"), QtGui.QIcon.Mode.Normal,
                           QtGui.QIcon.State.On)
        self.back_to_first_page_button = QtWidgets.QPushButton()
        self.back_to_first_page_button.setIcon(backIcon)
        self.back_to_first_page_button.setMinimumHeight(30)
        self.back_to_first_page_button.setFixedWidth(50)
        self.back_to_first_page_button.clicked.connect(self.back_to_first_page)
        horizontal_control.addWidget(self.back_to_first_page_button)
        horizontal_control.addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))

        main_layout.addLayout(horizontal_control)


        main_layout.addWidget(self.radar_plot)

        controls = self.create_controls()
        main_layout.addLayout(controls)

        self.setLayout(main_layout)

    def init_plot_vars(self):
        self.row_idx = 0
        self.is_playing = False
        self.timer_interval = 50
        self.data_chunk_size = 5

    def create_controls(self):
        control_layout = QtWidgets.QHBoxLayout()
        control_layout.setSpacing(10)
        cine_control_layout = QtWidgets.QHBoxLayout()
        backward_button = QtWidgets.QPushButton()
        self.backwardIcon = QtGui.QIcon()
        self.backwardIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--backward.png"),
                                    QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        backward_button.setIcon(self.backwardIcon)
        backward_button.clicked.connect(self.backward_waveform)
        cine_control_layout.addWidget(backward_button)

        play_button = QtWidgets.QPushButton()
        self.playIcon = QtGui.QIcon()
        self.playIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--play.png"),
                                QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        play_button.setIcon(self.playIcon)
        play_button.clicked.connect(self.play_waveform)
        cine_control_layout.addWidget(play_button)

        forward_button = QtWidgets.QPushButton()
        self.forwardIcon = QtGui.QIcon()
        self.forwardIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--forward.png"),
                                   QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        forward_button.setIcon(self.forwardIcon)
        forward_button.clicked.connect(self.forward_waveform)
        cine_control_layout.addWidget(forward_button)

        pause_button = QtWidgets.QPushButton()
        self.pauseIcon = QtGui.QIcon()
        self.pauseIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--pause.png"),
                                 QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        pause_button.setIcon(self.pauseIcon)
        pause_button.clicked.connect(self.pause_waveform)
        cine_control_layout.addWidget(pause_button)

        control_layout.addLayout(cine_control_layout)

        upload_button = QtWidgets.QPushButton('Upload CSV')
        upload_button.setMinimumHeight(30)
        self.uploadIcon = QtGui.QIcon()
        self.uploadIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--upload.png"),
                                  QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        upload_button.setIcon(self.uploadIcon)
        upload_button.clicked.connect(self.load_csv)
        control_layout.addWidget(upload_button)

        line_color_button = QtWidgets.QPushButton('Fill Color')
        line_color_button.setMinimumHeight(30)
        line_color_button.clicked.connect(self.choose_line_color)
        control_layout.addWidget(line_color_button)
        return control_layout

    def load_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            csv_data = pd.read_csv(file_name)
            if csv_data.shape[1] != 1:
                raise ValueError("CSV file must contain exactly 1 column.")
            self.waveform_data = csv_data.iloc[:, 0].to_numpy()
            self.row_idx = 1
            self.radar_plot.update_plot(self.waveform_data[:self.row_idx])

    def choose_line_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.radar_plot.update_line_color(color.name())

    def play_waveform(self):
        self.is_playing = True
        self.timer.start(self.timer_interval)

    def pause_waveform(self):
        self.is_playing = False
        self.timer.stop()

    def update_waveform(self):
        if hasattr(self, 'waveform_data') and len(self.waveform_data) > 0:
            end_idx = self.row_idx + self.data_chunk_size
            if end_idx < len(self.waveform_data):
                self.row_idx = end_idx
                self.radar_plot.update_plot(self.waveform_data[:self.row_idx])
            else:
                self.pause_waveform()

    def backward_waveform(self):
        if hasattr(self, 'waveform_data'):
            self.row_idx = max(0, self.row_idx - self.data_chunk_size)
            self.radar_plot.update_plot(self.waveform_data[:self.row_idx])

    def forward_waveform(self):
        if hasattr(self, 'waveform_data'):
            self.row_idx = min(len(self.waveform_data), self.row_idx + self.data_chunk_size)
            self.radar_plot.update_plot(self.waveform_data[:self.row_idx])

    def back_to_first_page(self):
        self.parent.show_first_page()


if __name__ == '__main__':
    app = QApplication([])
    main_window = QMainWindow()
    non_rec_page = NonRecPage(main_window)
    main_window.setCentralWidget(non_rec_page)
    main_window.show()
    app.exec()
