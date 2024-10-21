from PyQt6 import QtWidgets, QtCore,QtGui
import scipy.interpolate as interp
import pyqtgraph as pg
import numpy as np
import sys
from ReportDialog import ReportDialog
from GraphWidget import GraphWidget
from NonRecPage import NonRecPage

class SignalViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QtGui.QIcon("./control/pics/logo.png"))

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
