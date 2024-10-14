import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QSlider, QHBoxLayout, \
    QFileDialog, QLabel, QColorDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import QTimer, Qt


class RadarPlotWidget(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100):
        # subplot_kw refers to a dictionary contains the names of the available plots where we chose polar here
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi, subplot_kw=dict(polar=True))
        super(RadarPlotWidget, self).__init__(fig)
        self.ax.set_ylim(0, 5)
        self.fill_color = '#b2d1f0'  # Default fill color
        self.line_color = '#287fd5'  # Default line color

    def update_fill_color(self, fill_color):
        self.fill_color = fill_color

    def update_line_color(self, line_color):
        self.line_color = line_color

    def update_plot(self, data, categories):
        self.ax.clear()
        data = np.concatenate((data, [data[0]]))  # Closing the radar chart
        # the value of the angle between each category in the plot is from 0 to 360 divided by their number and
        # the endpoint was set to false to prevent the existence of a category 2 times as 0 and 2pi are the same angle
        # .tolist returns the values in a list

        self.angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        self.angles += self.angles[:1]  # We concatenate so our array starts and ends with the same value

        # Plot fill and line
        self.ax.fill(self.angles, data, color=self.fill_color, alpha=0.5)
        self.ax.plot(self.angles, data, color=self.line_color, linewidth=1)

        self.ax.set_xticks(self.angles[:-1])
        self.ax.set_xticklabels(categories)
        for i, (angle, value) in enumerate(zip(self.angles, data)):
            # ax.text puts a label where the plot is with the current value
            self.ax.text(angle, value + 5, f'{value:.2f}', horizontalalignment='center', size=10, color='black',
                         backgroundcolor=self.fill_color)

        self.draw()


class RadarPlotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Dual Radar Plot Viewer')

        self.radar_plot1 = RadarPlotWidget()
        self.radar_plot2 = RadarPlotWidget()

        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(lambda: self.transition_plot(self.radar_plot1, 1))
        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(lambda: self.transition_plot(self.radar_plot2, 2))

        self.init_plot_vars(1)
        self.init_plot_vars(2)

        radar_layout = QHBoxLayout()
        radar_layout.addWidget(self.radar_plot1)
        radar_layout.addWidget(self.radar_plot2)

        controls1 = self.create_controls(self.radar_plot1, self.timer1, plot_num=1)

        controls2 = self.create_controls(self.radar_plot2, self.timer2, plot_num=2)

        main_layout = QVBoxLayout()
        main_layout.addLayout(radar_layout)
        main_layout.addLayout(controls1)
        main_layout.addLayout(controls2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def init_plot_vars(self, plot_num):
        setattr(self, f'row_idx{plot_num}', 0)
        setattr(self, f'interpolation_steps{plot_num}', 30)
        setattr(self, f'current_step{plot_num}', 0)
        setattr(self, f'is_playing{plot_num}', False)
        setattr(self, f'timer_interval{plot_num}', 50)

    def create_controls(self, radar_plot, timer, plot_num):

        control_layout = QVBoxLayout()

        upload_button = QPushButton(f'Upload CSV for Plot {plot_num}')
        upload_button.clicked.connect(lambda: self.load_csv(radar_plot, plot_num))
        control_layout.addWidget(upload_button)

        fill_color_button = QPushButton(f'Choose Fill Color for Plot {plot_num}')
        fill_color_button.clicked.connect(lambda: self.choose_fill_color(radar_plot))
        control_layout.addWidget(fill_color_button)

        line_color_button = QPushButton(f'Choose Line Color for Plot {plot_num}')
        line_color_button.clicked.connect(lambda: self.choose_line_color(radar_plot))
        control_layout.addWidget(line_color_button)

        cine_control_layout = QHBoxLayout()
        backward_button = QPushButton('Backward')
        backward_button.clicked.connect(lambda: self.backward_plot(radar_plot, plot_num))
        cine_control_layout.addWidget(backward_button)

        play_button = QPushButton('Play')
        play_button.clicked.connect(lambda: self.play_plot(timer, plot_num))
        cine_control_layout.addWidget(play_button)

        forward_button = QPushButton('Forward')
        forward_button.clicked.connect(lambda: self.forward_plot(radar_plot, plot_num))
        cine_control_layout.addWidget(forward_button)

        pause_button = QPushButton('Pause')
        pause_button.clicked.connect(lambda: self.pause_plot(timer, plot_num))
        cine_control_layout.addWidget(pause_button)

        stop_button = QPushButton('Stop')
        stop_button.clicked.connect(lambda: self.stop_plot(radar_plot, plot_num))
        cine_control_layout.addWidget(stop_button)

        control_layout.addLayout(cine_control_layout)

        speed_layout = QHBoxLayout()
        minspeed_label = QLabel('4 FPS')
        maxspeed_label = QLabel('80 FPS')
        speed_slider = QSlider(Qt.Orientation.Horizontal)
        speed_slider.setMinimum(10)
        speed_slider.setMaximum(200)
        speed_slider.setValue(150)
        speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        speed_slider.setTickInterval(20)
        speed_slider.valueChanged.connect(lambda: self.change_speed(timer, plot_num, speed_slider))
        speed_layout.addWidget(minspeed_label)
        speed_layout.addWidget(speed_slider)
        speed_layout.addWidget(maxspeed_label)
        control_layout.addLayout(speed_layout)

        return control_layout

    def choose_fill_color(self, radar_plot):
        color = QColorDialog.getColor()
        if color.isValid():
            radar_plot.update_fill_color(color.name())

    def choose_line_color(self, radar_plot):
        color = QColorDialog.getColor()
        if color.isValid():
            radar_plot.update_line_color(color.name())

    def load_csv(self, radar_plot, plot_num):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)",
                                                   options=options)
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RadarPlotApp()
    window.show()
    sys.exit(app.exec())