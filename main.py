from PyQt6.QtPrintSupport import QPrinter
from PyQt6 import QtWidgets, QtCore,QtGui
import scipy.interpolate as interp
import pyqtgraph as pg
import numpy as np
import sys
import csv

class ReportDialog(QtWidgets.QDialog):
    def __init__(self, graph_widget, parent=None):
        super().__init__(parent)
        self.graph_widget = graph_widget  
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

    def add_screenshot_to_report(self):
        graph_widget = self.graph_widget.graph  
        graph_rect = graph_widget.geometry()
        screen = QtGui.QGuiApplication.primaryScreen()
        screenshot = screen.grabWindow(graph_widget.winId(), graph_rect.x(), graph_rect.y(), graph_rect.width() - 10, graph_rect.height() - 10)
        resized_screenshot = screenshot.scaled(600, 400, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        cursor = self.textEdit.textCursor()
        cursor.insertImage(resized_screenshot.toImage(), "Screenshot")  
        self.textEdit.setTextCursor(cursor)

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
    self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
    self.layout.setSpacing(20)  # Remove spacing between items

    self.graph = pg.PlotWidget()
    self.graph.showGrid(x=True, y=True)
    self.layout.addWidget(self.graph)

    self.legend = pg.LegendItem(offset=(70, 20))
    self.legend.setParentItem(self.graph.graphicsItem())

    self.signalFrame = QtWidgets.QFrame(self)
    self.signalFrame.setFixedWidth(250)
    self.layout.addWidget(self.signalFrame)

    self.roi = pg.LinearRegionItem()
    self.roi.setZValue(10)
    self.roi.hide()

    self.graph.addItem(self.roi)

    self.signalLayout = QtWidgets.QVBoxLayout(self.signalFrame)
    self.signalLayout.setContentsMargins(0, 0, 0, 0)  # Remove margins for signal layout

    self.signals = []
    self.signalsLines = []
    self.currentPositions = []
    self.signalColors = []
    self.signalSpeeds = []

    self.isPaused = False

    self.controlLayout3 = QtWidgets.QHBoxLayout()
    loadIcon = QtGui.QIcon()
    loadIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--upload.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.loadSignalButton = QtWidgets.QPushButton()
    self.loadSignalButton.setFixedWidth(50)
    self.loadSignalButton.setIcon(loadIcon)
    self.loadSignalButton.clicked.connect(self.load_signal)
    self.controlLayout3.addWidget(self.loadSignalButton)

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
    self.controlLayout1.setContentsMargins(0, 0, 0, 0)  # Remove margins for control layout

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

    # Control Layout for Play/Pause and Other Buttons
    self.controlLayout1 = QtWidgets.QHBoxLayout()
    self.controlLayout1.setContentsMargins(0, 0, 0, 0)  # Remove margins for control layout

    self.pauseIcon = QtGui.QIcon()
    self.pauseIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--pause.png"),
                            QtGui.QIcon.Mode.Normal,
                            QtGui.QIcon.State.On)
    self.playIcon = QtGui.QIcon()
    self.playIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--play.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.playPauseButton = QtWidgets.QPushButton()
    self.playPauseButton.setIcon(self.pauseIcon)
    self.playPauseButton.clicked.connect(self.play_pause)
    self.controlLayout1.addWidget(self.playPauseButton)

    replayIcon = QtGui.QIcon()
    replayIcon.addPixmap(QtGui.QPixmap("./control/pics/mdi--replay.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.replayButton = QtWidgets.QPushButton()
    self.replayButton.setIcon(replayIcon)
    self.controlLayout1.addWidget(self.replayButton)

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

    self.signalLayout.addLayout(self.controlLayout1)

    # Control Layout for Zoom
    self.controlLayout2 = QtWidgets.QHBoxLayout()
    self.controlLayout2.setContentsMargins(0, 0, 0, 0)  # Remove margins for zoom control

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

    # Cine Mode Panel Layout
    self.cineModePanel = QtWidgets.QHBoxLayout()
    self.cineModePanel.setContentsMargins(0, 0, 0, 0)  # Remove margins for cine mode panel
    self.forwardLabel = QtWidgets.QLabel("Forward")
    self.cineModePanel.addWidget(self.forwardLabel)
    self.mainSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
    self.mainSlider.setMinimum(0)
    self.mainSlider.setMaximum(100)
    self.mainSlider.setValue(0)
    self.mainSlider.valueChanged.connect(self.slider_moved)
    self.cineModePanel.addWidget(self.mainSlider)
    self.backWard = QtWidgets.QLabel("Backward")
    self.cineModePanel.addWidget(self.backWard)
    self.signalLayout.addLayout(self.cineModePanel)

    self.playPauseButton.setEnabled(False)

    self.selectedColor = (255, 0, 0)
    self.defaultSpeed = 10

    self.roi.sigRegionChanged.connect(self.on_roi_changed)

    self.report_dialog = None

    self.timer = QtCore.QTimer()
    self.timer.setInterval(100)
    self.timer.timeout.connect(self.update)
    self.timer.start()

    self.currentSignalIndex = None 

  def on_roi_changed(self):
    self.selected_range = self.roi.getRegion()

  def show_context_menu(self, pos):
        item = self.signalListWidget.itemAt(pos)
        if item is not None:
            index = self.signalListWidget.row(item)
            self.show_statistics_tooltip(index, pos)

  def show_statistics_tooltip(self, index, pos):
      if index < len(self.signals):
          time, amplitude = self.signals[index]
          max_value = np.max(amplitude)
          min_value = np.min(amplitude)
          time_length = time[-1] - time[0]  
          speed = self.signalSpeeds[index]
          color = self.signalColors[index]
          statistics_message = (
            f"<b style='color: blue;'>Signal:</b> {self.signalListWidget.item(index).text()}<br>"
            f"<b style='color: blue;'>Max Value:</b> {max_value}<br>"
            f"<b style='color: blue;'>Min Value:</b> {min_value}<br>"
            f"<b style='color: blue;'>Time Length:</b> {time_length:.2f}<br>"
            f"<b style='color: blue;'>Speed:</b> {speed}<br>"
            f"<b style='color: blue;'>Color:</b> {color}"
          )
          QtWidgets.QToolTip.showText(self.signalListWidget.mapToGlobal(pos), statistics_message)

  def open_report_dialog(self):
    if self.report_dialog is None:
        self.report_dialog = ReportDialog(self)
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

  def slider_moved(self, value):
      for index in range(self.signalListWidget.count()):
          item = self.signalListWidget.item(index)
          if item.isSelected(): 
              self.currentSignalIndex = index 
              self.currentPositions[index] = int(value / 100 * len(self.signals[index][0]))
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
                if index == self.currentSignalIndex:
                    self.mainSlider.setValue(int(new_pos / len(time) * 100))

  def play_pause(self):
    if self.isPaused:
        self.playPauseButton.setIcon(self.pauseIcon)
    else:
        self.playPauseButton.setIcon(self.playIcon)
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
                # Remove from legend
                self.legend.removeItem(item.text())

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

      # Zoom in by reducing the range by 10%
        new_x_range = (current_x_range[0] + (current_x_range[1] - current_x_range[0]) * 0.1,
                       current_x_range[1] - (current_x_range[1] - current_x_range[0]) * 0.1)
        new_y_range = (current_y_range[0] + (current_y_range[1] - current_y_range[0]) * 0.1,
                       current_y_range[1] - (current_y_range[1] - current_y_range[0]) * 0.1)

        self.graph.setXRange(*new_x_range, padding=0)
        self.graph.setYRange(*new_y_range, padding=0)

  def zoom_out(self):
        current_x_range = self.graph.viewRange()[0]
        current_y_range = self.graph.viewRange()[1]

      # Zoom out by increasing the range by 10%
        new_x_range = (current_x_range[0] - (current_x_range[1] - current_x_range[0]) * 0.1,
                       current_x_range[1] + (current_x_range[1] - current_x_range[0]) * 0.1)
        new_y_range = (current_y_range[0] - (current_y_range[1] - current_y_range[0]) * 0.1,
                       current_y_range[1] + (current_y_range[1] - current_y_range[0]) * 0.1)

        self.graph.setXRange(*new_x_range, padding=0)
        self.graph.setYRange(*new_y_range, padding=0)
class SignalViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Signal Viewer")
        self.setGeometry(100, 100, 1000, 600)
        self.setMinimumHeight(615)

        self.original_height = 615
        self.original_width = 1000

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.verticalBody = QtWidgets.QVBoxLayout(self.central_widget)

        # Control Layout
        self.controlGraphFrame = QtWidgets.QFrame(self)
        self.controlGraphFrame.setMinimumHeight(600)
        self.controlGraphLayout = QtWidgets.QVBoxLayout(self.controlGraphFrame)

        self.controlLayout1 = QtWidgets.QHBoxLayout()
        self.controlLayout1.setContentsMargins(10, 0, 0, 0)

        # Toggle Third Graph Button
        self.toggleThirdGraphButton = QtWidgets.QPushButton("Show Third Graph")
        self.toggleThirdGraphButton.clicked.connect(self.toggle_third_graph)
        self.controlLayout1.addWidget(self.toggleThirdGraphButton)

        # Toggle ROI Button
        self.toggleROIButton = QtWidgets.QPushButton("Show ROI")
        self.toggleROIButton.clicked.connect(self.toggle_roi)
        self.controlLayout1.addWidget(self.toggleROIButton)

        # Spacer
        self.controlLayout1.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))
        self.controlGraphLayout.addLayout(self.controlLayout1)

        # Graph Layout
        self.graphlayout = QtWidgets.QVBoxLayout()
        self.controlGraphLayout.addLayout(self.graphlayout)

        # First Graph
        self.graphFrame1 = QtWidgets.QFrame(self)
        self.graphFrame1.setMinimumHeight(250)
        self.graphLayout1 = QtWidgets.QVBoxLayout(self.graphFrame1)
        self.graphBox1 = GraphWidget(self)
        self.graphLayout1.addWidget(self.graphBox1)
        self.graphlayout.addWidget(self.graphFrame1)

        # Second Graph
        self.graphFrame2 = QtWidgets.QFrame(self)
        self.graphFrame2.setMinimumHeight(250)
        self.graphLayout2 = QtWidgets.QVBoxLayout(self.graphFrame2)
        self.graphBox2 = GraphWidget(self)
        self.graphLayout2.addWidget(self.graphBox2)
        self.graphlayout.addWidget(self.graphFrame2)

        self.verticalBody.addWidget(self.controlGraphFrame)

        # Glue Layout
        self.glueFrame = QtWidgets.QFrame(self)
        self.glueFrame.setMinimumHeight(300)
        self.glue_layout = QtWidgets.QHBoxLayout(self.glueFrame)

        self.glue_tool_box_layout = QtWidgets.QVBoxLayout()
        self.glue_tool_box = QtWidgets.QFrame(self)
        self.glue_tool_box.setFixedWidth(250)
        self.glue_tool_box.setMinimumHeight(250)

        # Clear Third Graph Button
        self.clearThirdGraphButton = QtWidgets.QPushButton("Clear Third Graph")
        self.clearThirdGraphButton.clicked.connect(self.clear_third_graph)
        self.clearThirdGraphButton.hide()
        self.glue_tool_box_layout.addWidget(self.clearThirdGraphButton)

        # Glue Signals Button
        self.glueButton = QtWidgets.QPushButton("Glue Signals")
        self.glueButton.clicked.connect(self.glue_signals)
        self.glue_tool_box_layout.addWidget(self.glueButton)

        # Gap Slider
        self.gap_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.gap_slider.setMinimum(-100)
        self.gap_slider.setMaximum(100)
        self.gap_slider.setValue(0)
        self.glue_tool_box_layout.addWidget(self.gap_slider)

        # Interpolation Dropdown
        self.interpolation_dropdown = QtWidgets.QComboBox()
        self.interpolation_dropdown.addItems(["Linear", "Cubic", "Nearest"])
        self.glue_tool_box_layout.addWidget(self.interpolation_dropdown)

        # Third Graph
        self.thirdGraph = pg.PlotWidget()
        self.thirdGraph.showGrid(x=True, y=True)

        # Third Graph Container
        self.thirdGraph_container = QtWidgets.QFrame(self)
        thirdGraph_layout = QtWidgets.QHBoxLayout()
        thirdGraph_layout.setSpacing(20)
        self.thirdGraph_container.setLayout(thirdGraph_layout)
        self.thirdGraph_container.layout().addWidget(self.thirdGraph)

        # Glue Tool Box Layout
        self.glue_tool_box.setLayout(self.glue_tool_box_layout)
        self.thirdGraph_container.layout().addWidget(self.glue_tool_box)
        self.glue_layout.addWidget(self.thirdGraph_container)

        self.thirdGraph_container.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.thirdGraph_container.setVisible(False)

        self.verticalBody.addWidget(self.glueFrame)

        # Timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_graphs)
        self.timer.start()

    def toggle_third_graph(self):
        if self.thirdGraph_container.isVisible():
            self.thirdGraph_container.setVisible(False)
            self.toggleThirdGraphButton.setText("Show Third Graph")
            self.setFixedSize(self.original_width, self.original_height)
        else:
            self.thirdGraph_container.setVisible(True)
            self.toggleThirdGraphButton.setText("Hide Third Graph")
            self.setFixedSize(self.original_width , self.original_height+300)
        

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
