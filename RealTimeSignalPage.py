from PyQt6 import QtWidgets, QtCore,QtGui
from PyQt6.QtCore import Qt
import time
import yfinance as yf
from pyqtgraph import mkPen
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget
from PyQt6 import QtWidgets


class RealTimeSignalPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(20)

        self.isPaused = False
        self.isConnected = True

        self.leftLayout = QtWidgets.QVBoxLayout()
        self.leftLayout.setSpacing(20)

        self.back_to_first_page_button = QtWidgets.QPushButton()
        back_icon = QtGui.QIcon()
        back_icon.addPixmap(QtGui.QPixmap("./control/pics/bx--arrow-back.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.back_to_first_page_button.setIcon(back_icon)
        self.back_to_first_page_button.setMinimumHeight(30)
        self.back_to_first_page_button.setFixedWidth(50)
        self.leftLayout.addWidget(self.back_to_first_page_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.graph_widget = pg.PlotWidget()
        self.graph_widget.showGrid(x=True, y=True)
        self.leftLayout.addWidget(self.graph_widget)

        self.cineModeLayout = QtWidgets.QHBoxLayout()
        self.cineModeLayout.setSpacing(5)
        self.cineModeLayout.setContentsMargins(0, 0, 0, 0)
        self.cineModeLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.pauseIcon = QtGui.QIcon()
        self.pauseIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--pause.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.playIcon = QtGui.QIcon()
        self.playIcon.addPixmap(QtGui.QPixmap("./control/pics/fontisto--play.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.playPauseButton = QtWidgets.QPushButton()
        self.playPauseButton.setFixedWidth(50)
        self.playPauseButton.setIcon(self.pauseIcon)
        self.playPauseButton.clicked.connect(self.play_pause)
        self.cineModeLayout.addWidget(self.playPauseButton)
        self.leftLayout.addLayout(self.cineModeLayout)

        self.playPauseButton.setEnabled(False)

        self.mainLayout.addLayout(self.leftLayout)

        self.signalListWidget = QtWidgets.QListWidget()
        self.signalListWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.signalListWidget.setFixedSize(180, 300)
        self.signalListWidget.itemChanged.connect(self.update_play_button_state)
        self.mainLayout.addWidget(self.signalListWidget, alignment=Qt.AlignmentFlag.AlignLeft)

        self.setLayout(self.mainLayout)

        self.back_to_first_page_button.clicked.connect(self.back_to_first_page)
        self.parent.RealSignal.clicked.connect(self.connect_real_time_signal)
    def update_play_button_state(self):
        has_selected = any(item.checkState() == QtCore.Qt.CheckState.Checked for item in self.signalListWidget.findItems("*", QtCore.Qt.MatchFlag.MatchWildcard))
        self.playPauseButton.setEnabled(has_selected)

  

    def play_pause(self):
        if self.isPaused:
            self.timer.stop()
            self.playPauseButton.setIcon(self.playIcon)
        else:
            self.timer.start()
            self.playPauseButton.setIcon(self.pauseIcon)
        self.isPaused = not self.isPaused
        
    def connect_real_time_signal(self):
        if  self.isConnected:
            itemIsExist = []
            newItem = "AAPL finance"
            item = QtWidgets.QListWidgetItem(newItem)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable | QtCore.Qt.ItemFlag.ItemIsSelectable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            
            for index in range(self.signalListWidget.count()):
                if  self.signalListWidget.item(index).text() == newItem:
                    itemIsExist.append(True)      
                else:  
                    itemIsExist.append(False)
            if True in itemIsExist:
                pass
            else:
                self.signalListWidget.addItem(item)     
            
            self.times = []  
            self.prices = []  
            
            self.timer = QtCore.QTimer()  
            self.timer.setInterval(1000)  
            self.timer.timeout.connect(self.fetch_real_time_signal)
            self.timer.start()
        else:
            self.timer.stop()

    def fetch_real_time_signal(self):
        ticker = yf.Ticker("AAPL")
        real_time_data = ticker.info
        currentTime = time.time()
        
        self.prices.append(real_time_data['currentPrice'])
        self.times.append(currentTime)
        
        if not hasattr(self, 'real_time_plot'):  
            pen = mkPen(color='blue', width=2, style=QtCore.Qt.PenStyle.SolidLine)
            self.real_time_plot = self.graph_widget.plot(self.times, self.prices, pen=pen)
        else:
            self.real_time_plot.setData(self.times, self.prices) 
  
    def back_to_first_page(self):
        self.parent.show_first_page()
