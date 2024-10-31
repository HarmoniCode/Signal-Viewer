import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QSlider, QHBoxLayout,QFileDialog, QLabel, QColorDialog,QFrame
from PyQt6 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import QTimer, Qt


class RadarPlotWidget(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi, subplot_kw=dict(polar=True))
        super(RadarPlotWidget, self).__init__(fig)
        self.ax.set_ylim(0, 5)
        self.fill_color = '#b2d1f0'  
        self.line_color = '#287fd5'  

        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Shape.Box)  
        self.frame.setFrameShadow(QFrame.Shadow.Raised)  
        self.frame.setLineWidth(50)  
        self.frame.setStyleSheet("border-color: black;")  
        self.frame.setLayout(QtWidgets.QVBoxLayout())
        self.frame.layout().addWidget(self)

    def update_fill_color(self, fill_color):
        self.fill_color = fill_color

    def update_line_color(self, line_color):
        self.line_color = line_color

    def update_plot(self, data, categories):
        self.ax.clear()
        data = np.concatenate((data, [data[0]])) 

        self.angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        self.angles += self.angles[:1]  

        self.ax.fill(self.angles, data, color=self.fill_color, alpha=0.5)
        self.ax.plot(self.angles, data, color=self.line_color, linewidth=1)

        self.ax.set_xticks(self.angles[:-1])
        self.ax.set_xticklabels(categories)
        for i, (angle, value) in enumerate(zip(self.angles, data)):
            self.ax.text(angle, value + 5, f'{value:.2f}', horizontalalignment='center', size=10, color='black',
                         backgroundcolor=self.fill_color)

        self.draw()



