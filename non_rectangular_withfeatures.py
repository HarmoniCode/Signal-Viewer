import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QSlider, QHBoxLayout, \
    QFileDialog, QLabel, QColorDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import QTimer, Qt


class RadarPlotWidget(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi, subplot_kw=dict(polar=True))
        super(RadarPlotWidget, self).__init__(fig)
        self.ax.set_ylim(0, 5)  # increasing this will add more layers to the polar plot
        self.categories = []  # Initialize empty categories
        self.angles = []  # Initialize empty angles
        self.fill_color = '#b2d1f0'  # Default fill color
        self.line_color = '#287fd5'  # Default line color

    def update_fill_color(self, fill_color):
        self.fill_color = fill_color

    def update_line_color(self, line_color):
        self.line_color = line_color

    def update_plot(self, data, categories):
        self.ax.clear()
        data = np.concatenate((data, [data[0]]))  # Creating a list that starts and ends with the same value
        # the value of the angle between each category in the plot is from 0 to 360 divided by their number and
        # the endpoint was set to false to prevent the existence of a category 2 times as 0 and 2pi are the same angle
        # .tolist returns the values in a list
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]  # We do this so our array starts and ends with the same value

        # Plotting the data with fill and line
        self.ax.fill(angles, data, color=self.fill_color, alpha=0.5)
        self.ax.plot(angles, data, color=self.line_color, linewidth=1)
        self.ax.set_xticks(angles[:-1])
        self.ax.set_xticklabels(categories)

        for i, (angle, value) in enumerate(zip(angles, data)):
            self.ax.text(angle, value + 5, f'{value:.2f}', horizontalalignment='center', size=10, color='black',
                         backgroundcolor=self.fill_color)

        self.draw()


class RadarPlotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.fill_color = '#b2d1f0'  # Default fill color
        self.line_color = '#287fd5'  # Default line color
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.transition_plot)

    def initUI(self):
        self.setWindowTitle('Radar Plot Viewer')

        self.radar_plot = RadarPlotWidget()

        # Upload CSV button
        self.upload_button = QPushButton('Upload')
        self.upload_button.clicked.connect(self.load_csv)

        # Color chooser buttons
        self.fill_color_button = QPushButton('Choose Fill Color')
        self.fill_color_button.clicked.connect(self.choose_fill_color)
        self.fill_color_button.setEnabled(False)

        self.line_color_button = QPushButton('Choose Line Color')
        self.line_color_button.clicked.connect(self.choose_line_color)
        self.line_color_button.setEnabled(False)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        main_layout.addWidget(self.upload_button)
        main_layout.addWidget(self.fill_color_button)
        main_layout.addWidget(self.line_color_button)
        main_layout.addWidget(self.radar_plot)

        control_layout = QHBoxLayout()

        self.backward_button = QPushButton('Backward')
        self.backward_button.clicked.connect(self.backward_plot)
        self.backward_button.setEnabled(False)
        control_layout.addWidget(self.backward_button)

        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.play_plot)
        self.play_button.setEnabled(False)
        control_layout.addWidget(self.play_button)

        self.forward_button = QPushButton('Forward')
        self.forward_button.clicked.connect(self.forward_plot)
        self.forward_button.setEnabled(False)
        control_layout.addWidget(self.forward_button)

        self.pause_button = QPushButton('Pause')
        self.pause_button.clicked.connect(self.pause_plot)
        self.pause_button.setEnabled(False)
        control_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_plot)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        # Current row label
        self.current_row_label = QLabel("Current Row: N/A")
        control_layout.addWidget(self.current_row_label)

        speed_layout = QHBoxLayout()

        minspeed_label = QLabel('4 FPS')
        maxspeed_label = QLabel('80 FPS')

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(10)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(150)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(20)
        self.speed_slider.setEnabled(False)
        self.speed_slider.valueChanged.connect(self.change_speed)

        speed_layout.addWidget(minspeed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(maxspeed_label)

        control_layout.addLayout(speed_layout)

        # Add control layout to the main layout
        main_layout.addLayout(control_layout)
        self.setCentralWidget(main_widget)

    def choose_fill_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.fill_color = color.name()

        self.radar_plot.update_fill_color(self.fill_color)

    def choose_line_color(self):
        line_color = QColorDialog.getColor()
        if line_color.isValid():
            self.line_color = line_color.name()

        self.radar_plot.update_line_color(self.line_color)

    def load_csv(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)",
                                                   options=options)
        if file_name:
            self.csv_data = pd.read_csv(file_name)

            # Ensure that the CSV file has more than 2 columns
            if self.csv_data.shape[1] < 3:
                raise ValueError("CSV file must contain at least 3 columns.")

            self.play_button.setEnabled(True)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.speed_slider.setEnabled(True)
            self.backward_button.setEnabled(True)
            self.forward_button.setEnabled(True)
            self.line_color_button.setEnabled(True)
            self.fill_color_button.setEnabled(True)

            # Initialize plot settings
            self.row_idx = 0
            self.interpolation_steps = 30
            self.current_step = 0
            self.current_data = np.array(self.csv_data.iloc[self.row_idx])
            self.next_data = np.array(self.csv_data.iloc[(self.row_idx + 1) % len(self.csv_data)])
            self.is_playing = True  # Default is: not playing
            self.timer_interval = 50  # Default interval in ms
            self.timer.start(self.timer_interval)
            categories = self.csv_data.columns.tolist()  # Get column names as categories
            self.radar_plot.update_plot(self.current_data, categories)

            # Call this function to update the row label according to the current data
            self.update_current_row_label()

    def update_current_row_label(self):
        self.current_row_label.setText(f"Current Row: {self.row_idx + 1}")

    def play_plot(self):
        self.is_playing = True
        self.timer.start(self.timer_interval)

    def backward_plot(self):
        self.row_idx = max(0, self.row_idx - 1)
        self.current_data = np.array(self.csv_data.iloc[self.row_idx])
        categories = self.csv_data.columns.tolist()
        self.radar_plot.update_plot(self.current_data, categories)
        self.update_current_row_label()

    def forward_plot(self):
        self.row_idx = (self.row_idx + 1) % len(self.csv_data)
        self.current_data = np.array(self.csv_data.iloc[self.row_idx])
        categories = self.csv_data.columns.tolist()
        self.radar_plot.update_plot(self.current_data, categories)
        self.update_current_row_label()

    def pause_plot(self):
        self.is_playing = False
        self.timer.stop()

    def stop_plot(self):
        self.is_playing = False
        self.timer.stop()
        self.row_idx = 0
        self.current_step = 0
        self.current_data = np.array(self.csv_data.iloc[self.row_idx])
        categories = self.csv_data.columns.tolist()
        self.radar_plot.update_plot(self.current_data, categories)
        self.update_current_row_label()

    def change_speed(self):
        speed_value = self.speed_slider.value()  # Get speed value from the slider
        self.timer_interval = 200 - speed_value  # Since the slider value is inversely proportional with the time interval
        if self.is_playing:
            self.timer.start(self.timer_interval)  # Update the timer if playing

    def interpolate_data(self):
        factor = self.current_step / self.interpolation_steps
        interpolated_data = (1 - factor) * self.current_data + factor * self.next_data
        return interpolated_data

    def transition_plot(self):
        if self.current_step < self.interpolation_steps:
            interpolated_data = self.interpolate_data()
            categories = self.csv_data.columns.tolist()
            self.radar_plot.update_plot(interpolated_data, categories)
            self.current_step += 1
        else:
            self.row_idx = (self.row_idx + 1) % len(self.csv_data)
            self.current_data = np.array(self.csv_data.iloc[self.row_idx])
            self.next_data = np.array(self.csv_data.iloc[(self.row_idx + 1) % len(self.csv_data)])
            self.current_step = 0
            self.update_current_row_label()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RadarPlotApp()
    window.show()
    sys.exit(app.exec_())
