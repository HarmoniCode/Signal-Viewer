from PyQt6.QtPrintSupport import QPrinter
from nonRectangle import RadarPlotWidget
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6 import QtWidgets, QtCore,QtGui
import scipy.interpolate as interp
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import sys
import csv
import time
import yfinance as yf
from pyqtgraph import mkPen


class ReportDialog(QtWidgets.QDialog):
    def __init__(self, graph, parent=None):
        super().__init__(parent)
        self.graph = graph  
        self.setWindowTitle("Create Report")
        self.setMinimumSize(500, 500)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.textEdit = QtWidgets.QTextEdit()
        default_font = QtGui.QFont()
        default_font.setPointSize(14)  
        default_font.setWeight(50)  
        default_font.setFamily("Arial")  
        self.textEdit.setFont(default_font)
        self.textEdit.setStyleSheet("QTextEdit { padding: 10px; }")  

        self.layout.addWidget(self.textEdit)
        self.exportButton = QtWidgets.QPushButton("Export")
        self.exportButton.clicked.connect(self.export_report)
        self.layout.addWidget(self.exportButton)

        self.screenshotButton = QtWidgets.QPushButton("Add Screenshot")
        self.screenshotButton.clicked.connect(self.add_screenshot_to_report)
        self.layout.addWidget(self.screenshotButton)

        self.showStatisticsButton = QtWidgets.QPushButton("Show Statistics")
        self.showStatisticsButton.clicked.connect(self.show_statistics_table)
        self.layout.addWidget(self.showStatisticsButton)
        
        
        

    def show_statistics_table(self):
        selectedIndecies = self.graph.parent().signalListWidget.selectedIndexes()
        if len(selectedIndecies) > 0:
            statistics = self.graph.parent().show_statistics_tooltip(selectedIndecies[0].row())
            print(statistics)

        if statistics:
            
            cursor = self.textEdit.textCursor()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)  
            
            keyword_format = QtGui.QTextCharFormat()
            keyword_format.setFontWeight(QtGui.QFont.Weight.Bold)
            keyword_format.setFontPointSize(11)
            keyword_format.setForeground(QtGui.QColor("blue"))

            value_format = QtGui.QTextCharFormat()
            value_format.setFontWeight(QtGui.QFont.Weight.Bold)
            value_format.setFontPointSize(11)
            value_format.setForeground(QtGui.QColor("black"))
            
            def insert_formatted_text(keyword, value):
                cursor.insertText(keyword + "  ", keyword_format)  
                cursor.insertText(str(value) + "\n", value_format)  
            
            insert_formatted_text("Max Value", statistics['Max_Value'])
            insert_formatted_text("Min Value", statistics['Min_Value'])
            insert_formatted_text("Length", statistics['Time_Length'])
            insert_formatted_text("Speed", statistics['Speed'])
            insert_formatted_text("Color", statistics['Color'])
            insert_formatted_text("STD", statistics['Std_Deviation'])

            self.textEdit.setTextCursor(cursor)



    def add_screenshot_to_report(self):
        graph_widget = self.graph
        graph_rect = graph_widget.geometry()
        screen = QtGui.QGuiApplication.primaryScreen()
        screenshot = screen.grabWindow(graph_widget.winId(), graph_rect.x(), graph_rect.y(), graph_rect.width() - 10, graph_rect.height() - 10)
        resized_screenshot = screenshot.scaled(600, 400, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        cursor = self.textEdit.textCursor()
        cursor.insertImage(resized_screenshot.toImage(), "Screenshot")  
        self.textEdit.setTextCursor(cursor)
        self.show_statistics_table()

    def export_report(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, None, None, "PDF Files (*.pdf);;All Files (*)"
        )
        if fileName:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(fileName)
            self.textEdit.document().print(printer)
            self.close()

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
    
    self.connectRealTimeSignalButton = QtWidgets.QPushButton()
    self.connectRealTimeSignalButton.setIcon(self.connectIcon)
    self.connectRealTimeSignalButton.setFixedWidth(50)
    self.connectRealTimeSignalButton.clicked.connect(self.connect_stop)
    self.controlLayout3.addWidget(self.connectRealTimeSignalButton)

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




    ## hiden button

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

    # Create Backward Button
    self.backWardButton = QtWidgets.QPushButton()
    self.backWardButton.setFixedWidth(50)
    self.backWardButton.setIcon(QtGui.QIcon("./control/pics/fontisto--backward.png"))
    self.backWardButton.clicked.connect(self.backward_clicked)
    self.cineModeLayout.addWidget(self.backWardButton)

    self.cineModeLayout.addWidget(self.playPauseButton)


    # Create Forward Button
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
                # if index == self.currentSignalIndex:
                #     self.mainSlider.setValue(int(new_pos / len(time) * 100))

  def play_pause(self):
    if self.isPaused:
        self.playPauseButton.setIcon(self.pauseIcon)
    else:
        self.playPauseButton.setIcon(self.playIcon)
    self.isPaused = not self.isPaused

  def connect_stop(self):
        if  not self.isConnected:
            self.connectRealTimeSignalButton.setIcon(self.disconnectIcon)
            self.isConnected = True
        else:
            self.connectRealTimeSignalButton.setIcon(self.connectIcon)
            self.isConnected = False
        self.connect_real_time_signal()
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
            transferFrom.signalsLines[index] = None
            transferFrom.legend.removeItem(item.text())

            del transferFrom.signals[index]
            del transferFrom.signalsLines[index]
            del transferFrom.currentPositions[index]
            del transferFrom.signalColors[index]
            del transferFrom.signalSpeeds[index]
            transferFrom.signalListWidget.takeItem(index)
  def connect_real_time_signal(self):
    self.currentPositions.append(0)  
    if self.isConnected:
      itemIsExist=[]
      newItem = "APPL finance"
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
      self.timer = QtCore.QTimer()  
      self.timer.setInterval(1000)  
      self.timer.timeout.connect(self.fetch_real_time_signal)
      self.timer.start()
    else:
      self.timer.stop()
        
        
  def fetch_real_time_signal(self):
    price = []
    times = []
    
    for _ in range(8):
        ticker = yf.Ticker("AAPL") 
        real_time_data = ticker.info
        currentTime = time.time()
        
        price.append(real_time_data['currentPrice'])
        times.append(currentTime)
        
        if len(price) > 0 and len(times) > 0:
            self.signals.append((times, price))
            self.signalColors.append(self.selectedColor)
            self.signalSpeeds.append(1)
            
            pen = mkPen(color=self.selectedColor, width=2, style=QtCore.Qt.PenStyle.SolidLine)
            self.signalsLines.append(self.graph.plot(times, price, pen=pen))
   
  def show_hide_signal(self):
        selected_items = self.signalListWidget.selectedItems()
        for item in selected_items:
                index = self.signalListWidget.row(item)
                if index < len(self.signalsLines) and self.signalsLines[index] is not None:   
                    if self.signalsLines[index].isVisible():
                        self.signalsLines[index].hide()
                    else:
                        self.signalsLines[index].show()  



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
        backIcon.addPixmap(QtGui.QPixmap("./control/pics/bx--arrow-back.png"),QtGui.QIcon.Mode.Normal,QtGui.QIcon.State.On)
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
        self.uploadIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--upload.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
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
        self.backwardIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--backward.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        backward_button.setIcon(self.backwardIcon)
        backward_button.clicked.connect(lambda: self.backward_plot(radar_plot, plot_num))
        cine_control_layout.addWidget(backward_button)

        play_button = QtWidgets.QPushButton()
        self.playIcon = QtGui.QIcon()
        self.playIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--play.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        play_button.setIcon(self.playIcon)

        play_button.clicked.connect(lambda: self.play_plot(timer, plot_num))
        cine_control_layout.addWidget(play_button)

        forward_button = QtWidgets.QPushButton()
        self.forwardIcon = QtGui.QIcon()
        self.forwardIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--forward.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        forward_button.setIcon(self.forwardIcon)
        forward_button.clicked.connect(lambda: self.forward_plot(radar_plot, plot_num))
        cine_control_layout.addWidget(forward_button)

        pause_button = QtWidgets.QPushButton()
        self.pauseIcon = QtGui.QIcon()
        self.pauseIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--pause.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        pause_button.setIcon(self.pauseIcon)
        pause_button.clicked.connect(lambda: self.pause_plot(timer, plot_num))
        cine_control_layout.addWidget(pause_button)

        stop_button = QtWidgets.QPushButton()
        self.replayIcon = QtGui.QIcon()
        self.replayIcon.addPixmap(QtGui.QPixmap("./control/pics/mdi--replay.png"),QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
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
class SignalViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.linked = False

        self.linkIcon=QtGui.QIcon()
        self.linkIcon.addPixmap(QtGui.QPixmap("./control/pics/solar--link-bold.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)

        self.unLinkIcon=QtGui.QIcon()
        self.unLinkIcon.addPixmap(QtGui.QPixmap("./control/pics/fa-solid--unlink.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)


        self.report_dialog = None
        self.setWindowTitle("Signal Viewer")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumWidth(1200)

        self.original_height = 715

        self.central_widget = QtWidgets.QWidget()

        self.setCentralWidget(self.central_widget)

        self.stack = QtWidgets.QStackedWidget()
        self.verticalBody = QtWidgets.QVBoxLayout(self.central_widget)
        self.verticalBody.addWidget(self.stack)

       
        self.first_page = QtWidgets.QWidget()
        self.first_page_layout = QtWidgets.QVBoxLayout(self.first_page)

    
        self.controlGraphFrame = QtWidgets.QFrame(self)
        self.controlGraphFrame.setMinimumHeight(700)
        self.controlGraphLayout = QtWidgets.QVBoxLayout(self.controlGraphFrame)

        self.controlLayout1 = QtWidgets.QHBoxLayout()
        self.controlLayout1.setContentsMargins(10, 0, 0, 0)


        self.linkButton = QtWidgets.QPushButton()
        self.linkButton.setFixedWidth(50)
        self.linkButton.setFixedHeight(30)
        self.linkButton.setIcon(self.linkIcon)
        self.linkButton.clicked.connect(self.toggle_linking)
        self.controlLayout1.addWidget(self.linkButton)

        self.linkPlayButton = QtWidgets.QPushButton()
        self.linkPlayButton.setFixedWidth(50)
        self.linkPlayButton.setFixedHeight(30)

        self.linkPlayButton.clicked.connect(self.play_linked)
        self.controlLayout1.addWidget(self.linkPlayButton)
        
        self.linkRewindButton = QtWidgets.QPushButton()
        self.linkRewindButton.setFixedWidth(50)
        self.linkRewindButton.setFixedHeight(30)

        self.linkRewindButton.clicked.connect(self.rewind_linked)
        self.controlLayout1.addWidget(self.linkRewindButton)
        
        self.controlLayout1.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))
        self.controlGraphLayout.addLayout(self.controlLayout1)
        
        self.toggleThirdGraphButton = QtWidgets.QPushButton("Third Graph")
        self.toggleThirdGraphButton.setFixedHeight(30)
        self.toggleThirdGraphButton.clicked.connect(self.toggle_third_graph)
        self.controlLayout1.addWidget(self.toggleThirdGraphButton)
        
        self.toggleROIButton = QtWidgets.QPushButton("Show ROI")
        self.toggleROIButton.setFixedHeight(30)
        self.toggleROIButton.clicked.connect(self.toggle_roi)
        self.controlLayout1.addWidget(self.toggleROIButton)

        self.NonRegtangle = QtWidgets.QPushButton("Spider Graph")
        self.NonRegtangle.setFixedHeight(30)
        self.NonRegtangle.clicked.connect(self.show_second_page)  
        self.controlLayout1.addWidget(self.NonRegtangle)

        self.graphlayout = QtWidgets.QVBoxLayout()
        self.controlGraphLayout.addLayout(self.graphlayout)

        
        self.graphFrame1 = QtWidgets.QFrame(self)
        self.graphFrame1.setMinimumHeight(300)
        self.graphLayout1 = QtWidgets.QVBoxLayout(self.graphFrame1)
        self.graphBox1 = GraphWidget(self)
        self.graphLayout1.addWidget(self.graphBox1)
        self.graphlayout.addWidget(self.graphFrame1)

    
        self.graphFrame2 = QtWidgets.QFrame(self)
        self.graphFrame2.setMinimumHeight(300)
        self.graphLayout2 = QtWidgets.QVBoxLayout(self.graphFrame2)
        self.graphBox2 = GraphWidget(self)
        self.graphLayout2.addWidget(self.graphBox2)
        self.graphlayout.addWidget(self.graphFrame2)

        self.first_page_layout.addWidget(self.controlGraphFrame)
        
        self.linkPlayButton.setIcon(self.graphBox1.playIcon)
        self.linkRewindButton.setIcon(self.graphBox1.replayIcon)

        self.glueFrame = QtWidgets.QFrame(self)

        self.glueFrame.setMinimumHeight(300)
        self.glue_layout = QtWidgets.QHBoxLayout(self.glueFrame)
        self.glue_tool_box_layout = QtWidgets.QVBoxLayout()
        self.glue_tool_box = QtWidgets.QFrame(self)
        self.glue_tool_box.setFixedWidth(250)
        self.glue_tool_box.setMinimumHeight(250)

        self.report_layout= QtWidgets.QHBoxLayout()
        reportIcon = QtGui.QIcon()
        reportIcon.addPixmap(QtGui.QPixmap("./control/pics/mdi--file.png"), QtGui.QIcon.Mode.Normal,QtGui.QIcon.State.On)
        self.thirdGraphReportButton = QtWidgets.QPushButton()
        self.thirdGraphReportButton.setFixedWidth(50)
        self.thirdGraphReportButton.setIcon(reportIcon)
        self.thirdGraphReportButton.clicked.connect(self.open_report_dialog)

        self.report_layout.addWidget(self.thirdGraphReportButton)
        self.glue_tool_box_layout.addWidget(self.thirdGraphReportButton)

        self.clearThirdGraphButton = QtWidgets.QPushButton("Clear Third Graph")
        self.clearThirdGraphButton.clicked.connect(self.clear_third_graph)
        self.glue_tool_box_layout.addWidget(self.clearThirdGraphButton)

        self.glueButton = QtWidgets.QPushButton("Glue Signals")
        self.glueButton.clicked.connect(self.glue_signals)
        self.glue_tool_box_layout.addWidget(self.glueButton)

        gap_slider_layout=QtWidgets.QHBoxLayout()
        gap_label = QtWidgets.QLabel("Gap : ")
        self.gap_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.gap_slider.setMinimum(-100)
        self.gap_slider.setMaximum(100)
        self.gap_slider.setValue(0)
        gap_slider_layout.addWidget(gap_label)
        gap_slider_layout.addWidget(self.gap_slider)
        self.glue_tool_box_layout.addLayout(gap_slider_layout)

        self.interpolation_dropdown = QtWidgets.QComboBox()
        self.interpolation_dropdown.addItems(["Linear", "Cubic", "Nearest"])
        self.glue_tool_box_layout.addWidget(self.interpolation_dropdown)
        self.glue_tool_box_layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding))

        self.thirdGraph = pg.PlotWidget()
        self.thirdGraph.showGrid(x=True, y=True)

        self.thirdGraph_container = QtWidgets.QFrame(self)
        self.thirdGraph_layout = QtWidgets.QHBoxLayout()
        self.thirdGraph_layout.setSpacing(20)
        self.thirdGraph_container.setLayout(self.thirdGraph_layout)
        self.thirdGraph_container.layout().addWidget(self.thirdGraph)

        # Glue Tool Box Layout
        self.glue_tool_box.setLayout(self.glue_tool_box_layout)
        self.thirdGraph_container.layout().addWidget(self.glue_tool_box)
        self.glue_layout.addWidget(self.thirdGraph_container)
        self.thirdGraph_container.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.thirdGraph_container.setVisible(True)

        self.first_page_layout.addWidget(self.glueFrame)
        self.glueFrame.setVisible(False)
        self.stack.addWidget(self.first_page)  

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_graphs)
        self.timer.start()

        self.second_page = NonRecPage(self)
        self.stack.addWidget(self.second_page)  

    def alignSpeed(self):
        speed = self.graphBox1.signalSpeeds[0]
        for item in self.graphBox1.signalListWidget.selectedItems():
            index = self.graphBox1.signalListWidget.row(item)
            self.graphBox1.signalSpeeds[index] = speed

        for item in self.graphBox2.signalListWidget.selectedItems():
            index = self.graphBox2.signalListWidget.row(item)
            self.graphBox2.signalSpeeds[index] = speed

    def play_linked(self):

        speed=self.graphBox1.signalSpeeds[0]
        for item in self.graphBox1.signalListWidget.selectedItems():
            index = self.graphBox1.signalListWidget.row(item)
            self.graphBox1.signalSpeeds[index] = speed

        for item in self.graphBox2.signalListWidget.selectedItems():
            index = self.graphBox2.signalListWidget.row(item)
            self.graphBox2.signalSpeeds[index] = speed

        if self.linked:
            if self.graphBox1.isPaused:
                self.graphBox1.playPauseButton.setIcon(self.graphBox1.pauseIcon)
                self.graphBox2.playPauseButton.setIcon(self.graphBox2.pauseIcon)
            else:
                self.graphBox1.playPauseButton.setIcon(self.graphBox1.playIcon)
                self.graphBox2.playPauseButton.setIcon(self.graphBox2.playIcon)
            self.graphBox1.isPaused = not self.graphBox1.isPaused
            self.graphBox2.isPaused = not self.graphBox2.isPaused

    def rewind_linked(self):

        if self.linked:
            if self.graphBox1.isPaused:
                self.graphBox1.playPauseButton.setIcon(self.graphBox1.playIcon)
                self.graphBox2.playPauseButton.setIcon(self.graphBox2.playIcon)
            self.graphBox1.isPaused = False
            self.graphBox2.isPaused = False
            self.graphBox1.rewind()
            self.graphBox2.rewind()

    def toggle_linking(self):
        

        if self.linked:
            self.graphBox1.playPauseButton.setDisabled(False)
            self.graphBox2.playPauseButton.setDisabled(False)
            self.graphBox1.replayButton.setDisabled(False)
            self.graphBox2.replayButton.setDisabled(False)
            self.graphBox2.controlLayout1.setEnabled(False)
            self.graphBox2.graph.setXLink(None)
            self.graphBox2.graph.setYLink(None)
            self.linkButton.setIcon(self.linkIcon)
            self.linked = False
        else:
            self.graphBox1.playPauseButton.setDisabled(True)
            self.graphBox2.playPauseButton.setDisabled(True)
            self.graphBox1.replayButton.setDisabled(True)
            self.graphBox2.replayButton.setDisabled(True)
            self.graphBox2.graph.setXLink(self.graphBox1.graph)
            self.graphBox2.graph.setYLink(self.graphBox1.graph)
            self.linkButton.setIcon(self.unLinkIcon)
            self.linked = True


    def show_second_page(self):
        self.stack.setCurrentWidget(self.second_page)

    def show_first_page(self):
        self.stack.setCurrentWidget(self.first_page)
    def open_report_dialog(self):
        if self.report_dialog is None:
            self.report_dialog = ReportDialog(self.thirdGraph)
            parent_pos = self.mapToGlobal(self.pos())
            self.report_dialog.move(parent_pos.x() + self.width(), parent_pos.y())
        self.report_dialog.show()
    def toggle_third_graph(self):
        if self.glueFrame.isVisible():
            self.glueFrame.setVisible(False)
            self.first_page_layout.removeWidget(self.glueFrame)
            self.setFixedHeight( self.original_height)
            self.toggleThirdGraphButton.setText("Third Graph")
        else:
            self.first_page_layout.addWidget(self.glueFrame)
            self.glueFrame.setVisible(True)
            self.toggleThirdGraphButton.setText("Third Graph")
            self.setFixedHeight( self.original_height+ 300)


    def toggle_roi(self):
        if self.graphBox1.roi.isVisible() and self.graphBox2.roi.isVisible():
            self.graphBox1.roi.hide()
            self.graphBox2.roi.hide()
            self.toggleROIButton.setText("Show ROI")
        else:
            self.graphBox1.roi.show()
            self.graphBox2.roi.show()
            self.toggleROIButton.setText("Hide ROI")

    def clear_third_graph(self):
        self.thirdGraph.clear()

    def glue_signals(self):
        range1 = self.graphBox1.selected_range
        range2 = self.graphBox2.selected_range

        subsignal1 = self.extract_signal(self.graphBox1, range1)
        subsignal2 = self.extract_signal(self.graphBox2, range2)

        gap = self.gap_slider.value()  
        interpolation_order = self.interpolation_dropdown.currentText()  
        glued_signal = self.process_gap_or_overlap(subsignal1, subsignal2, gap, interpolation_order)
        time = np.arange(len(glued_signal))
        self.thirdGraph.plot(time, glued_signal, pen=pg.mkPen('b', width=2))

    def extract_signal(self, graph_widget, selected_range):
        time, amplitude = graph_widget.signals[0]  
        mask = (time >= selected_range[0]) & (time <= selected_range[1])
        return amplitude[mask]

    def process_gap_or_overlap(self, subsignal1, subsignal2, gap, interpolation_order):
      if gap > 0:
          
        interpolation_range = np.linspace(0, gap - 1, gap)
        if interpolation_order == "Linear":
            gap_signal = np.linspace(subsignal1[-1], subsignal2[0], gap)
        elif interpolation_order == "Cubic":
            if len(subsignal1) >= 2 and len(subsignal2) >= 2:
                x_points = [-1, 0, 1, 2]  
                y_points = [subsignal1[-2], subsignal1[-1], subsignal2[0], subsignal2[1]]
                cubic_interp = interp.interp1d(x_points, y_points, kind='cubic')
                gap_signal = cubic_interp(np.linspace(0, 1, gap))  
            else:
                print("Not enough data points for cubic interpolation.")
                return None  
        elif interpolation_order == "Nearest":
            gap_signal = interp.interp1d([0, gap - 1], [subsignal1[-1], subsignal2[0]], kind='nearest')(interpolation_range)

        glued_signal = np.concatenate([subsignal1, gap_signal, subsignal2])

      else:
          overlap = abs(gap)
          if len(subsignal1) < overlap or len(subsignal2) < overlap:
              print("Overlap too large for the signals.")
              return None  

          
          if overlap > len(subsignal1) or overlap > len(subsignal2):
              overlap = min(len(subsignal1), len(subsignal2))  

          
          if interpolation_order == "Linear":
              interpolation_func = interp.interp1d(np.arange(overlap), subsignal1[-overlap:], kind='linear')
          elif interpolation_order == "Cubic":
              interpolation_func = interp.interp1d(np.arange(overlap), subsignal1[-overlap:], kind='cubic')
          elif interpolation_order == "Nearest":
              interpolation_func = interp.interp1d(np.arange(overlap), subsignal1[-overlap:], kind='nearest')

          
          interpolation_range = np.linspace(0, overlap - 1, overlap)
          transition = (1 - interpolation_func(interpolation_range)) * subsignal1[-overlap:] + interpolation_func(interpolation_range) * subsignal2[:overlap]
          glued_signal = np.concatenate([subsignal1[:-overlap], transition, subsignal2[overlap:]])

      return glued_signal  

    def update_graphs(self):
        self.graphBox1.update()
        self.graphBox2.update()


def main():
    app = QtWidgets.QApplication(sys.argv)
    viewer = SignalViewer()
    viewer.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
