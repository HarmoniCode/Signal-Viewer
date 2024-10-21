from PyQt6.QtPrintSupport import QPrinter
from PyQt6 import QtWidgets, QtCore,QtGui

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
        
    def show_statistics_table(self):
        selectedIndecies = self.graph.parent().signalListWidget.selectedIndexes()
        if len(selectedIndecies) > 0:
            statistics = self.graph.parent().show_statistics_tooltip(selectedIndecies[0].row())

        if statistics:
            
            cursor = self.textEdit.textCursor()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)  
            
            keyword_format = QtGui.QTextCharFormat()
            keyword_format.setFontWeight(QtGui.QFont.Weight.Bold)
            keyword_format.setFontPointSize(9)
            keyword_format.setForeground(QtGui.QColor("blue"))

            value_format = QtGui.QTextCharFormat()
            value_format.setFontWeight(QtGui.QFont.Weight.Bold)
            value_format.setFontPointSize(9)
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