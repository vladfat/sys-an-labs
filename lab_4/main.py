__author__ = 'vlad'
# coding: utf8

import sys

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtGui import QTextDocument, QFont
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt5.uic import loadUiType

from lab_4.solver_manager import SolverManager
from lab_4.bruteforce import BruteForceWindow

app = QApplication(sys.argv)
app.setApplicationName('lab4_sa')
form_class, base_class = loadUiType('lab_4/main_window.ui')


class MainWindow(QDialog, form_class):
    # signals:
    input_changed = pyqtSignal('QString')
    output_changed = pyqtSignal('QString')


    def __init__(self, *args):
        super(MainWindow, self).__init__(*args)

        # setting up ui
        self.setupUi(self)

        # other initializations
        self.dimensions = [self.x1_dim.value(), self.x2_dim.value(),
                                    self.x3_dim.value(), self.y_dim.value()]
        self.degrees = [self.x1_deg.value(), self.x2_deg.value(), self.x3_deg.value()]
        self.type = 'null'
        if self.radio_sh_cheb.isChecked():
            self.type = 'sh_cheb_doubled'
        elif self.radio_cheb.isChecked():
            self.type = 'cheb'
        elif self.radio_sh_cheb_2.isChecked():
            self.type = 'sh_cheb_2'
        self.custom_func_struct = self.custom_check.isChecked()
        self.input_path = self.line_input.text()
        self.output_path = self.line_output.text()
        self.samples_num = self.sample_spin.value()
        self.lambda_multiblock = self.lambda_check.isChecked()
        self.weight_method = self.weights_box.currentText().lower()
        self.manager = None


        #set tablewidget
        self.tablewidget.verticalHeader().hide()
        column_size = [40, 70, 70, 70,160, 60, 160,80]
        for index, size in enumerate(column_size):
             self.tablewidget.setColumnWidth(index,size)
        data = ['9999', '999', '9999,99','1234568', 'Безпечна ситуація']
        self.insert_data(data)
        return

    @pyqtSlot()
    def input_clicked(self):
        filename = QFileDialog.getOpenFileName(self, 'Open data file', '.', 'Data file (*.xlsx)')[0]
        if filename == '':
            return
        if filename != self.input_path:
            self.input_path = filename
            self.input_changed.emit(filename)
        return

    @pyqtSlot('QString')
    def input_modified(self, value):
        if value != self.input_path:
            self.input_path = value
        return

    @pyqtSlot()
    def output_clicked(self):
        filename = QFileDialog.getSaveFileName(self, 'Save data file', '.', 'Spreadsheet (*.xlsx)')[0]
        if filename == '':
            return
        if filename != self.output_path:
            self.output_path = filename
            self.output_changed.emit(filename)
        return

    @pyqtSlot('QString')
    def output_modified(self, value):
        if value != self.output_path:
            self.output_path = value
        return

    @pyqtSlot(int)
    def samples_modified(self, value):
        self.samples_num = value
        return

    @pyqtSlot(int)
    def dimension_modified(self, value):
        sender = self.sender().objectName()
        if sender == 'x1_dim':
            self.dimensions[0] = value
        elif sender == 'x2_dim':
            self.dimensions[1] = value
        elif sender == 'x3_dim':
            self.dimensions[2] = value
        elif sender == 'y_dim':
            self.dimensions[3] = value
        return

    @pyqtSlot(int)
    def degree_modified(self, value):
        sender = self.sender().objectName()
        if sender == 'x1_deg':
            self.degrees[0] = value
        elif sender == 'x2_deg':
            self.degrees[1] = value
        elif sender == 'x3_deg':
            self.degrees[2] = value
        return

    @pyqtSlot(bool)
    def type_modified(self, isdown):
        if (isdown):
            sender = self.sender().objectName()
            if sender == 'radio_sh_cheb':
                self.type = 'sh_cheb_doubled'
            elif sender == 'radio_cheb':
                self.type = 'cheb'
            elif sender == 'radio_sh_cheb_2':
                self.type = 'sh_cheb_2'
        return

    @pyqtSlot(bool)
    def structure_changed(self, isdown):
        self.custom_func_struct = isdown

    @pyqtSlot()
    def plot_clicked(self):
        if self.manager:
            try:
                self.manager.plot(self.predictBox.value())
            except Exception as e:
                QMessageBox.warning(self,'Error!','Error happened during plotting: ' + str(e))
        return

    @pyqtSlot()
    def exec_clicked(self):
        self.exec_button.setEnabled(False)
        try:
            self.manager = SolverManager(self._get_params())
            self.manager.prepare(self.input_path)
            self.manager.start_machine()
            # s = [1,2,3,4]
            # for i in range(4):
            #     for m, item in enumerate(s):
            #         ni = QTableWidgetItem(str(item))
            #         self.tableWidget.setItem(i, m, ni)
        except Exception as e:
            QMessageBox.warning(self,'Error!','Error happened during execution: ' + str(e))
        self.exec_button.setEnabled(True)
        return

    @pyqtSlot()
    def bruteforce_called(self):
        BruteForceWindow.launch(self)
        return

    @pyqtSlot(int, int, int)
    def update_degrees(self, x1_deg, x2_deg, x3_deg):
        self.x1_deg.setValue(x1_deg)
        self.x2_deg.setValue(x2_deg)
        self.x3_deg.setValue(x3_deg)
        return

    @pyqtSlot(bool)
    def lambda_calc_method_changed(self, isdown):
        self.lambda_multiblock = isdown
        return

    @pyqtSlot('QString')
    def weights_modified(self, value):
        self.weight_method = value.lower()
        return

    def _get_params(self):
        return dict(custom_struct=self.custom_func_struct,poly_type=self.type, degrees=self.degrees,
                    dimensions=self.dimensions,
                    samples=self.samples_num, output_file=self.output_path,
                    weights=self.weight_method, lambda_multiblock=self.lambda_multiblock,
                    pred_steps = self.predictBox.value())

    def insert_data(self, data):
        assert len(data) <= 8
        for i,d in enumerate(data):
            item = QTableWidgetItem(d)
            item.setTextAlignment(Qt.AlignHCenter)
            self.tablewidget.setItem(0,i,item)

# -----------------------------------------------------#
form = MainWindow()
form.setWindowTitle('System Analysis - Lab 4')
form.show()
sys.exit(app.exec_())
