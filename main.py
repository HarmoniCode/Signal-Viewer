from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
import sys
import csv

class SignalViewer(QtWidgets.QMainWindow):
  def __init__(self):
    super().__init__()

    self.setWindowTitle("Signal Viewer")
    self.setGeometry(100, 100, 1000, 600)

    self.central_widget = QtWidgets.QWidget()
    self.setCentralWidget(self.central_widget)
    self.layout = QtWidgets.QHBoxLayout(self.central_widget)
    
    self.graph = pg.PlotWidget()
    self.layout.addWidget(self.graph)
    
    self.signalFrame = QtWidgets.QFrame(self)
    self.signalFrame.setFixedWidth(250)  
    self.layout.addWidget(self.signalFrame)
    
    self.signalLayout = QtWidgets.QVBoxLayout(self.signalFrame)
    
    self.signals = []  
    self.signalsLines = []  
    self.currentPositions = []  
    self.signalColors = []  
    self.signalSpeeds = []  
    
    self.isPaused = False
  
    self.signalListWidget = QtWidgets.QListWidget()
    self.signalListWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
    self.signalLayout.addWidget(self.signalListWidget)

    self.loadSignalButton = QtWidgets.QPushButton("Load Signal from CSV")
    self.loadSignalButton.clicked.connect(self.load_signal)
    self.signalLayout.addWidget(self.loadSignalButton)
    
    self.colorButton = QtWidgets.QPushButton("Select Color for Signal")
    self.colorButton.clicked.connect(self.select_color)
    self.signalLayout.addWidget(self.colorButton)
    
    self.speedSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    self.speedSlider.setMinimum(1)  
    self.speedSlider.setMaximum(100)  
    self.speedSlider.setValue(10)  
    self.speedSlider.valueChanged.connect(self.change_speed)
    self.signalLayout.addWidget(self.speedSlider)
    
    self.playPauseButton = QtWidgets.QPushButton("Pause")
    self.playPauseButton.clicked.connect(self.play_pause)
    self.signalLayout.addWidget(self.playPauseButton)
  
    self.clearButton = QtWidgets.QPushButton("Clear Graph")
    self.clearButton.clicked.connect(self.clear_selected_graph)
    self.signalLayout.addWidget(self.clearButton)

    self.deleteButton = QtWidgets.QPushButton("Delete Selected Signal")
    self.deleteButton.clicked.connect(self.delete_selected_signal)
    self.signalLayout.addWidget(self.deleteButton)
    
    self.timer = QtCore.QTimer()
    self.timer.setInterval(100)  
    self.timer.timeout.connect(self.update)
    self.timer.start()
    
    self.playPauseButton.setEnabled(False)

    
    self.signalListWidget.itemChanged.connect(self.update_play_button_state)
    
    self.selectedColor = (255, 0, 0)  
    self.defaultSpeed = 10  

  def load_signal(self):
      
    filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Signal File", "", "CSV Files (*.csv)")
    if filePath:
        time, amplitude = [], []
        with open(filePath, 'r') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                if len(row) == 2:
                    time.append(float(row[0]))
                    amplitude.append(float(row[1]))
        
        time = np.array(time)
        amplitude = np.array(amplitude)

        
        self.signals.append((time, amplitude))
        
        signalName = filePath.split('/')[-1]  
        
        item = QtWidgets.QListWidgetItem(signalName)
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsSelectable)
        item.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.signalListWidget.addItem(item)

        
        self.currentPositions.append(0)  
        self.signalColors.append(self.selectedColor)  
        self.signalSpeeds.append(self.defaultSpeed)  

        self.update_play_button_state()

        self.graph.setXRange(min(time), max(time))

  def select_color(self):
    color = QtWidgets.QColorDialog.getColor()
    if color.isValid():
        
        self.selectedColor = (color.red(), color.green(), color.blue())
      
        for item in self.signalListWidget.selectedItems():
          index = self.signalListWidget.row(item)
          self.signalColors[index] = self.selectedColor  
          
          if index < len(self.signalsLines):  
              self.signalsLines[index].setPen(pg.mkPen(color=self.selectedColor, width=2))  

  def update_play_button_state(self):
    has_selected = any(item.checkState() == QtCore.Qt.CheckState.Checked for item in self.signalListWidget.findItems("*", QtCore.Qt.MatchFlag.MatchWildcard))
    self.playPauseButton.setEnabled(has_selected)

  def update(self):
    if self.isPaused:
        return  
    while len(self.signalsLines) < len(self.signals):
        self.signalsLines.append(None)  

    for index in range(self.signalListWidget.count()):
      item = self.signalListWidget.item(index)
      if item.checkState() == QtCore.Qt.CheckState.Checked:
        time, amplitude = self.signals[index]  
        current_pos = self.currentPositions[index]  

        if current_pos >= len(time):
            continue  

        new_pos = min(current_pos + self.signalSpeeds[index], len(time))

        if self.signalsLines[index] is None:
            
            pen = pg.mkPen(color=self.signalColors[index], width=2)
            self.signalsLines[index] = self.graph.plot(time[:new_pos], amplitude[:new_pos], pen=pen)
        else:
            
            self.signalsLines[index].setData(time[:new_pos], amplitude[:new_pos])
        
        self.currentPositions[index] = new_pos

  def play_pause(self):
    if self.isPaused:
        self.playPauseButton.setText("Pause")
    else:
        self.playPauseButton.setText("Play")
    self.isPaused = not self.isPaused

  def change_speed(self):
    for item in self.signalListWidget.selectedItems():
        index = self.signalListWidget.row(item)
        self.signalSpeeds[index] = self.speedSlider.value() 

  def clear_selected_graph(self):
    selected_items = self.signalListWidget.selectedItems()
    for item in selected_items:
        index = self.signalListWidget.row(item)

        if index < len(self.signalsLines) and self.signalsLines[index] is not None:
            self.graph.removeItem(self.signalsLines[index])  
            self.signalsLines[index] = None  
            self.currentPositions[index] = 0

  def delete_selected_signal(self):
    selected_items = self.signalListWidget.selectedItems()
    for item in selected_items:
      index = self.signalListWidget.row(item)
      
      self.signalListWidget.takeItem(index)

      del self.signals[index]
      del self.currentPositions[index]
      del self.signalColors[index]
      del self.signalSpeeds[index]
      
      if index < len(self.signalsLines):
          self.graph.removeItem(self.signalsLines[index])  
          del self.signalsLines[index]


def main():
  app = QtWidgets.QApplication(sys.argv)
  viewer = SignalViewer()
  viewer.show()
  sys.exit(app.exec())

if __name__ == "__main__":
  main()


