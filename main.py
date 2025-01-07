from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QMenuBar, QFileDialog, QLineEdit, QHBoxLayout, QWidget, QDialog, QVBoxLayout, QComboBox, QLabel, QPushButton,QTextEdit
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QAction
from PySide6.QtCore import Qt, QRegularExpression
import sys
import os
import subprocess

from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QRect,QSize
from PySide6.QtGui import QTextCursor, QPainter
import sys


from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QMenu, QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog, QDialog, QTreeView, QFileSystemModel
from PySide6.QtGui import QAction, QTextCursor, QPainter, QFont, QColor, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtCore import Qt, QRegularExpression, QSize,QEvent
from PySide6.QtGui import QKeyEvent

class LineNumberArea(QLabel):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.line_number_font = QFont("Courier", 14)
        self.line_number_color = "#a4a4a4"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), "#444444")

        painter.setFont(self.line_number_font)
        painter.setPen(self.line_number_color)

        block_count = self.editor.blockCount()
        current_block = self.editor.firstVisibleBlock()
        block_number = current_block.blockNumber()
        top = int(self.editor.blockBoundingGeometry(current_block).translated(self.editor.contentOffset()).top())

        for i in range(block_count):
            if top < event.rect().bottom():
                painter.drawText(-2, top, self.width(), self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, str(block_number + 1))
            block_number += 1
            current_block = current_block.next()
            top += int(self.editor.blockBoundingRect(current_block).height())

    def sizeHint(self):
        return QSize(50, 0)


class FileNameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New File")

        layout = QVBoxLayout()
        self.label = QLabel("File Name :")
        layout.addWidget(self.label)
        self.file_name_input = QLineEdit(self)
        layout.addWidget(self.file_name_input)
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def get_file_name(self):
        return self.file_name_input.text().strip()


class CHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # Bleu clair pour les mots-clés
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = ["int", "long", "unsigned", "return", "void", "struct", "if", "else", "for", "while", "size_t",
                    "let", "mut", "fn", "impl", "async"]
        for word in keywords:
            pattern = QRegularExpression(rf"\b{word}\b")
            self.highlighting_rules.append((pattern, keyword_format))

        type_format = QTextCharFormat()
        type_format.setForeground(QColor("#4EC9B0"))  # Vert clair pour les types
        type_words = ["char", "FILE"]
        for word in type_words:
            pattern = QRegularExpression(rf"\b{word}\b")
            self.highlighting_rules.append((pattern, type_format))


        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#EAB24F"))  # Jaune clair pour les fonctions
        function_pattern = QRegularExpression(r"\b\w+\s*\(.*\)\s*\{")  # Mot suivi de parenthèses et d'une accolade
        self.highlighting_rules.append((function_pattern, function_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Vert pour les commentaires
        comment_pattern = QRegularExpression(r"//[^\n]*|/\*.*\*/")
        self.highlighting_rules.append((comment_pattern, comment_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Rouge clair pour les chaînes
        string_pattern = QRegularExpression(r"\".*\"")
        self.highlighting_rules.append((string_pattern, string_format))


        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#4B83BA"))  # Vert pour les nombres
        number_pattern = QRegularExpression(r"\b\d+\b")
        self.highlighting_rules.append((number_pattern, number_format))


        brace_format = QTextCharFormat()
        brace_format.setForeground(QColor("#C586C0"))  # Violet pour les accolades normales
        brace_pattern = QRegularExpression(r"[{}]")
        self.highlighting_rules.append((brace_pattern, brace_format))

        parenthesis_format = QTextCharFormat()
        parenthesis_format.setForeground(QColor("#C586C0"))
        parenthesis_pattern = QRegularExpression(r"[\(\)]")
        self.highlighting_rules.append((parenthesis_pattern, parenthesis_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = pattern.globalMatch(text)
            while expression.hasNext():
                match = expression.next()


                if format.foreground().color() == QColor("#DCDCAA") and match.captured().endswith("{"):

                    function_brace_format = QTextCharFormat()
                    function_brace_format.setForeground(QColor("#DCDCAA"))
                    start = match.capturedStart()
                    end = match.capturedEnd()


                    self.setFormat(start, end - start, function_brace_format)
                else:

                    self.setFormat(match.capturedStart(), match.capturedLength(), format)


class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):

        index = self.indexAt(position)
        file_path = self.model().filePath(index)
        context_menu = QMenu(self)
        create_file_action = QAction("New File", self)
        delete_action = QAction("Delete", self)
        context_menu.addAction(create_file_action)
        context_menu.addAction(delete_action)
        create_file_action.triggered.connect(lambda: self.create_file(file_path))
        delete_action.triggered.connect(lambda: self.delete_file(file_path))

        context_menu.exec(self.viewport().mapToGlobal(position))

    def create_file(self, file_path):
        file_dir = os.path.dirname(file_path)
        dialog = FileNameDialog(self)
        if dialog.exec() == QDialog.Accepted:
            file_name = dialog.get_file_name()
            if file_name:
                current_dir = file_dir
                file_path = os.path.join(current_dir, file_name)
                if ".c" in file_path:
                    with open(file_path, 'w') as new_file:
                        print("file", file_path)
                        new_file.write("""// Here a new C file have fun :)\n#include <stdio.h>\n\nint main(){\n    printf("Hello, world!\\n");\nreturn 0;\n}\n""")

                elif ".rs" in file_path:
                    with open(file_path, 'w') as new_file:
                        print("file", file_path)
                        new_file.write("""// Here a new Rust file have fun :)\nfn main(){\n    println!("Hellow World!");\n}""")


    def delete_file(self, file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File deleted: {file_path}")
            self.model()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple IDE")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        layout = QHBoxLayout(central_widget)
        self.showMaximized()

        self.layout_button = QVBoxLayout()
        layout.addLayout(self.layout_button)
        self.layout_button.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.label_working_dir = QLabel("Working directory:")
        self.label_working_dir.setStyleSheet("color:white;")
        self.current_directory_line_edit = QLineEdit()
        self.current_directory_line_edit.setMaximumWidth(400)
        self.current_directory_line_edit.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_button.addWidget(self.label_working_dir)
        self.layout_button.addWidget(self.current_directory_line_edit)

        self.label_compile = QLabel("Compile command:")
        self.label_compile.setStyleSheet("color:white;")
        self.layout_button.addWidget(self.label_compile)

        self.layout_compilation_options = QHBoxLayout()
        self.layout_button.addLayout(self.layout_compilation_options)

        self.compile_line_edit = QLineEdit()
        self.compile_line_edit.setMaximumWidth(300)
        self.compile_line_edit.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.layout_compilation_options.addWidget(self.compile_line_edit)

        self.combo_box = QComboBox(self)
        self.combo_box.setMaximumWidth(100)
        self.combo_box.addItems(["Current File", "main"])
        self.layout_compilation_options.addWidget(self.combo_box)

        self.combo_box.currentTextChanged.connect(self.refresh_compilation_cmd)

        self.layout_more_button = QHBoxLayout()
        self.layout_button.addLayout(self.layout_more_button)

        self.compile_button = QPushButton("compile")
        self.compile_button.clicked.connect(self.compile_programm)
        self.layout_more_button.addWidget(self.compile_button)

        self.run_button = QPushButton("run")
        self.run_button.clicked.connect(self.run_programm)
        self.layout_more_button.addWidget(self.run_button)

        self.compile_and_run_button = QPushButton("compile and run")
        self.compile_and_run_button.clicked.connect(self.compile_and_run_programm)
        self.layout_button.addWidget(self.compile_and_run_button)

        self.label_compilation = QLabel("Compilation statut:")
        self.label_compilation.setStyleSheet("color:white;")
        self.layout_button.addWidget(self.label_compilation)

        self.compilation_field = QPlainTextEdit()
        self.compilation_field.setReadOnly(True)
        self.compilation_field.setMaximumWidth(400)
        #self.compilation_field.setMaximumHeight(500)

        self.compilation_field.setStyleSheet("""
                            QPlainTextEdit {
                                background-color: #2B2B2B;
                                color: #D4D4D4;
                                font-family: Consolas;
                                font-size: 16px;
                            }
                        """)



        self.layout_button.addWidget(self.compilation_field)

        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet("""
                    QPlainTextEdit {
                        background-color: #2B2B2B;
                        color: #D4D4D4;
                        font-family: Consolas;
                        font-size: 18px;
                    }
                QPlainTextEdit:focus {
                    border: 1px solid #7A7A7A; /* Bordure de 2px de couleur #7A7A7A */
                    }
                    
                """)

        self.editor.installEventFilter(self)


        layout.addWidget(self.editor)

        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath('')

        self.tree_view = CustomTreeView()
        self.tree_view.setModel(self.file_system_model)
        self.tree_view.setRootIndex(self.file_system_model.index(""))
        self.tree_view.setSortingEnabled(True)

        for col in range(1, self.file_system_model.columnCount()):
            self.tree_view.setColumnHidden(col, True)

        self.tree_view.setColumnWidth(0, 300)


        self.tree_view.setStyleSheet("""
            QTreeView {
                background-color: #3C3F41;
                color: #D4D4D4;
                border: none;
            }
            QTreeView::item {
                background-color: #3C3F41;
                color: #D4D4D4;
            }
            QTreeView::item:selected {
                background-color: #1b4f77;
                color: #D4D4D4;
            }
            QHeaderView::section {
                background-color: #1b4f77;
                color: #D4D4D4;
                border: 1px solid #0D293E;
                }
            QScrollBar:vertical
    {
        background-color: #2A2929;

    }


""")

        self.tree_view.setIndentation(20)
        self.tree_view.setMaximumWidth(400)

        self.tree_view.clicked.connect(self.open_file_from_tree)


        self.layout_button.addWidget(self.tree_view)

        self.setCentralWidget(central_widget)


        self.highlighter = CHighlighter(self.editor.document())

        self.line_number_area = LineNumberArea(self.editor)
        layout.addWidget(self.line_number_area)
        layout.addWidget(self.editor)

        self.setCentralWidget(central_widget)

        self.editor.verticalScrollBar().valueChanged.connect(self.line_number_area.update)

        self.line_number_area.update()

        self.editor.document().blockCountChanged.connect(self.line_number_area.update)
        self.editor.verticalScrollBar().valueChanged.connect(self.line_number_area.update)

        self.highlighter = CHighlighter(self.editor.document())

        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D2D2D;
            }
            QMenuBar {
                background-color: #2D2D2D;
                color: #D4D4D4;
            }
            QMenuBar::item:selected {
                background-color: #444444;
            }
            QStatusBar {
                background-color: #2D2D2D;
                color: #D4D4D4;
            }
        """)

        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")

        self.new_file_action = QAction("New file", self)
        self.new_file_action.triggered.connect(self.create_new_file)
        self.file_menu.addAction(self.new_file_action)

        self.open_action = QAction("Open File", self)
        self.open_action.triggered.connect(self.open_file)
        self.file_menu.addAction(self.open_action)

        self.open_project_action = QAction("Open Project", self)
        self.open_project_action.triggered.connect(self.open_project)
        self.file_menu.addAction(self.open_project_action)

        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.save_file)
        self.file_menu.addAction(self.save_action)

        self.file_to_execute = "main"

        self.language = "C"
        self.windowed = False

        with open("parameters", "r") as file:
            data = file.read()
            last_file = "Not Found"
            compile_command = "Not found"

            for line in data.split("\n"):
                print(line)
                if line.startswith("last_file:"):
                    last_file = line.replace("last_file:", "").strip()
                elif line.startswith("language:"):
                    self.language = line.replace("language:", "").strip()
                elif line.startswith("compile_cmd_c:"):
                    compile_command_c = line.replace("compile_cmd_c:", "").strip()
                elif line.startswith("compile_cmd_rust:"):
                    compile_command_rust = line.replace("compile_cmd_rust:", "").strip()
                elif line.startswith("windowed:"):
                    windowed = line.replace("windowed:", "").strip()
                    if windowed == "False":
                        self.windowed = False
                    else:
                        self.windowed = True

            self.current_directory_line_edit.setText(last_file)
            self.compile_line_edit.setText(compile_command_rust)
            self.open_file_path(last_file)
            self.open_project(os.path.dirname(last_file))

    def eventFilter(self, obj, event):
        if obj is self.editor and event.type() == QEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent):

                if event.key() == Qt.Key.Key_Tab:
                    # Remplacer la tabulation par 4 espaces
                    cursor = self.editor.textCursor()
                    cursor.insertText("    ")
                    return True
        return super().eventFilter(obj, event)

    def open_file_path(self, file_path):
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                file_content = file.read()
            self.editor.setPlainText(file_content)
            self.current_directory_line_edit.setText(file_path)

            if file_path.endswith(".c"):
                new_compile_cmd = self.create_new_compile_command_with_name(self.compile_line_edit.text(),
                                                                            os.path.basename(file_path))
                self.compile_line_edit.setText(new_compile_cmd)
            elif file_path.endswith(".rs"):
                new_compile_cmd = self.create_new_compile_command_with_name(self.compile_line_edit.text(),
                                                                            os.path.basename(file_path))
                self.compile_line_edit.setText(new_compile_cmd)

    def open_file_from_tree(self, index):
        file_path = self.file_system_model.filePath(index)

        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                file_content = file.read()
            self.editor.setPlainText(file_content)
            self.current_directory_line_edit.setText(file_path)

            if file_path.endswith(".c"):
                new_compile_cmd = self.create_new_compile_command_with_name(self.compile_line_edit.text(),
                                                                            os.path.basename(file_path))
                self.compile_line_edit.setText(new_compile_cmd)


    def refresh_compilation_cmd(self):
        if self.combo_box.currentText() == "Current File":
            file_name = os.path.basename(self.current_directory_line_edit.text())
            print("current file", os.path.basename(self.current_directory_line_edit.text()))
        else:
            file_name = "main.c"

        new_cmd = self.create_new_compile_command_with_name(self.compile_line_edit.text(), file_name)

        self.compile_line_edit.setText(new_cmd)


    def get_file_name_to_execute(self):
        compile_command = self.compile_line_edit.text()

        if "cargo" in compile_command:
            dir_to_execute = self.current_directory_line_edit.text()

            dir_to_execute = "/".join(dir_to_execute.split("/")[:-2])
            print("dir_to_execute", dir_to_execute)
            file_to_execute = dir_to_execute.split("/")[-1]

            file_to_execute = dir_to_execute + f"/target/debug/{file_to_execute}"

            print("file to _exe", file_to_execute)

        elif "-o" not in compile_command:
            file_to_execute = "a"
        else:
            split_command = compile_command.split("-o")
            file_to_execute = split_command[1].strip().split(" ")[0]

        return file_to_execute

    def compile_programm(self):
        working_dir = os.path.dirname(self.current_directory_line_edit.text())
        compile_cmd = self.compile_line_edit.text()

        try:
            result = subprocess.run(compile_cmd, cwd=working_dir, check=True, capture_output=True, text=True)
            print("Successful compilation.")
            self.compilation_field.setPlainText("Successful compilation.")
        except subprocess.CalledProcessError as e:
            self.compilation_field.setPlainText(e.stderr)
            print("Compilation error :", e.stderr)

    def run_programm(self):
        selected_option = self.combo_box.currentText()
        working_dir = os.path.dirname(self.current_directory_line_edit.text())

        if selected_option == "Current File":
            file_to_ex = self.get_file_name_to_execute()
        else:
            file_to_ex = "main"

        print("windowed", self.windowed)

        if self.windowed == True:
            os.system(file_to_ex)

        else:
            batch_script = os.path.join(working_dir, "run_with_pause.bat")
            with open(batch_script, "w") as f:
                #f.write(f'"{working_dir}/{file_to_ex}.exe"\n')
                f.write(f'"{file_to_ex}.exe"\n')
                f.write("pause\n")

            os.startfile(batch_script)

    def compile_and_run_programm(self):
        file_to_ex = self.get_file_name_to_execute()
        working_dir = os.path.dirname(self.current_directory_line_edit.text())
        compile_cmd = self.compile_line_edit.text()

        try:
            result = subprocess.run(compile_cmd, cwd=working_dir, check=True, capture_output=True, text=True)
            print("Successful compilation.")
            self.compilation_field.setPlainText("Successful compilation.")
        except subprocess.CalledProcessError as e:
            self.compilation_field.setPlainText(e.stderr)
            print("Compilation error :", e.stderr)

        try:
            os.startfile(working_dir + f"/{file_to_ex}.exe")
        except Exception as e:
            print("Error during execution :", e)

    def create_new_compile_command_with_name(self, old_compile_cmd, new_name_file):
        new_compile_cmd = old_compile_cmd
        for word in old_compile_cmd.split(" "):
            if ".c" or ".rs" in word:
                new_c_file = new_name_file
                new_compile_cmd = old_compile_cmd.replace(word, new_c_file)
                print("word", word, "new c file", new_c_file)
        return new_compile_cmd

    def create_new_file(self):
        dialog = FileNameDialog(self)
        if dialog.exec() == QDialog.Accepted:
            file_name = dialog.get_file_name()
            if file_name:
                current_dir = os.path.abspath(self.current_directory_line_edit.text())
                file_path = os.path.join(current_dir, file_name)
                if ".c" in file_path:
                    with open(file_path, 'w') as new_file:
                        new_file.write("// Here a new C file have fun :)\n")
                elif ".rs" in file_path:
                    with open(file_path, 'w') as new_file:
                        new_file.write("// Here a new Rust file have fun :)\n")
                else:
                    with open(file_path, 'w') as new_file:
                        new_file.write("// Here a new file have fun :)\n")

                with open(file_path, 'r') as file:
                    self.editor.setPlainText(file.read())
                self.current_directory_line_edit.setText(file_path)

    #def create_new_project(self):


    def open_file(self):
        if self.current_directory_line_edit.text().strip():
            file_name, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier", os.path.dirname(self.current_directory_line_edit.text()), "C Files (*.c);;All Files (*)")
            if file_name:
                with open(file_name, 'r') as file:
                    self.editor.setPlainText(file.read())
                self.current_directory_line_edit.setText(file_name)
        if self.combo_box.currentText() == "Current File":
            new_compile_cmd = self.create_new_compile_command_with_name(self.compile_line_edit.text(), os.path.basename(file_name))
            self.compile_line_edit.setText(new_compile_cmd)

    def open_project(self, dir_name=None):
        print("dir", dir_name)
        if dir_name is False and self.current_directory_line_edit.text().strip():
            dir_name = QFileDialog.getExistingDirectory(self, "Ouvrir un dossier",
                                                        os.path.dirname(self.current_directory_line_edit.text()))
        if dir_name:
            self.tree_view.setRootIndex(self.file_system_model.index(dir_name))
            print(os.path.dirname(dir_name))
            self.current_directory_line_edit.setText(dir_name)

    def save_file(self):
        file_dir = self.current_directory_line_edit.text()
        if file_dir:
            with open(file_dir, 'w') as file:
                file.write(self.editor.toPlainText())

    def save_as_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le fichier", "", "C Files (*.c);;All Files (*)")
        if file_name:
            with open(file_name, 'w') as file:
                file.write(self.editor.toPlainText())
            self.current_directory_line_edit.setText(os.path.dirname(file_name))


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
