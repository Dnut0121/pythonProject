import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QLineEdit, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette

class CalculatorLogic:
    def __init__(self):
        self.reset()

    def reset(self):
        self.current = '0'
        self.operator = ''
        self.operand = ''

    def add(self):
        self.operator = '+'
        self.operand = self.current
        self.current = '0'

    def subtract(self):
        self.operator = '-'
        self.operand = self.current
        self.current = '0'

    def multiply(self):
        self.operator = '*'
        self.operand = self.current
        self.current = '0'

    def divide(self):
        self.operator = '/'
        self.operand = self.current
        self.current = '0'

    def toggle_sign(self):
        if self.current.startswith('-'):
            self.current = self.current[1:]
        elif self.current != '0':
            self.current = '-' + self.current

    def percent(self):
        try:
            value = float(self.current)
            value /= 100
            self.current = str(value)
        except:
            self.current = 'Error'

    def append_number(self, num):
        if self.current == '0' and num != '.':
            self.current = num
        else:
            if num == '.' and '.' in self.current:
                return
            self.current += num

    def equal(self):
        try:
            expression = self.operand + self.operator + self.current
            result = eval(expression)
            if isinstance(result, float):
                result = round(result, 6)
            self.current = str(result)
            self.operator = ''
            self.operand = ''
        except:
            self.current = 'Error'

class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.logic = CalculatorLogic()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Calculator')
        self.setFixedSize(320, 520)

        vbox = QVBoxLayout()

        self.prev_label = QLabel('')
        self.prev_label.setAlignment(Qt.AlignRight)
        self.prev_label.setFixedHeight(30)
        self.prev_label.setFont(QFont('Arial', 12))
        self.prev_label.setStyleSheet('color: gray; background-color: rgb(30,30,30);')
        vbox.addWidget(self.prev_label)

        self.result = QLineEdit('0')
        self.result.setAlignment(Qt.AlignRight)
        self.result.setReadOnly(True)
        self.result.setFixedHeight(80)
        self.result.setFont(QFont('Arial', 24))
        self.result.setStyleSheet('color: white; background-color: rgb(30,30,30); border: none;')
        vbox.addWidget(self.result)

        grid = QGridLayout()
        buttons = [
            ('AC', 0, 0), ('+/-', 0, 1), ('%', 0, 2), ('/', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('*', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('0', 4, 0, 1, 2), ('.', 4, 2), ('=', 4, 3)
        ]

        for button in buttons:
            if len(button) == 3:
                text, row, col = button
                btn = QPushButton(text)
                grid.addWidget(btn, row, col)
            else:
                text, row, col, rowspan, colspan = button
                btn = QPushButton(text)
                grid.addWidget(btn, row, col, rowspan, colspan)

            btn.setFixedSize(70, 70)
            btn.setFont(QFont('Arial', 18))

            if text in ['+', '-', '*', '/', '=']:
                btn.setStyleSheet('background-color: orange; color: white; border-radius: 35px;')
            elif text in ['AC', '+/-', '%']:
                btn.setStyleSheet('background-color: lightgray; color: black; border-radius: 35px;')
            else:
                btn.setStyleSheet('background-color: darkgray; color: white; border-radius: 35px;')

            btn.clicked.connect(self.buttonClicked)

        vbox.addLayout(grid)
        self.setLayout(vbox)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        self.setPalette(palette)

    def buttonClicked(self):
        sender = self.sender()
        text = sender.text()

        if text == 'AC':
            self.logic.reset()
        elif text == '+/-':
            self.logic.toggle_sign()
        elif text == '%':
            self.logic.percent()
        elif text == '+':
            self.logic.add()
        elif text == '-':
            self.logic.subtract()
        elif text == '*':
            self.logic.multiply()
        elif text == '/':
            self.logic.divide()
        elif text == '=':
            self.logic.equal()
        else:
            self.logic.append_number(text)

        self.updateDisplay()

    def updateDisplay(self):
        text = self.logic.current
        length = len(text)
        if length < 9:
            font_size = 24
        elif length < 12:
            font_size = 20
        else:
            font_size = 16
        self.result.setFont(QFont('Arial', font_size))
        self.result.setText(text)

        if self.logic.operator and self.logic.operand:
            self.prev_label.setText(f"{self.logic.operand} {self.logic.operator}")
        else:
            self.prev_label.setText('')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec_())
