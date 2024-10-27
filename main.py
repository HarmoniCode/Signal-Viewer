from PyQt6 import QtWidgets, QtCore,QtGui
import scipy.interpolate as interp
from scipy.interpolate import Akima1DInterpolator
import pyqtgraph as pg
import numpy as np
import sys
from ReportDialog import ReportDialog
from GraphWidget import GraphWidget
from NonRecPage import NonRecPage

class SignalViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.linked = False
        self.report_dialog = None
        self.original_height = 715

        self.setWindowIcon(QtGui.QIcon("./Icons/pics/logo.png"))
        self.setWindowTitle("Signal Viewer")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumWidth(1200)


        self.linkIcon=QtGui.QIcon()
        self.linkIcon.addPixmap(QtGui.QPixmap("./Icons/pics/solar--link-bold.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)

        self.unLinkIcon=QtGui.QIcon()
        self.unLinkIcon.addPixmap(QtGui.QPixmap("./Icons/pics/fa-solid--unlink.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)

        reportIcon = QtGui.QIcon()
        reportIcon.addPixmap(QtGui.QPixmap("./Icons/pics/mdi--file.png"), QtGui.QIcon.Mode.Normal,QtGui.QIcon.State.On)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.stack = QtWidgets.QStackedWidget()
        self.verticalBody = QtWidgets.QVBoxLayout(self.central_widget)
        self.verticalBody.addWidget(self.stack)

       
        self.first_page = QtWidgets.QWidget()
        self.firstPageLayout = QtWidgets.QVBoxLayout(self.first_page)

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
        self.linkPlayButton.setIcon(QtGui.QIcon("./Icons/pics/fontisto--play.png"))
        self.linkPlayButton.setFixedWidth(50)
        self.linkPlayButton.setFixedHeight(30)

        self.linkPlayButton.clicked.connect(self.play_linked)
        self.controlLayout1.addWidget(self.linkPlayButton)
        
        self.linkRewindButton = QtWidgets.QPushButton()
        self.linkRewindButton.setIcon(QtGui.QIcon("./Icons/pics/mdi--replay.png"))
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

        self.firstPageLayout.addWidget(self.controlGraphFrame)
        
        self.glueFrame = QtWidgets.QFrame(self)

        self.glueFrame.setMinimumHeight(300)
        self.glueLayout = QtWidgets.QHBoxLayout(self.glueFrame)
        self.glueToolBoxLayout = QtWidgets.QVBoxLayout()
        self.glueToolBox = QtWidgets.QFrame(self)
        self.glueToolBox.setFixedWidth(250)
        self.glueToolBox.setMinimumHeight(250)

        self.reportLayout= QtWidgets.QHBoxLayout()
        
        self.thirdGraphReportButton = QtWidgets.QPushButton()
        self.thirdGraphReportButton.setFixedWidth(50)
        self.thirdGraphReportButton.setIcon(reportIcon)
        self.thirdGraphReportButton.clicked.connect(self.open_report_dialog)

        self.reportLayout.addWidget(self.thirdGraphReportButton)
        self.glueToolBoxLayout.addWidget(self.thirdGraphReportButton)

        self.clearThirdGraphButton = QtWidgets.QPushButton("Clear Third Graph")
        self.clearThirdGraphButton.clicked.connect(self.clear_third_graph)
        self.glueToolBoxLayout.addWidget(self.clearThirdGraphButton)

        self.glueButton = QtWidgets.QPushButton("Glue Signals")
        self.glueButton.clicked.connect(self.glue_signals)

        self.glueToolBoxLayout.addWidget(self.glueButton)

        gapSliderLayout=QtWidgets.QHBoxLayout()
        gap_label = QtWidgets.QLabel("Gap : ")
        self.gapSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.gapSlider.setMinimum(-100)
        self.gapSlider.setMaximum(100)
        self.gapSlider.setValue(0)
        gapSliderLayout.addWidget(gap_label)
        gapSliderLayout.addWidget(self.gapSlider)
        self.glueToolBoxLayout.addLayout(gapSliderLayout)

        self.interpolationDropdown = QtWidgets.QComboBox()
        self.interpolationDropdown.addItems(["Linear", "Cubic", "Nearest"])
        self.glueToolBoxLayout.addWidget(self.interpolationDropdown)
        self.glueToolBoxLayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding))

        self.thirdGraph = pg.PlotWidget()
        self.thirdGraph.showGrid(x=True, y=True)

        self.thirdGraphContainer = QtWidgets.QFrame(self)
        self.thirdGraphLayout = QtWidgets.QHBoxLayout()
        self.thirdGraphLayout.setSpacing(20)
        self.thirdGraphContainer.setLayout(self.thirdGraphLayout)
        self.thirdGraphContainer.layout().addWidget(self.thirdGraph)

        self.glueToolBox.setLayout(self.glueToolBoxLayout)
        self.thirdGraphContainer.layout().addWidget(self.glueToolBox)
        self.glueLayout.addWidget(self.thirdGraphContainer)
        self.thirdGraphContainer.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.thirdGraphContainer.setVisible(True)

        self.firstPageLayout.addWidget(self.glueFrame)
        self.glueFrame.setVisible(False)
        self.stack.addWidget(self.first_page)  

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_graphs)
        self.timer.start()

        self.secondPage = NonRecPage(self)
        self.stack.addWidget(self.secondPage)  

    def align_speed(self):
        speed = self.graphBox1.signalSpeeds[0]
        for item in self.graphBox1.signalListWidget.selectedItems():
            index = self.graphBox1.signalListWidget.row(item)
            self.graphBox1.signalSpeeds[index] = speed

        for item in self.graphBox2.signalListWidget.selectedItems():
            index = self.graphBox2.signalListWidget.row(item)
            self.graphBox2.signalSpeeds[index] = speed

    def play_linked(self):
        if self.linked:
          self.align_speed()

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
            self.align_speed()
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
            self.graphBox1.rewindButton.setDisabled(False)
            self.graphBox2.rewindButton.setDisabled(False)
            self.graphBox2.controlLayout1.setEnabled(False)
            self.graphBox2.graph.setXLink(None)
            self.graphBox2.graph.setYLink(None)
            self.linkButton.setIcon(self.linkIcon)
            self.linked = False
        else:
            self.graphBox1.playPauseButton.setDisabled(True)
            self.graphBox2.playPauseButton.setDisabled(True)
            self.graphBox1.rewindButton.setDisabled(True)
            self.graphBox2.rewindButton.setDisabled(True)
            self.graphBox2.graph.setXLink(self.graphBox1.graph)
            self.graphBox2.graph.setYLink(self.graphBox1.graph)
            self.linkButton.setIcon(self.unLinkIcon)
            self.linked = True


    def show_second_page(self):
        self.stack.setCurrentWidget(self.secondPage)

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
            self.firstPageLayout.removeWidget(self.glueFrame)
            self.setFixedHeight( self.original_height)
            self.toggleThirdGraphButton.setText("Third Graph")
        else:
            self.firstPageLayout.addWidget(self.glueFrame)
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
        color1 = self.graphBox1.signalColors[0]
        color2 = self.graphBox2.signalColors[0]
        subsignal1 = self.extract_signal(self.graphBox1, range1)
        subsignal2 = self.extract_signal(self.graphBox2, range2)



        gap = self.gapSlider.value()  
        interpolationOrder = self.interpolationDropdown.currentText()  
        gluedSignal = self.process_gap_or_overlap(subsignal1, subsignal2, gap, interpolationOrder)
        if gap>0:
            self.thirdGraph.plot(np.arange(0, len(gluedSignal), 1), gluedSignal, pen=pg.mkPen('b', width=2))
            self.thirdGraph.plot(subsignal1, pen=pg.mkPen(color1, width=2))
            self.thirdGraph.plot(np.arange(len(subsignal1)+gap, len(gluedSignal), 1), subsignal2, pen=pg.mkPen(color2, width=2))
        else:
            overlap = abs(gap)
            overlap_start = len(subsignal1) - overlap
            
            self.thirdGraph.plot(np.arange(0, len(gluedSignal)), gluedSignal, pen=pg.mkPen('b', width=2))
            self.thirdGraph.plot(np.arange(0, overlap_start), subsignal1[:overlap_start], pen=pg.mkPen(color1, width=2))
            self.thirdGraph.plot(np.arange(len(subsignal1), len(gluedSignal)), subsignal2[overlap:], pen=pg.mkPen(color2, width=2))
                
        

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
            if len(subsignal1) >= 3 and len(subsignal2) >= 3:
              x_points = [-2,-1, 0, 1, 2,3]
              y_points = [subsignal1[-3],subsignal1[-2], subsignal1[-1], subsignal2[0], subsignal2[1],subsignal2[2]]
              akima_interp = Akima1DInterpolator(x_points, y_points)
              gap_signal = akima_interp(np.linspace(0, 1, gap))
            else:
                print("Not enough data points for cubic interpolation.")
                return None  
        elif interpolation_order == "Nearest":
            gap_signal = interp.interp1d([0, gap - 1], [subsignal1[-1], subsignal2[0]], kind='nearest')(interpolation_range)

        glued_signal = np.concatenate([subsignal1, gap_signal, subsignal2])

      else:
          overlap = abs(gap)
          
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
