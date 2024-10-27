from nonRectangle import RadarPlotWidget
import pandas as pd
from PyQt6 import QtWidgets, QtCore,QtGui
from PyQt6.QtCore import Qt
import numpy as np

class NonRecPage(QtWidgets.QWidget):
    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        self.initUI()
        

    def initUI(self):
        self.setWindowTitle('Dual Radar Plot Viewer')
        self.parent.setGeometry(100, 100, 1000, 400)

        self.radar_plot1 = RadarPlotWidget()
        self.radar_plot2 = RadarPlotWidget()

        self.timer1 = QtCore.QTimer(self)
        self.timer1.timeout.connect(lambda: self.transition_plot(self.radar_plot1, 1))
        self.timer2 = QtCore.QTimer(self)
        self.timer2.timeout.connect(lambda: self.transition_plot(self.radar_plot2, 2))

        self.init_plot_vars(1)
        self.init_plot_vars(2)

        main_layout = QtWidgets.QVBoxLayout()


        horizontal_control=QtWidgets.QHBoxLayout()
        backIcon=QtGui.QIcon()
        backIcon.addPixmap(QtGui.QPixmap("./Icons/pics/bx--arrow-back.png"),QtGui.QIcon.Mode.Normal,QtGui.QIcon.State.On)
        self.back_to_first_page_button = QtWidgets.QPushButton()
        self.back_to_first_page_button.setIcon(backIcon)
        self.back_to_first_page_button.setMinimumHeight(30)
        self.back_to_first_page_button.setFixedWidth(50)
        self.back_to_first_page_button.clicked.connect(self.back_to_first_page)
        horizontal_control.addWidget(self.back_to_first_page_button)
        horizontal_control.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))

        main_layout.addLayout(horizontal_control)

        radar_layout = QtWidgets.QHBoxLayout()
        vertical_layout1 = QtWidgets.QVBoxLayout()
        
        radar_layout.addLayout(vertical_layout1)
        vertical_layout1.addWidget(self.radar_plot1)

        vertical_layout2 = QtWidgets.QVBoxLayout()
        radar_layout.addLayout(vertical_layout2)
        vertical_layout2.addWidget(self.radar_plot2)

        controls1 = self.create_controls(self.radar_plot1, self.timer1, plot_num=1)
        vertical_layout1.addLayout(controls1)
        controls2 = self.create_controls(self.radar_plot2, self.timer2, plot_num=2)
        vertical_layout2.addLayout(controls2)


        main_layout.setSpacing(20)
        main_layout.addLayout(radar_layout)
        main_layout.addLayout(controls1)
        main_layout.addSpacerItem(QtWidgets.QSpacerItem(15, 0, QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Expanding))
        main_layout.addLayout(controls2)

        

        self.setLayout(main_layout)

    def init_plot_vars(self, plot_num):
        setattr(self, f'row_idx{plot_num}', 0)
        setattr(self, f'interpolation_steps{plot_num}', 30)
        setattr(self, f'current_step{plot_num}', 0)
        setattr(self, f'is_playing{plot_num}', False)
        setattr(self, f'timer_interval{plot_num}', 50)

    def create_controls(self, radar_plot, timer, plot_num):

        control_layout = QtWidgets.QVBoxLayout()
        control_layout.setSpacing(10)

        controlBox1 = QtWidgets.QHBoxLayout()

        upload_button = QtWidgets.QPushButton(f' Upload CSV')
        upload_button.setMinimumHeight(30)
        self.uploadIcon = QtGui.QIcon()
        self.uploadIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--upload.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        upload_button.setIcon(self.uploadIcon)
        upload_button.clicked.connect(lambda: self.load_csv(radar_plot, plot_num))
        controlBox1.addWidget(upload_button)

        fill_color_button = QtWidgets.QPushButton(f' Fill Color  {plot_num}')
        fill_color_button.setMinimumHeight(30)
        fill_color_button.clicked.connect(lambda: self.choose_fill_color(radar_plot))
        controlBox1.addWidget(fill_color_button)

        line_color_button = QtWidgets.QPushButton(f' Line Color  {plot_num}')
        line_color_button.setMinimumHeight(30)
        line_color_button.clicked.connect(lambda: self.choose_line_color(radar_plot))
        controlBox1.addWidget(line_color_button)
        control_layout.addLayout(controlBox1)

        cine_control_layout = QtWidgets.QHBoxLayout()
        backward_button = QtWidgets.QPushButton()
        self.backwardIcon = QtGui.QIcon()
        self.backwardIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--backward.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        backward_button.setIcon(self.backwardIcon)
        backward_button.clicked.connect(lambda: self.backward_plot(radar_plot, plot_num))
        cine_control_layout.addWidget(backward_button)

        play_button = QtWidgets.QPushButton()
        self.playIcon = QtGui.QIcon()
        self.playIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--play.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        play_button.setIcon(self.playIcon)

        play_button.clicked.connect(lambda: self.play_plot(timer, plot_num))
        cine_control_layout.addWidget(play_button)

        forward_button = QtWidgets.QPushButton()
        self.forwardIcon = QtGui.QIcon()
        self.forwardIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--forward.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        forward_button.setIcon(self.forwardIcon)
        forward_button.clicked.connect(lambda: self.forward_plot(radar_plot, plot_num))
        cine_control_layout.addWidget(forward_button)

        pause_button = QtWidgets.QPushButton()
        self.pauseIcon = QtGui.QIcon()
        self.pauseIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fontisto--pause.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        pause_button.setIcon(self.pauseIcon)
        pause_button.clicked.connect(lambda: self.pause_plot(timer, plot_num))
        cine_control_layout.addWidget(pause_button)

        stop_button = QtWidgets.QPushButton()
        self.replayIcon = QtGui.QIcon()
        self.replayIcon.addPixmap(QtGui.QPixmap("./Icons/pics/mdi--replay.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        stop_button.setIcon(self.replayIcon)
        stop_button.clicked.connect(lambda: self.stop_plot(radar_plot, plot_num))
        cine_control_layout.addWidget(stop_button)

        control_layout.addLayout(cine_control_layout)

        speed_layout = QtWidgets.QHBoxLayout()
        minspeed_label = QtWidgets.QLabel('4 FPS')
        maxspeed_label = QtWidgets.QLabel('80 FPS')
        speed_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        speed_slider.setMinimum(10)
        speed_slider.setMaximum(200)
        speed_slider.setValue(150)
        speed_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        speed_slider.setTickInterval(20)
        speed_slider.valueChanged.connect(lambda: self.change_speed(timer, plot_num, speed_slider))
        speed_layout.addWidget(minspeed_label)
        speed_layout.addWidget(speed_slider)
        speed_layout.addWidget(maxspeed_label)
        control_layout.addLayout(speed_layout)

        return control_layout

    def choose_fill_color(self, radar_plot):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            radar_plot.update_fill_color(color.name())

    def choose_line_color(self, radar_plot):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            radar_plot.update_line_color(color.name())

    def load_csv(self, radar_plot, plot_num):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            csv_data = pd.read_csv(file_name)
            if csv_data.shape[1] < 3:
                raise ValueError("CSV file must contain at least 3 columns.")

            setattr(self, f'csv_data{plot_num}', csv_data)

            categories = csv_data.columns.tolist()
            row_idx = getattr(self, f'row_idx{plot_num}')
            current_data = np.array(csv_data.iloc[row_idx])
            radar_plot.update_plot(current_data, categories)

    def change_speed(self, timer, plot_num, slider):
        speed_value = slider.value()
        timer_interval = 200 - speed_value
        setattr(self, f'timer_interval{plot_num}', timer_interval)
        if getattr(self, f'is_playing{plot_num}'):
            timer.start(timer_interval)

    def play_plot(self, timer, plot_num):
        setattr(self, f'is_playing{plot_num}', True)
        timer.start(getattr(self, f'timer_interval{plot_num}'))

    def pause_plot(self, timer, plot_num):
        setattr(self, f'is_playing{plot_num}', False)
        timer.stop()

    def stop_plot(self, radar_plot, plot_num):
        timer = getattr(self, f'timer{plot_num}')
        timer.stop()
        self.init_plot_vars(plot_num)
        radar_plot.ax.clear()
        radar_plot.draw()

    def backward_plot(self, radar_plot, plot_num):
        row_idx = getattr(self, f'row_idx{plot_num}')
        csv_data = getattr(self, f'csv_data{plot_num}')
        if row_idx > 0:
            row_idx -= 1
        setattr(self, f'row_idx{plot_num}', row_idx)
        current_data = np.array(csv_data.iloc[row_idx])
        categories = csv_data.columns.tolist()
        radar_plot.update_plot(current_data, categories)

    def forward_plot(self, radar_plot, plot_num):
        row_idx = getattr(self, f'row_idx{plot_num}')
        csv_data = getattr(self, f'csv_data{plot_num}')
        row_idx = (row_idx + 1) % len(csv_data)
        setattr(self, f'row_idx{plot_num}', row_idx)
        current_data = np.array(csv_data.iloc[row_idx])
        categories = csv_data.columns.tolist()
        radar_plot.update_plot(current_data, categories)

    def interpolate_data(self, current_data, next_data, current_step, interpolation_steps):
        factor = current_step / interpolation_steps
        interpolated_data = (1 - factor) * current_data + factor * next_data
        return interpolated_data

    def transition_plot(self, radar_plot, plot_num):
        current_step = getattr(self, f'current_step{plot_num}')
        interpolation_steps = getattr(self, f'interpolation_steps{plot_num}')
        row_idx = getattr(self, f'row_idx{plot_num}')
        csv_data = getattr(self, f'csv_data{plot_num}')
        categories = csv_data.columns.tolist()

        current_data = np.array(csv_data.iloc[row_idx])
        next_data = np.array(csv_data.iloc[(row_idx + 1) % len(csv_data)])

        interpolated_data = self.interpolate_data(current_data, next_data, current_step, interpolation_steps)
        radar_plot.update_plot(interpolated_data, categories)

        if current_step < interpolation_steps:
            current_step += 1
            setattr(self, f'current_step{plot_num}', current_step)
        else:
            setattr(self, f'row_idx{plot_num}', (row_idx + 1) % len(csv_data))
            setattr(self, f'current_step{plot_num}', 0)


    def back_to_first_page(self):
        self.parent.show_first_page()
