from PyQt6 import QtWidgets, QtCore,QtGui
import pyqtgraph as pg
import numpy as np
import csv
import time
import yfinance as yf
from pyqtgraph import mkPen
from ReportDialog import ReportDialog


class GraphWidget(QtWidgets.QWidget):
  def __init__(self,parent=None):
    super().__init__(parent)
    
    self.layout = QtWidgets.QHBoxLayout(self)
    self.layout.setContentsMargins(0, 0, 0, 0)
    self.layout.setSpacing(20)

    self.isPaused = False
    self.isConnected = False
    self.is_hidden = False

    self.graph = pg.PlotWidget()
    self.graph.showGrid(x=True, y=True)
    self.graphLayout = QtWidgets.QVBoxLayout()
    self.graphLayout.setSpacing(0)
    self.graphLayout.addWidget(self.graph)
    self.layout.addLayout(self.graphLayout)

    self.legend = pg.LegendItem(offset=(70, 20))
    self.legend.setParentItem(self.graph.graphicsItem())

    self.signalFrame = QtWidgets.QFrame(self)
    self.signalFrame.setFixedWidth(250)
    self.layout.addWidget(self.signalFrame)

    self.roi = pg.LinearRegionItem()
    self.roi.setZValue(10)
    self.roi.setRegion([0, 0.4])
    self.roi.hide()

    self.graph.addItem(self.roi)

    self.signalLayout = QtWidgets.QVBoxLayout(self.signalFrame)
    self.signalLayout.setContentsMargins(0, 0, 0, 0) 

    self.signals = []
    self.signalsLines = []
    self.currentPositions = []
    self.signalColors = []
    self.signalSpeeds = []


    self.controlLayout3 = QtWidgets.QHBoxLayout()
    loadIcon = QtGui.QIcon()
    loadIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--upload.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.loadSignalButton = QtWidgets.QPushButton()
    self.loadSignalButton.setFixedWidth(50)
    self.loadSignalButton.setIcon(loadIcon)
    self.loadSignalButton.clicked.connect(self.load_signal)
    self.controlLayout3.addWidget(self.loadSignalButton)

    self.connectIcon = QtGui.QIcon()
    self.connectIcon.addPixmap(QtGui.QPixmap("./control/pics/material-symbols--wifi.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    
    self.disconnectIcon = QtGui.QIcon()
    self.disconnectIcon.addPixmap(QtGui.QPixmap("./control/pics/clarity--disconnected-solid.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
   
    self.controlLayout3.addSpacerItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))

    reportIcon = QtGui.QIcon()
    reportIcon.addPixmap(QtGui.QPixmap("./control/pics/mdi--file.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.reportButton = QtWidgets.QPushButton()
    self.reportButton.setFixedWidth(50)
    self.reportButton.setIcon(reportIcon)
    self.reportButton.clicked.connect(self.open_report_dialog)
    self.controlLayout3.addWidget(self.reportButton)

    self.signalLayout.addLayout(self.controlLayout3)

    self.signalListWidget = QtWidgets.QListWidget()
    
    self.signalListWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
    self.signalListWidget.itemChanged.connect(self.update_play_button_state)
    self.signalLayout.addWidget(self.signalListWidget)

    self.controlLayout1 = QtWidgets.QHBoxLayout()
    self.controlLayout1.setContentsMargins(0, 0, 0, 0)

    self.speedPanal = QtWidgets.QHBoxLayout()
    self.speedLabel = QtWidgets.QLabel("Speed:")
    self.speedPanal.addWidget(self.speedLabel)

    self.speedSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    self.speedSlider.setMinimum(1)
    self.speedSlider.setMaximum(100)
    self.speedSlider.setValue(10)
    self.speedSlider.valueChanged.connect(self.change_speed)
    self.speedPanal.addWidget(self.speedSlider)
    self.signalLayout.addLayout(self.speedPanal)

   
    self.controlLayout1 = QtWidgets.QHBoxLayout()
    self.controlLayout1.setContentsMargins(0, 0, 0, 0)

    self.cineModeLayout= QtWidgets.QHBoxLayout()
    self.cineModeLayout.setSpacing(5)
    self.cineModeLayout.setContentsMargins(0, 10, 0, 0)
    self.cineModeLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    self.graphLayout.addLayout(self.cineModeLayout)

    self.pauseIcon = QtGui.QIcon()
    self.pauseIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--pause.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.playIcon = QtGui.QIcon()
    self.playIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--play.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.playPauseButton = QtWidgets.QPushButton()
    self.playPauseButton.setFixedWidth(50)
    self.playPauseButton.setIcon(self.pauseIcon)
    self.playPauseButton.clicked.connect(self.play_pause)

    self.replayIcon = QtGui.QIcon()
    self.replayIcon.addPixmap(QtGui.QPixmap("./control/pics/mdi--replay.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.replayButton = QtWidgets.QPushButton()
    self.replayButton.setFixedWidth(50)
    self.replayButton.setIcon(self.replayIcon)
    self.replayButton.clicked.connect(self.rewind)
    self.cineModeLayout.addWidget(self.replayButton)
    

    clearIcon = QtGui.QIcon()
    clearIcon.addPixmap(QtGui.QPixmap("./control/pics/ic--baseline-clear (1).png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.clearButton = QtWidgets.QPushButton()
    self.clearButton.setIcon(clearIcon)
    self.clearButton.clicked.connect(self.clear_selected_graph)
    self.controlLayout1.addWidget(self.clearButton)

    deleteIcon = QtGui.QIcon()
    deleteIcon.addPixmap(QtGui.QPixmap("./control/pics/ic--baseline-delete.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.deleteButton = QtWidgets.QPushButton()
    self.deleteButton.setIcon(deleteIcon)
    self.deleteButton.clicked.connect(self.delete_selected_signal)
    self.controlLayout1.addWidget(self.deleteButton)

    self.transferButton = QtWidgets.QPushButton()
    trnasferIcon = QtGui.QIcon()
    trnasferIcon.addPixmap(QtGui.QPixmap("./control/pics/gg--arrows-exchange-alt-v.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.transferButton.setIcon(trnasferIcon)
    self.transferButton.clicked.connect(self.transfer_signal)
    self.controlLayout1.addWidget(self.transferButton)

    self.signalLayout.addLayout(self.controlLayout1)

    self.controlLayout2 = QtWidgets.QHBoxLayout()
    self.controlLayout2.setContentsMargins(0, 0, 0, 0) 

    zoomINIcon = QtGui.QIcon()
    zoomINIcon.addPixmap(QtGui.QPixmap("./control/pics/raphael--zoomin.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.zoomInButton = QtWidgets.QPushButton()
    self.zoomInButton.setIcon(zoomINIcon)
    self.zoomInButton.clicked.connect(self.zoom_in)
    self.controlLayout2.addWidget(self.zoomInButton)

    zooOutIcon = QtGui.QIcon()
    zooOutIcon.addPixmap(QtGui.QPixmap("./control/pics/raphael--zoomout.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.zoomOutButton = QtWidgets.QPushButton()
    self.zoomOutButton.setIcon(zooOutIcon)
    self.zoomOutButton.clicked.connect(self.zoom_out)
    self.controlLayout2.addWidget(self.zoomOutButton)





    colorIcon = QtGui.QIcon()
    colorIcon.addPixmap(QtGui.QPixmap("./control/pics/bxs--color-fill.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.colorButton = QtWidgets.QPushButton()
    self.colorButton.setIcon(colorIcon)
    self.colorButton.clicked.connect(self.select_color)
    self.controlLayout2.addWidget(self.colorButton)

    self.signalLayout.addLayout(self.controlLayout2)
    self.showIcon = QtGui.QIcon()
    self.showIcon.addPixmap(QtGui.QPixmap("./control/pics/streamline--visible.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    
    self.hideIcon = QtGui.QIcon()
    self.hideIcon.addPixmap(QtGui.QPixmap("./control/pics/streamline--invisible-1-solid.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)

    self.showHideButton = QtWidgets.QPushButton()
    self.showHideButton.setFixedWidth(50)
    self.showHideButton.setIcon(self.showIcon)
    self.showHideButton.clicked.connect(self.show_hide)

    
    # self.cineModePanel = QtWidgets.QHBoxLayout()
    # self.cineModePanel.setContentsMargins(0, 0, 0, 0)  
    # self.backWard = QtWidgets.QLabel("Backward")
    # self.cineModePanel.addWidget(self.backWard)
    # self.mainSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    # self.mainSlider.setMinimum(0)
    # self.mainSlider.setMaximum(100)
    # self.mainSlider.setValue(0)
    # self.mainSlider.valueChanged.connect(self.slider_moved)
    # self.cineModePanel.addWidget(self.mainSlider)
    # self.forwardLabel = QtWidgets.QLabel("Forward")
    # self.cineModePanel.addWidget(self.forwardLabel)
    # self.signalLayout.addLayout(self.cineModePanel)

    self.cineModePanel = QtWidgets.QHBoxLayout()
    self.cineModePanel.setContentsMargins(0, 0, 0, 0)  

    self.backWardButton = QtWidgets.QPushButton()
    self.backWardButton.setFixedWidth(50)
    self.backWardButton.setIcon(QtGui.QIcon("./control/pics/fontisto--backward.png"))
    self.backWardButton.clicked.connect(self.backward_clicked)
    self.cineModeLayout.addWidget(self.backWardButton)

    self.cineModeLayout.addWidget(self.playPauseButton)


    self.forwardButton = QtWidgets.QPushButton()
    self.forwardButton.setFixedWidth(50)
    self.forwardButton.setIcon(QtGui.QIcon("./control/pics/fontisto--forward.png"))
    self.forwardButton.clicked.connect(self.forward_clicked)
    self.cineModeLayout.addWidget(self.forwardButton)

    self.cineModeLayout.addWidget(self.showHideButton)

    self.signalLayout.addLayout(self.cineModePanel)
    self.default_step = 0.05



    self.playPauseButton.setEnabled(False)

    self.selectedColor = (255, 0, 0)
    self.defaultSpeed = 10

    self.roi.sigRegionChanged.connect(self.on_roi_changed)

    self.report_dialog = None

    self.timer = QtCore.QTimer()
    self.timer.setInterval(100)
    self.timer.timeout.connect(self.update)
    self.timer.start()

    self.signalListWidget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
    self.signalListWidget.customContextMenuRequested.connect(self.show_context_menu)

    self.currentSignalIndex = None 

  def auto_scroll_x_axis(self, x):
    """Auto-scroll the x-axis as the signal progresses."""
    # Get the current visible range
    x_range = self.graph.viewRange()[0]
    defult_step = 0.01
    
    # Check if the signal is moving beyond the current visible range
    if x > x_range[1]:
        # Shift the x-axis to follow the signal without compressing the view
        self.graph.setXRange(x_range[0] + defult_step, x_range[1] + defult_step, padding=0)


  def load_signal(self):
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, None, None, "CSV Files (*.csv)")
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
            signalName = (filePath.split('/')[-1]).split('.')[0]
            item = QtWidgets.QListWidgetItem(signalName)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsSelectable)
            item.setCheckState(QtCore.Qt.CheckState.Checked)
            self.signalListWidget.addItem(item)

            self.currentPositions.append(0)  
            self.signalColors.append(self.selectedColor)  
            self.signalSpeeds.append(self.defaultSpeed)  

            self.update_play_button_state()

            pen = pg.mkPen(color=self.selectedColor, width=2)
            line_item = self.graph.plot(time, amplitude, pen=pen)
            self.signalsLines.append(line_item)
            self.legend.addItem(line_item, signalName)

            x_padding = (max(time) - min(time)) * 0.05  
            y_padding = (max(amplitude) - min(amplitude)) * 0.05  

            self.graph.setXRange(min(time) - x_padding, max(time) + x_padding, padding=0)
            self.graph.setYRange(min(amplitude) - y_padding, max(amplitude) + y_padding, padding=0)

            self.graph.setLimits(xMin=min(time) - x_padding, xMax=max(time) + x_padding, 
                                yMin=min(amplitude) - y_padding, yMax=max(amplitude) + y_padding)
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
                if current_pos < len(time):
                    new_pos = min(current_pos + self.signalSpeeds[index], len(time))
                    if self.signalsLines[index] is None:
                        pen = pg.mkPen(color=self.signalColors[index], width=2)
                        self.signalsLines[index] = self.graph.plot(time[:new_pos], amplitude[:new_pos], pen=pen)
                    else:
                        self.signalsLines[index].setData(time[:new_pos], amplitude[:new_pos])

                    self.currentPositions[index] = new_pos
                    self.auto_scroll_x_axis(time[int(new_pos)])
                    # if index == self.currentSignalIndex:
                    #     self.mainSlider.setValue(int(new_pos / len(time) * 100))

  def on_roi_changed(self):
    self.selected_range = self.roi.getRegion()

  def show_context_menu(self, pos):
        item = self.signalListWidget.itemAt(pos)
        if item is not None:
            index = self.signalListWidget.row(item)
            statistics_message=self.show_statistics_tooltip(index)
            statistics_message=(
                f"<b style='color: blue;'>Signal:</b> {statistics_message['Signal']}<br>"
                f"<b style='color: blue;'>Max Value:</b> {statistics_message['Max_Value']}<br>"
                f"<b style='color: blue;'>Min Value:</b> {statistics_message['Min_Value']}<br>"
                f"<b style='color: blue;'>Time Length:</b> {statistics_message['Time_Length']:.2f}<br>"
                f"<b style='color: blue;'>Speed:</b> {statistics_message['Speed']}<br>"
                f"<b style='color: blue;'>Color:</b> {statistics_message['Color']}<br>"
                f"<b style='color: blue;'>STD:</b> {statistics_message['Std_Deviation']}"
            )
            QtWidgets.QToolTip.showText(self.signalListWidget.mapToGlobal(pos), statistics_message)

  def show_statistics_tooltip(self, index):
    if index < len(self.signals):
        time, amplitude = self.signals[index]
        max_value =round(np.max(amplitude),4)
        min_value = round(np.min(amplitude),4)
        time_length = round(time[-1] - time[0],4  )
        std_deviation = round(np.std(amplitude), 4) 
        speed = self.signalSpeeds[index]
        color = self.signalColors[index]
        statistics_message = {
        "Signal": self.signalListWidget.item(index).text(),
        "Max_Value": max_value,
        "Min_Value": min_value,
        "Time_Length": time_length,
        "Speed": speed,
        "Color": color,
        "Std_Deviation": std_deviation
        }
        return statistics_message

  def open_report_dialog(self):
    if self.report_dialog is None:
        self.report_dialog = ReportDialog(self.graph)
        parent_pos = self.mapToGlobal(self.pos())
        self.report_dialog.move(parent_pos.x() + self.width(), parent_pos.y())
    self.report_dialog.show()

#   def slider_moved(self, value):
#       for index in range(self.signalListWidget.count()):
#           item = self.signalListWidget.item(index)
#           if item.isSelected(): 
#               self.currentSignalIndex = index 
#               self.currentPositions[index] = int(value / 100 * len(self.signals[index][0]))
#               time, amplitude = self.signals[index]
#               current_pos = self.currentPositions[index]

#               if self.signalsLines[index] is None:
#                   pen = pg.mkPen(color=self.signalColors[index], width=2)
#                   self.signalsLines[index] = self.graph.plot(time[:current_pos], amplitude[:current_pos], pen=pen)
#               else:
#                   self.signalsLines[index].setData(time[:current_pos], amplitude[:current_pos])
#               self.signalsLines[index].setPen(pg.mkPen(color=self.signalColors[index], width=2))
#               break 

  def backward_clicked(self):
    self.move_signal(-self.default_step)

  def forward_clicked(self):
    self.move_signal(self.default_step)

  def move_signal(self, step_factor):
    for index in range(self.signalListWidget.count()):
        item = self.signalListWidget.item(index)
        if item.isSelected(): 
            self.currentSignalIndex = index 

            # Calculate new position based on step
            self.currentPositions[index] = max(0, min(len(self.signals[index][0]), self.currentPositions[index] + int(step_factor * len(self.signals[index][0]))))
            
            time, amplitude = self.signals[index]
            current_pos = self.currentPositions[index]

            if self.signalsLines[index] is None:
                pen = pg.mkPen(color=self.signalColors[index], width=2)
                self.signalsLines[index] = self.graph.plot(time[:current_pos], amplitude[:current_pos], pen=pen)
            else:
                self.signalsLines[index].setData(time[:current_pos], amplitude[:current_pos])
            
            self.signalsLines[index].setPen(pg.mkPen(color=self.signalColors[index], width=2))
            break

  def select_color(self):
      color = QtWidgets.QColorDialog.getColor()
      if color.isValid():
          self.selectedColor = (color.red(), color.green(), color.blue())
          for item in self.signalListWidget.selectedItems():
              index = self.signalListWidget.row(item)
              self.signalColors[index] = self.selectedColor  
              if index < len(self.signalsLines):  
                  self.signalsLines[index].setPen(pg.mkPen(color=self.selectedColor, width=2))

  def select_color(self):
    color = QtWidgets.QColorDialog.getColor()
    self.selectedColor = (color.red(), color.green(), color.blue())
    for item in self.signalListWidget.selectedItems():
        index = self.signalListWidget.row(item)
        self.signalColors[index] = self.selectedColor  
        if index < len(self.signalsLines):  
            self.signalsLines[index].setPen(pg.mkPen(color=self.selectedColor, width=2))  

  def update_play_button_state(self):
    has_selected = any(item.checkState() == QtCore.Qt.CheckState.Checked for item in self.signalListWidget.findItems("*", QtCore.Qt.MatchFlag.MatchWildcard))
    self.playPauseButton.setEnabled(has_selected)

  

  def play_pause(self):
    if self.isPaused:
        self.playPauseButton.setIcon(self.pauseIcon)
    else:
        self.playPauseButton.setIcon(self.playIcon)
    self.isPaused = not self.isPaused

  def show_hide(self):
    if  self.is_hidden:
        self.showHideButton.setIcon(self.showIcon)
        self.is_hidden = False
    else:
        self.showHideButton.setIcon(self.hideIcon)
        self.is_hidden = True
    self.show_hide_signal()

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
                # Remove from legend
                self.legend.removeItem(item.text())
        if not self.isPaused:
            self.play_pause()
  def rewind(self):
            self.graph.setXRange(0, 1 , padding=10)
            self.isPaused = False
            for index in range(self.signalListWidget.count()):
                item = self.signalListWidget.item(index)
                if item.checkState() == QtCore.Qt.CheckState.Checked:
                    self.currentPositions[index] = 0
                    if index < len(self.signalsLines) and self.signalsLines[index] is not None:
                        self.graph.removeItem(self.signalsLines[index])
                        self.signalsLines[index] = None
            self.update()


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
                # Remove from legend
                self.legend.removeItem(item.text())

  def zoom_in(self):
        current_x_range = self.graph.viewRange()[0]
        current_y_range = self.graph.viewRange()[1]

        new_x_range = (current_x_range[0] + (current_x_range[1] - current_x_range[0]) * 0.1,
                       current_x_range[1] - (current_x_range[1] - current_x_range[0]) * 0.1)
        new_y_range = (current_y_range[0] + (current_y_range[1] - current_y_range[0]) * 0.1,
                       current_y_range[1] - (current_y_range[1] - current_y_range[0]) * 0.1)

        self.graph.setXRange(*new_x_range, padding=0)
        self.graph.setYRange(*new_y_range, padding=0)

  def zoom_out(self):
        current_x_range = self.graph.viewRange()[0]
        current_y_range = self.graph.viewRange()[1]

        new_x_range = (current_x_range[0] - (current_x_range[1] - current_x_range[0]) * 0.1,
                       current_x_range[1] + (current_x_range[1] - current_x_range[0]) * 0.1)
        new_y_range = (current_y_range[0] - (current_y_range[1] - current_y_range[0]) * 0.1,
                       current_y_range[1] + (current_y_range[1] - current_y_range[0]) * 0.1)

        self.graph.setXRange(*new_x_range, padding=0)
        self.graph.setYRange(*new_y_range, padding=0)
  def transfer_signal(self):
    signal_viewer = self.parent().parent().parent().parent().parent().parent()
    selected_items = self.signalListWidget.selectedItems()

    if self is signal_viewer.graphBox1:
        transferFrom = signal_viewer.graphBox1
        transferTo = signal_viewer.graphBox2
    else:
        transferFrom = signal_viewer.graphBox2
        transferTo = signal_viewer.graphBox1

    for item in selected_items:
        index = transferFrom.signalListWidget.row(item)

        if index < len(transferFrom.signalsLines) and transferFrom.signalsLines[index] is not None:
            time, amplitude = transferFrom.signals[index]
            color = transferFrom.signalColors[index]
            speed = transferFrom.signalSpeeds[index]
            currentPosition = transferFrom.currentPositions[index]

            transferTo.signals.append((time, amplitude))
            transferTo.currentPositions.append(currentPosition)
            transferTo.signalColors.append(color)
            transferTo.signalSpeeds.append(speed)

            newItem = QtWidgets.QListWidgetItem(item.text())
            newItem.setFlags(newItem.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsSelectable)
            newItem.setCheckState(QtCore.Qt.CheckState.Unchecked)
            transferTo.signalListWidget.addItem(newItem)

            transferFrom.graph.removeItem(transferFrom.signalsLines[index])
            
            transferTo.legend.addItem(self.signalsLines[index],item.text())
            
            transferFrom.signalsLines[index] = None
            transferFrom.legend.removeItem(item.text())

            del transferFrom.signals[index]
            del transferFrom.signalsLines[index]
            del transferFrom.currentPositions[index]
            del transferFrom.signalColors[index]
            del transferFrom.signalSpeeds[index]
            transferFrom.signalListWidget.takeItem(index)           
  
    def show_hide_signal(self):
        selected_items = self.signalListWidget.selectedItems()
        for item in selected_items:
                index = self.signalListWidget.row(item)
                if index < len(self.signalsLines) and self.signalsLines[index] is not None:   
                    if self.signalsLines[index].isVisible():
                        self.signalsLines[index].hide()
                    else:
                        self.signalsLines[index].show()  
