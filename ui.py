# ui.py

import sys
import json
import os
import shutil
import subprocess

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import squarify  # For treemap visualization

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QTextEdit, QLabel, QTabWidget, QMessageBox, QComboBox, QHBoxLayout,
    QProgressBar, QMenuBar, QAction, QDialog, QFormLayout, QSpinBox, QCheckBox, QListWidget,
    QListWidgetItem, QSplitter, QLineEdit, QInputDialog, QScrollArea, QGroupBox
)

from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet

# Import AnalysisThread and app_logger from analysis.py
from analysis import AnalysisThread, app_logger

# ----------------------- Settings Dialog -----------------------

class SettingsDialog(QDialog):
    def __init__(self, parent=None, available_tools=None, selected_tools=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(500, 600)
        self.available_tools = available_tools or []
        self.selected_tools = selected_tools or []
        self.initUI()

    def initUI(self):
        layout = QFormLayout()

        # Tool Selection
        self.tool_list = QListWidget()
        self.tool_list.setSelectionMode(QListWidget.MultiSelection)
        for tool in self.available_tools:
            item = QListWidgetItem(tool)
            item.setSelected(tool in self.selected_tools)
            self.tool_list.addItem(item)
        layout.addRow("Select Analysis Tools:", self.tool_list)

        # PyLint fail-under score
        self.pylint_fail_under = QSpinBox()
        self.pylint_fail_under.setRange(0, 10)  # PyLint scores range from 0 to 10
        self.pylint_fail_under.setValue(self.parent().settings.get("pylint_fail_under", 5))
        layout.addRow("PyLint Fail Under (0-10):", self.pylint_fail_under)

        # Radon complexity threshold
        self.radon_threshold = QSpinBox()
        self.radon_threshold.setRange(0, 100)
        self.radon_threshold.setValue(self.parent().settings.get("radon_threshold", 10))
        layout.addRow("Radon Complexity Threshold:", self.radon_threshold)

        # Bandit confidence level
        self.bandit_confidence = QComboBox()
        self.bandit_confidence.addItems(["LOW", "MEDIUM", "HIGH"])
        self.bandit_confidence.setCurrentText(self.parent().settings.get("bandit_confidence", "MEDIUM"))
        layout.addRow("Bandit Confidence Level:", self.bandit_confidence)

        # Report Format
        self.report_format = QComboBox()
        self.report_format.addItems(["PDF", "HTML", "Markdown"])
        self.report_format.setCurrentText(self.parent().settings.get("report_format", "PDF"))
        layout.addRow("Report Format:", self.report_format)
        
        # Metrics Tracking Checkbox
        self.enable_metrics_tracking = QCheckBox("Enable Metrics Tracking")
        self.enable_metrics_tracking.setChecked(self.parent().settings.get("enable_metrics_tracking", True))
        layout.addRow(self.enable_metrics_tracking)

        # Git Integration
        self.enable_git_integration = QCheckBox("Enable Git Integration")
        self.enable_git_integration.setChecked(self.parent().settings.get("enable_git_integration", False))
        layout.addRow(self.enable_git_integration)

        # Auto-fix options
        self.enable_autofix = QCheckBox("Enable Auto-fixing (Experimental)")
        self.enable_autofix.setChecked(self.parent().settings.get("enable_autofix", False))
        layout.addRow(self.enable_autofix)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addRow(button_layout)

        self.setLayout(layout)

    def save_settings(self):
        selected_items = self.tool_list.selectedItems()
        selected_tools = [item.text() for item in selected_items]
        settings = {
            "selected_tools": selected_tools,
            "pylint_fail_under": self.pylint_fail_under.value(),
            "radon_threshold": self.radon_threshold.value(),
            "bandit_confidence": self.bandit_confidence.currentText(),
            "report_format": self.report_format.currentText(),
            "enable_git_integration": self.enable_git_integration.isChecked(),
            "enable_autofix": self.enable_autofix.isChecked(),
            "enable_metrics_tracking": self.enable_metrics_tracking.isChecked(),  # Save the new setting
        }
        # Save settings to a JSON file
        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
            app_logger.info("Settings saved.")
            QMessageBox.information(self, "Settings", "Settings have been saved successfully.")
            self.accept()
        except Exception as e:
            app_logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")

# ----------------------- About Dialog -----------------------

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setFixedSize(500, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        about_text = QLabel("""
        <h2>Python Project Tester</h2>
        <p>Version 3.1</p>
        <p>Developed by Samuel Labant</p>
        <p>This application provides a comprehensive analysis of Python projects, including linting, type checking, code complexity, security scanning, testing, coverage, dependency audits, formatting checks, documentation style, license compliance, performance profiling, and more. Now with enhanced features like code duplication detection, metrics over time visualization, and automatic documentation generation.</p>
        """)
        about_text.setWordWrap(True)
        about_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(about_text)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

# ----------------------- Main Application -----------------------

class AnalyzerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Project Tester")
        self.setMinimumSize(1200, 700)
        self.project_path = ""
        self.analysis_results = {}
        self.tester_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of the tester
        self.analysis_thread = None
        self.available_tools = [
            'Pylint', 'Flake8', 'Mypy', 'Radon', 'Bandit', 'Black', 'Autopep8', 'Isort', 'Pydocstyle',
            'Pip-Licenses', 'Pytest', 'Coverage', 'Pip-Audit', 'Code Duplication', 'Profiling', 'Documentation Generation'
        ]
        self.settings = self.load_settings()  # Load settings in AnalyzerApp

        # Initialize metric attributes
        self.lint_issues = 0
        self.security_issues = 0
        self.formatting_issues = 0
        self.documentation_issues = 0
        self.duplication_issues = 0
        self.coverage = 0
        self.vulnerabilities = 0
        self.no_vulnerabilities = 0  # Initialize to 0
        self.license_compliant = 0
        self.license_non_compliant = 0
        self.total_dependencies = 0  # Initialize to 0
        self.complexity_data = {}

        self.initUI()

    def load_settings(self):
        if os.path.exists('settings.json'):
            try:
                with open('settings.json', 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                app_logger.error("Failed to parse settings.json. Using default settings.")
        # Default settings
        return {
            "selected_tools": self.available_tools,
            "pylint_fail_under": 5,
            "radon_threshold": 10,
            "bandit_confidence": "MEDIUM",
            "report_format": "PDF",
            "enable_git_integration": False,
            "enable_autofix": False,
            "enable_metrics_tracking": True,
        }

    def initUI(self):
        self.setWindowTitle("Python Project Tester")
        self.setMinimumSize(1200, 700)
        main_layout = QVBoxLayout()

        # Menu Bar
        menu_bar = QMenuBar(self)

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings Menu
        settings_menu = menu_bar.addMenu("&Settings")
        settings_action = QAction("&Configure Analysis Tools", self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.open_about)
        help_menu.addAction(about_action)

        main_layout.setMenuBar(menu_bar)

        # Top Buttons
        top_layout = QHBoxLayout()

        self.select_btn = QPushButton("Select Project")
        self.select_btn.setIcon(QIcon.fromTheme("folder"))
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.select_btn.clicked.connect(self.select_project)
        self.select_btn.setToolTip("Click to select the project directory for analysis.")
        top_layout.addWidget(self.select_btn)

        self.git_clone_btn = QPushButton("Clone from Git")
        self.git_clone_btn.setIcon(QIcon.fromTheme("git"))
        self.git_clone_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a3791;
            }
        """)
        self.git_clone_btn.clicked.connect(self.clone_from_git)
        self.git_clone_btn.setToolTip("Click to clone a repository from GitHub or GitLab.")
        self.git_clone_btn.setEnabled(self.settings.get("enable_git_integration", False))
        top_layout.addWidget(self.git_clone_btn)

        self.cancel_btn = QPushButton("Cancel Analysis")
        self.cancel_btn.setIcon(QIcon.fromTheme("process-stop"))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_analysis)
        self.cancel_btn.setToolTip("Click to cancel the ongoing analysis.")
        self.cancel_btn.setEnabled(False)
        top_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(top_layout)

        # Splitter for Tabs and Recommendations
        splitter = QSplitter(Qt.Vertical)

        # Tabs for analysis results
        self.tabs = QTabWidget()
        self.lint_tab = QWidget()
        self.typecheck_tab = QWidget()
        self.complexity_tab = QWidget()
        self.security_tab = QWidget()
        self.formatting_tab = QWidget()
        self.documentation_tab = QWidget()
        self.license_tab = QWidget()
        self.profiling_tab = QWidget()
        self.test_tab = QWidget()
        self.coverage_tab = QWidget()
        self.dependency_tab = QWidget()
        self.code_duplication_tab = QWidget()

        self.tabs.addTab(self.lint_tab, "Linting")
        self.tabs.addTab(self.typecheck_tab, "Type Checking")
        self.tabs.addTab(self.complexity_tab, "Complexity")
        self.tabs.addTab(self.security_tab, "Security")
        self.tabs.addTab(self.formatting_tab, "Formatting")
        self.tabs.addTab(self.documentation_tab, "Documentation")
        self.tabs.addTab(self.license_tab, "Licenses")
        self.tabs.addTab(self.profiling_tab, "Profiling")
        self.tabs.addTab(self.test_tab, "Testing")
        self.tabs.addTab(self.coverage_tab, "Coverage")
        self.tabs.addTab(self.dependency_tab, "Dependencies")
        self.tabs.addTab(self.code_duplication_tab, "Code Duplication")

        self.init_tabs()
        splitter.addWidget(self.tabs)

        # Recommendations Panel
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setStyleSheet("""
            QTextEdit {
                background-color: #2e3440;
                color: #a3be8c;
                font-family: Courier New;
                font-size: 12px;
            }
        """)
        self.recommendations_text.setMinimumHeight(150)
        splitter.addWidget(self.recommendations_text)

        # Set initial sizes for splitter widgets
        splitter.setSizes([300, 150])
        main_layout.addWidget(splitter, stretch=1)

        # Visualization Panel
        visualization_group = QGroupBox("Analysis Summary")
        visualization_layout = QVBoxLayout(visualization_group)

        # Scroll Area for Visualization
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Container widget for graphs
        self.graph_container = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_container)
        self.graph_layout.setSpacing(30)  # Increased spacing between graphs
        self.graph_layout.setContentsMargins(20, 20, 20, 20)

        self.scroll_area.setWidget(self.graph_container)
        visualization_layout.addWidget(self.scroll_area)

        main_layout.addWidget(visualization_group, stretch=2)

        # Export Report Button
        export_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export Report")
        self.export_btn.setIcon(QIcon.fromTheme("document-save"))
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
        """)
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setToolTip("Click to export the analysis results.")
        self.export_btn.setEnabled(False)
        export_layout.addWidget(self.export_btn)
        export_layout.addStretch()
        main_layout.addLayout(export_layout)

        # Progress Bar and Status Label
        progress_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 12))
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 20px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        main_layout.addLayout(progress_layout)

        # Apply a dark palette to the application
        self.apply_dark_palette()

        self.setLayout(main_layout)

    def init_tabs(self):
        # Define a mapping from tab names to attribute names
        tab_name_to_attr = {
            'Linting': 'lint_text',
            'Type Checking': 'typecheck_text',
            'Complexity': 'complexity_text',
            'Security': 'security_text',
            'Formatting': 'formatting_text',
            'Documentation': 'documentation_text',
            'Licenses': 'license_text',
            'Profiling': 'profiling_text',
            'Testing': 'test_text',
            'Coverage': 'coverage_text',
            'Dependencies': 'dependency_text',
            'Code Duplication': 'code_duplication_text'
        }

        for name, tab in [
            ('Linting', self.lint_tab),
            ('Type Checking', self.typecheck_tab),
            ('Complexity', self.complexity_tab),
            ('Security', self.security_tab),
            ('Formatting', self.formatting_tab),
            ('Documentation', self.documentation_tab),
            ('Licenses', self.license_tab),
            ('Profiling', self.profiling_tab),
            ('Testing', self.test_tab),
            ('Coverage', self.coverage_tab),
            ('Dependencies', self.dependency_tab),
            ('Code Duplication', self.code_duplication_tab)
        ]:
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #2e3440;
                    color: #d8dee9;
                    font-family: Courier New;
                    font-size: 12px;
                }
            """)
            tab.setLayout(QVBoxLayout())
            tab.layout().addWidget(text_edit)
            setattr(self, tab_name_to_attr[name], text_edit)  # Correct attribute naming

    def apply_dark_palette(self):
        dark_palette = QPalette()

        # Set dark background
        dark_palette.setColor(QPalette.Window, QColor(46, 52, 64))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(37, 42, 54))
        dark_palette.setColor(QPalette.AlternateBase, QColor(46, 52, 64))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(46, 52, 64))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(52, 152, 219))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)

        QApplication.instance().setPalette(dark_palette)
        QApplication.instance().setStyle("Fusion")

    def open_settings(self):
        settings_dialog = SettingsDialog(
            self,
            available_tools=self.available_tools,
            selected_tools=self.settings.get('selected_tools', self.available_tools)
        )
        settings_dialog.exec_()
        # Reload settings after closing the dialog in case they were changed
        self.settings = self.load_settings()
        # Update git clone button
        self.git_clone_btn.setEnabled(self.settings.get("enable_git_integration", False))

    def open_about(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def select_project(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Project Directory", "", options=options
        )
        if dir_path:
            self.project_path = dir_path
            app_logger.info(f"Project selected: {self.project_path}")
            self.run_analysis()

    def clone_from_git(self):
        repo_url, ok = QInputDialog.getText(self, 'Clone Repository', 'Enter Git Repository URL:')
        if ok and repo_url:
            self.status_label.setText("Cloning repository...")
            app_logger.info(f"Cloning repository from {repo_url}")
            self.project_path = os.path.join(self.tester_dir, 'cloned_repo')
            if os.path.exists(self.project_path):
                shutil.rmtree(self.project_path)
            git_cmd = ['git', 'clone', repo_url, self.project_path]
            try:
                subprocess.check_call(git_cmd)
                app_logger.info("Repository cloned successfully.")
                self.run_analysis()
            except subprocess.CalledProcessError as e:
                QMessageBox.critical(self, "Clone Failed", f"Failed to clone repository:\n{e}")
                app_logger.error(f"Failed to clone repository: {e}")

    def run_analysis(self):
        if not self.project_path:
            QMessageBox.warning(self, "No Project Selected", "Please select a project directory.")
            app_logger.warning("Run analysis attempted without selecting a project.")
            return

        # Reset previous results
        self.analysis_results = {}
        self.clear_tabs()
        self.export_btn.setEnabled(False)
        self.status_label.setText("Starting analysis...")
        self.progress_bar.setValue(0)
        self.cancel_btn.setEnabled(True)
        self.select_btn.setEnabled(False)
        self.git_clone_btn.setEnabled(False)

        # Get selected tools
        selected_tools = self.settings.get('selected_tools', self.available_tools)

        # Map selected tools to steps
        tools_to_steps = {
            'Pylint': ['linting'],
            'Flake8': ['linting'],
            'Mypy': ['type checking'],
            'Radon': ['complexity'],
            'Bandit': ['security'],
            'Black': ['formatting'],
            'Autopep8': ['formatting'],
            'Isort': ['formatting'],
            'Pydocstyle': ['documentation'],
            'Pytest': ['testing'],
            'Coverage': ['coverage'],
            'Pip-Licenses': ['license'],
            'Pip-Audit': ['dependency audit'],
            'Code Duplication': ['code duplication'],
            'Profiling': ['profiling'],
            'Documentation Generation': ['documentation generation']
        }

        self.steps = set()
        for tool in selected_tools:
            steps = tools_to_steps.get(tool, [])
            self.steps.update(steps)

        self.total_steps = len(self.steps)

        if self.total_steps == 0:
            QMessageBox.warning(self, "No Tools Selected", "Please select at least one analysis tool in the settings.")
            app_logger.warning("Run analysis attempted with no tools selected.")
            self.select_btn.setEnabled(True)
            self.git_clone_btn.setEnabled(self.settings.get("enable_git_integration", False))
            return

        self.completed_steps = 0

        # Initialize and start the analysis thread
        self.analysis_thread = AnalysisThread(self.project_path, self.tester_dir, self.settings)
        self.analysis_thread.lint_completed.connect(self.process_lint_output)
        self.analysis_thread.typecheck_completed.connect(self.process_typecheck_output)
        self.analysis_thread.complexity_completed.connect(self.process_complexity_output)
        self.analysis_thread.security_completed.connect(self.process_security_output)
        self.analysis_thread.formatting_completed.connect(self.process_formatting_output)
        self.analysis_thread.documentation_completed.connect(self.process_documentation_output)
        self.analysis_thread.license_completed.connect(self.process_license_output)
        self.analysis_thread.profiling_completed.connect(self.process_profiling_output)
        self.analysis_thread.test_completed.connect(self.process_test_output)
        self.analysis_thread.coverage_completed.connect(self.process_coverage_output)
        self.analysis_thread.dependency_audit_completed.connect(self.process_dependency_output)
        self.analysis_thread.code_duplication_completed.connect(self.process_code_duplication_output)
        self.analysis_thread.documentation_generated.connect(self.process_documentation_generation_output)
        self.analysis_thread.recommendations.connect(self.process_recommendations)
        self.analysis_thread.progress.connect(self.update_progress)
        self.analysis_thread.finished.connect(self.analysis_finished)
        self.analysis_thread.start()

    def cancel_analysis(self):
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.stop()
            self.status_label.setText("Analysis canceled.")
            self.progress_bar.setValue(0)
            self.cancel_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.select_btn.setEnabled(True)
            self.git_clone_btn.setEnabled(self.settings.get("enable_git_integration", False))
            app_logger.info("Analysis canceled by user.")

    def clear_tabs(self):
        for attr in [
            'lint_text',
            'typecheck_text',
            'complexity_text',
            'security_text',
            'formatting_text',
            'documentation_text',
            'license_text',
            'profiling_text',
            'test_text',
            'coverage_text',
            'dependency_text',
            'code_duplication_text'
        ]:
            text_edit = getattr(self, attr, None)
            if text_edit:
                text_edit.clear()
        self.recommendations_text.clear()

    def update_progress(self, message):
        self.status_label.setText(message)
        app_logger.info(message)
        # Do not increment progress bar here; it's handled in step_completed

    def step_completed(self, step_name):
        if step_name in self.steps:
            self.completed_steps += 1
            percentage = (self.completed_steps / self.total_steps) * 100
            self.progress_bar.setValue(int(percentage))
            self.status_label.setText(f"Completed {self.completed_steps} of {self.total_steps} steps.")

    def process_lint_output(self, output):
        self.analysis_results['Linting'] = output
        formatted = self.format_pylint_output(output)
        self.lint_text.setText(formatted if formatted else "No linting issues found.")
        self.update_visualization()
        self.step_completed('linting')

    def format_pylint_output(self, output):
        try:
            issues = json.loads(output)
            self.lint_issues = len(issues)
            if not issues:
                return ""
            formatted = ""
            for issue in issues:
                formatted += f"{issue['type'].upper()} - {issue['message']} (Line {issue['line']}) in {issue['path']}\n"
            return formatted
        except json.JSONDecodeError:
            return output  # Return raw output if JSON parsing fails

    def process_typecheck_output(self, output):
        self.analysis_results['Type Checking'] = output
        self.typecheck_text.setText(output if output else "No type checking issues found.")
        self.update_visualization()
        self.step_completed('type checking')

    def process_complexity_output(self, output):
        self.analysis_results['Complexity'] = output
        try:
            complexities = json.loads(output)
            self.complexity_data = complexities  # Store for visualization
            formatted = ""
            for module, metrics in complexities.items():
                for block in metrics:
                    # Filter based on the complexity threshold
                    if block['complexity'] > self.settings.get('radon_threshold', 10):
                        formatted += f"{block['name']} - CC: {block['complexity']} (Line {block['lineno']})\n"
            self.complexity_text.setText(formatted if formatted else "No complexity issues found.")
        except json.JSONDecodeError:
            self.complexity_text.setText(output)
        self.update_visualization()
        self.step_completed('complexity')

    def process_security_output(self, output):
        self.analysis_results['Security'] = output
        try:
            data = json.loads(output)
            issues = data.get('results', [])
            self.security_issues = len(issues)
            if issues:
                formatted = ""
                for issue in issues:
                    severity = issue.get('issue_severity', 'Unknown').capitalize()
                    confidence = issue.get('issue_confidence', 'Unknown').capitalize()
                    issue_text = issue.get('issue_text', 'No description provided.')
                    file_name = issue.get('filename', 'Unknown File')
                    line_number = issue.get('line_number', 'Unknown Line')
                    code = issue.get('code', '')
                    formatted += f"Severity: {severity}\n"
                    formatted += f"Confidence: {confidence}\n"
                    formatted += f"Issue: {issue_text}\n"
                    formatted += f"File: {file_name}:{line_number}\n"
                    formatted += f"Code:\n{code}\n"
                    formatted += "-" * 50 + "\n"
                self.security_text.setText(formatted)
            else:
                self.security_text.setText("No security issues found.")
        except json.JSONDecodeError:
            self.security_text.setText(output)
        self.update_visualization()
        self.step_completed('security')

    def process_formatting_output(self, output):
        self.analysis_results['Formatting'] = output
        if "would reformat" in output:
            # Count the number of "would reformat" lines
            self.formatting_issues = output.count("would reformat")
            self.formatting_text.setText(f"{self.formatting_issues} files would be reformatted.\n\n{output}")
        elif "All done! ✨ 🍰 ✨" in output:
            self.formatting_text.setText("All files are properly formatted.")
            self.formatting_issues = 0
        else:
            self.formatting_text.setText(output)
        self.update_visualization()
        self.step_completed('formatting')

    def process_documentation_output(self, output):
        self.analysis_results['Documentation'] = output
        if output.strip() == '':
            self.documentation_issues = 0
            self.documentation_text.setText("No documentation style issues found.")
        else:
            lines = output.strip().split('\n')
            self.documentation_issues = len([line for line in lines if line.strip() != ""])
            self.documentation_text.setText(output)
        self.update_visualization()
        self.step_completed('documentation')

    def process_license_output(self, output):
        self.analysis_results['Licenses'] = output
        try:
            licenses = json.loads(output)
            self.license_compliant = 0
            self.license_non_compliant = 0
            self.total_dependencies = len(licenses)  # Set total dependencies
            if not licenses:
                self.license_text.setText("No dependencies found.")
                return
            formatted = ""
            for package in licenses:
                name = package.get('Name', 'Unknown')
                version = package.get('Version', 'Unknown')
                license_type = package.get('License', 'Unknown')
                formatted += f"Package: {name}\n"
                formatted += f"Version: {version}\n"
                formatted += f"License: {license_type}\n"
                formatted += "-" * 50 + "\n"
                if license_type in ['MIT', 'BSD', 'Apache 2.0', 'GPLv3']:
                    self.license_compliant += 1
                else:
                    self.license_non_compliant += 1
            self.license_text.setText(formatted)
        except json.JSONDecodeError:
            self.license_text.setText(output)
        self.update_visualization()
        self.step_completed('license')

    def process_profiling_output(self, output):
        self.analysis_results['Profiling'] = output
        self.profiling_text.setText(output if output else "Profiling completed.")
        self.update_visualization()
        self.step_completed('profiling')

    def process_test_output(self, output):
        self.analysis_results['Testing'] = output
        self.test_text.setText(output if output else "No test results found.")
        self.update_visualization()
        self.step_completed('testing')

    def process_coverage_output(self, output):
        self.analysis_results['Coverage'] = output
        try:
            coverage_data = json.loads(output)
            total_coverage = coverage_data.get('meta', {}).get('coverage_percent', 0)
            if total_coverage is None or np.isnan(total_coverage):
                total_coverage = 0
            self.coverage = total_coverage  # Assign to self.coverage
            formatted = f"Total Coverage: {total_coverage}%\n\n"
            formatted += "Coverage by File:\n"
            files = coverage_data.get('files', {})
            for file_path, data in files.items():
                summary = data.get('summary', {})
                file_coverage = summary.get('percent_covered', 0)
                formatted += f"{file_path}: {file_coverage}%\n"
            self.coverage_text.setText(formatted)
        except json.JSONDecodeError:
            self.coverage_text.setText("Failed to parse coverage report.")
            app_logger.error("Failed to parse coverage report.")
        self.update_visualization()
        self.step_completed('coverage')

    def process_dependency_output(self, output):
        self.analysis_results['Dependencies'] = output
        try:
            vulnerabilities = json.loads(output)
            self.vulnerabilities = len(vulnerabilities)
            # Ensure total_dependencies is greater than or equal to vulnerabilities
            if self.total_dependencies == 0:
                self.total_dependencies = self.vulnerabilities
            self.no_vulnerabilities = max(0, self.total_dependencies - self.vulnerabilities)
            if vulnerabilities:
                formatted = ""
                for vuln in vulnerabilities:
                    dependency = vuln.get('dependency', {})
                    package_name = dependency.get('name', 'Unknown Package')
                    version = dependency.get('version', 'Unknown Version')
                    id = vuln.get('id', 'No ID')
                    description = vuln.get('description', 'No description provided.')
                    formatted += f"Package: {package_name}\n"
                    formatted += f"Version: {version}\n"
                    formatted += f"Vulnerability ID: {id}\n"
                    formatted += f"Description: {description}\n"
                    formatted += "-" * 50 + "\n"
                self.dependency_text.setText(formatted)
            else:
                self.dependency_text.setText("No dependency vulnerabilities found.")
        except json.JSONDecodeError:
            self.dependency_text.setText("Failed to parse dependency vulnerabilities.")
        self.update_visualization()
        self.step_completed('dependency audit')

    def process_code_duplication_output(self, output):
        self.analysis_results['Code Duplication'] = output
        if output.strip() == '':
            self.duplication_issues = 0
            self.code_duplication_text.setText("No code duplication issues found.")
        else:
            lines = output.strip().split('\n')
            self.duplication_issues = len(lines)
            self.code_duplication_text.setText(output)
        self.update_visualization()
        self.step_completed('code duplication')

    def process_documentation_generation_output(self, output):
        self.analysis_results['Documentation Generation'] = output
        QMessageBox.information(self, "Documentation Generated", output)
        self.step_completed('documentation generation')

    def process_recommendations(self, recommendations):
        self.recommendations_text.setText(recommendations)

    def update_visualization(self):
        # Clear the current layout
        while self.graph_layout.count():
            item = self.graph_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        # Use a dark background style
        plt.style.use('dark_background')

        # Data preparation

        # Common figure properties
        figure_kwargs = {
            'figsize': (8, 4),
            'constrained_layout': True  # Use constrained layout to prevent text from being cut off
        }

        self.figures = []  # List to store figures for report generation

        # Graph 1: Issue Distribution
        fig1 = plt.Figure(**figure_kwargs)
        canvas1 = FigureCanvas(fig1)
        canvas1.setMinimumHeight(300)
        ax1 = fig1.subplots()
        # Set facecolor
        fig1.patch.set_facecolor('#2e3440')
        ax1.set_facecolor('#2e3440')
        ax1.title.set_color('white')
        ax1.tick_params(colors='white')
        for spine in ax1.spines.values():
            spine.set_color('white')

        # Plotting code for ax1
        categories = ['Linting', 'Security', 'Formatting', 'Documentation', 'Duplication']
        values = [self.lint_issues, self.security_issues, self.formatting_issues, self.documentation_issues, self.duplication_issues]
        colors = ['#FF8C00', '#DC143C', '#4CAF50', '#FFD700', '#9b59b6']
        bars = ax1.bar(categories, values, color=colors)
        ax1.set_title("Issue Distribution", fontsize=14, color='white')
        ax1.set_ylabel("Number of Issues", fontsize=12, color='white')
        ax1.tick_params(axis='x', rotation=45, colors='white')
        ax1.tick_params(axis='y', colors='white')
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, color='white')
        # Add canvas to layout
        self.graph_layout.addWidget(canvas1)
        self.figures.append(fig1)

        # Graph 2: License Compliance
        fig2 = plt.Figure(**figure_kwargs)
        canvas2 = FigureCanvas(fig2)
        canvas2.setMinimumHeight(300)
        ax2 = fig2.subplots()
        # Set facecolor
        fig2.patch.set_facecolor('#2e3440')
        ax2.set_facecolor('#2e3440')
        ax2.title.set_color('white')
        # Plotting code for ax2
        labels = ['Compliant', 'Non-Compliant']
        sizes = [self.license_compliant, self.license_non_compliant]
        if sum(sizes) == 0:
            sizes = [1, 0]
        colors_pie = ['#2ecc71', '#e74c3c']
        explode = (0.05, 0)
        wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors_pie, explode=explode,
                autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10, 'color': 'white'})
        ax2.axis('equal')
        ax2.set_title("License Compliance", fontsize=14, color='white')
        # Adjust text to prevent overlap
        for text in texts + autotexts:
            text.set_color('white')
        # Add canvas to layout
        self.graph_layout.addWidget(canvas2)
        self.figures.append(fig2)

        # Graph 3: Vulnerability Status
        fig3 = plt.Figure(**figure_kwargs)
        canvas3 = FigureCanvas(fig3)
        canvas3.setMinimumHeight(300)
        ax3 = fig3.subplots()
        # Set facecolor
        fig3.patch.set_facecolor('#2e3440')
        ax3.set_facecolor('#2e3440')
        ax3.title.set_color('white')
        # Plotting code for ax3
        labels_vuln = ['Vulnerabilities', 'No Vulnerabilities']
        sizes_vuln = [self.vulnerabilities, self.no_vulnerabilities]
        if sum(sizes_vuln) == 0:
            sizes_vuln = [0, 1]  # Default values to prevent division by zero
        colors_pie_vuln = ['#e74c3c', '#2ecc71']
        explode_vuln = (0.05, 0)
        wedges, texts, autotexts = ax3.pie(sizes_vuln, labels=labels_vuln, colors=colors_pie_vuln, explode=explode_vuln,
                autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10, 'color': 'white'})
        ax3.axis('equal')
        ax3.set_title("Vulnerability Status", fontsize=14, color='white')
        # Adjust text to prevent overlap
        for text in texts + autotexts:
            text.set_color('white')
        # Add canvas to layout
        self.graph_layout.addWidget(canvas3)
        self.figures.append(fig3)

        # Graph 4: Code Coverage
        fig4 = plt.Figure(**figure_kwargs)
        canvas4 = FigureCanvas(fig4)
        canvas4.setMinimumHeight(300)
        ax4 = fig4.subplots()
        # Set facecolor
        fig4.patch.set_facecolor('#2e3440')
        ax4.set_facecolor('#2e3440')
        ax4.title.set_color('white')
        # Plotting code for ax4
        labels_coverage = ['Covered', 'Uncovered']
        coverage_value = self.coverage  # Use self.coverage
        sizes_coverage = [coverage_value, max(0, 100 - coverage_value)]
        if sum(sizes_coverage) == 0:
            sizes_coverage = [0, 1]  # Default values to prevent division by zero
        colors_pie_coverage = ['#3498db', '#95a5a6']
        explode_coverage = (0.05, 0)
        wedges, texts, autotexts = ax4.pie(sizes_coverage, labels=labels_coverage, colors=colors_pie_coverage, explode=explode_coverage,
                autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10, 'color': 'white'})
        ax4.axis('equal')
        ax4.set_title("Code Coverage", fontsize=14, color='white')
        # Adjust text to prevent overlap
        for text in texts + autotexts:
            text.set_color('white')
        # Add canvas to layout
        self.graph_layout.addWidget(canvas4)
        self.figures.append(fig4)

        # Spacer at the end
        self.graph_layout.addStretch()

        if self.complexity_data and squarify:
            fig5 = plt.Figure(**figure_kwargs)
            canvas5 = FigureCanvas(fig5)
            canvas5.setMinimumHeight(300)
            ax5 = fig5.subplots()
            fig5.patch.set_facecolor('#2e3440')
            ax5.set_facecolor('#2e3440')
            ax5.title.set_color('white')
            ax5.axis('off')

            # Prepare data
            labels = []
            sizes = []
            colors = []
            max_complexity = 0
            for module, metrics in self.complexity_data.items():
                module_complexity = sum(block['complexity'] for block in metrics)
                labels.append(module)
                sizes.append(module_complexity)
                max_complexity = max(max_complexity, module_complexity)

            if sizes:
                # Normalize colors based on complexity
                norm = plt.Normalize(vmin=0, vmax=max_complexity)
                colors = [plt.cm.Reds(norm(value)) for value in sizes]

                # Plot treemap
                squarify.plot(sizes=sizes, label=labels, color=colors, ax=ax5)
                ax5.set_title("Code Complexity Treemap", fontsize=14, color='white')

                # Add canvas to layout
                self.graph_layout.addWidget(canvas5)
                self.figures.append(fig5)

        # Load metrics over time
        metrics_file = os.path.join(self.tester_dir, 'metrics.json')
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
            dates = [datetime.fromisoformat(entry['date']) for entry in metrics_data]
            lint_issues = [entry['lint_issues'] for entry in metrics_data]
            security_issues = [entry['security_issues'] for entry in metrics_data]
            formatting_issues = [entry['formatting_issues'] for entry in metrics_data]
            coverage = [entry['code_coverage'] for entry in metrics_data]

            # Graph 6: Metrics Over Time
            fig6 = plt.Figure(**figure_kwargs)
            canvas6 = FigureCanvas(fig6)
            canvas6.setMinimumHeight(300)
            ax6 = fig6.subplots()
            fig6.patch.set_facecolor('#2e3440')
            ax6.set_facecolor('#2e3440')
            ax6.title.set_color('white')
            ax6.tick_params(colors='white')
            for spine in ax6.spines.values():
                spine.set_color('white')

            ax6.plot(dates, lint_issues, label='Lint Issues', marker='o')
            ax6.plot(dates, security_issues, label='Security Issues', marker='o')
            ax6.plot(dates, formatting_issues, label='Formatting Issues', marker='o')
            ax6.set_xlabel('Date', color='white')
            ax6.set_ylabel('Number of Issues', color='white')
            ax6.legend()
            ax6.set_title("Metrics Over Time", fontsize=14, color='white')
            ax6.tick_params(axis='x', rotation=45, colors='white')
            ax6.tick_params(axis='y', colors='white')

            self.graph_layout.addWidget(canvas6)
            self.figures.append(fig6)

            # Graph 7: Code Coverage Over Time
            fig7 = plt.Figure(**figure_kwargs)
            canvas7 = FigureCanvas(fig7)
            canvas7.setMinimumHeight(300)
            ax7 = fig7.subplots()
            fig7.patch.set_facecolor('#2e3440')
            ax7.set_facecolor('#2e3440')
            ax7.title.set_color('white')
            ax7.tick_params(colors='white')
            for spine in ax7.spines.values():
                spine.set_color('white')

            ax7.plot(dates, coverage, label='Code Coverage', marker='o', color='#3498db')
            ax7.set_xlabel('Date', color='white')
            ax7.set_ylabel('Coverage (%)', color='white')
            ax7.set_title("Code Coverage Over Time", fontsize=14, color='white')
            ax7.tick_params(axis='x', rotation=45, colors='white')
            ax7.tick_params(axis='y', colors='white')
            ax7.legend()

            self.graph_layout.addWidget(canvas7)
            self.figures.append(fig7)

        # Spacer at the end
        self.graph_layout.addStretch()

    def export_report(self):
        if not self.analysis_results:
            QMessageBox.warning(self, "No Data", "No analysis data to export.")
            app_logger.warning("Export report attempted without analysis data.")
            return

        options = QFileDialog.Options()
        report_format = self.settings.get('report_format', 'PDF').lower()
        file_filter = f"{report_format.upper()} Files (*.{report_format})"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "", file_filter, options=options
        )
        if file_path:
            try:
                self.generate_report(file_path)
                QMessageBox.information(self, "Report Exported", f"Report saved as {file_path}.")
                app_logger.info(f"Report exported to {file_path}.")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"An error occurred while exporting the report:\n{e}")
                app_logger.error(f"Failed to export report: {e}")

    def generate_report(self, file_path):
        import io
        from reportlab.lib.utils import ImageReader

        report_format = self.settings.get('report_format', 'PDF').upper()
        if report_format != 'PDF':
            QMessageBox.warning(self, "Unsupported Format", f"Report format '{report_format}' is not supported yet.")
            app_logger.warning(f"Report format '{report_format}' is not supported yet.")
            return

        doc = SimpleDocTemplate(file_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph("Python Project Analysis Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Project Info
        project_info = Paragraph(f"<b>Project Path:</b> {self.project_path}", styles['Normal'])
        date_info = Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(project_info)
        elements.append(date_info)
        elements.append(Spacer(1, 12))

        # Executive Summary
        elements.append(Paragraph("<b>Executive Summary</b>", styles['Heading2']))
        summary_text = f"""
        This report provides a comprehensive analysis of the Python project located at {self.project_path}. 
        The analysis includes linting, type checking, code complexity assessment, security vulnerability scanning, 
        formatting checks, documentation style verification, license compliance, dependency audits, performance profiling, 
        testing, and code coverage.
        """
        elements.append(Paragraph(summary_text, styles['BodyText']))
        elements.append(Spacer(1, 12))

        # Recommendations
        elements.append(Paragraph("<b>Recommendations</b>", styles['Heading2']))
        recommendations = self.recommendations_text.toPlainText().replace('\n', '<br/>')
        elements.append(Paragraph(recommendations, styles['BodyText']))
        elements.append(Spacer(1, 12))

        # Analysis Sections
        for section, content in self.analysis_results.items():
            if section in ['Profiling', 'Licenses', 'Coverage', 'Dependencies', 'Documentation Generation']:
                continue  # These will be handled separately
            elements.append(Paragraph(f"<b>{section}</b>", styles['Heading3']))
            formatted_content = content.replace('\n', '<br/>')
            elements.append(Paragraph(formatted_content, styles['BodyText']))
            elements.append(Spacer(1, 12))

        # Embedded Visualization Charts
        if hasattr(self, 'figures'):
            elements.append(Paragraph("<b>Analysis Summary Visualizations</b>", styles['Heading2']))
            elements.append(Spacer(1, 12))
            for idx, fig in enumerate(self.figures):
                try:
                    img_buffer = io.BytesIO()
                    fig.savefig(img_buffer, format='png')
                    img_buffer.seek(0)
                    img = RLImage(ImageReader(img_buffer), width=500, height=400)
                    elements.append(img)
                    elements.append(Spacer(1, 12))
                    img_buffer.close()
                except Exception as e:
                    app_logger.error(f"Failed to include figure {idx} in the report: {e}")
                    elements.append(Paragraph(f"Failed to include figure {idx} in the report.", styles['BodyText']))
                    elements.append(Spacer(1, 12))

        # Profiling Section
        elements.append(Paragraph("<b>Performance Profiling</b>", styles['Heading3']))
        profiling_content = self.analysis_results.get('Profiling', 'No profiling data available.')
        elements.append(Paragraph(profiling_content.replace('\n', '<br/>'), styles['BodyText']))
        elements.append(Spacer(1, 12))

        # Licenses Section
        elements.append(Paragraph("<b>License Compliance</b>", styles['Heading3']))
        licenses_content = self.analysis_results.get('Licenses', 'No license data available.')
        elements.append(Paragraph(licenses_content.replace('\n', '<br/>'), styles['BodyText']))
        elements.append(Spacer(1, 12))

        # Dependency Vulnerabilities Section
        elements.append(Paragraph("<b>Dependency Vulnerabilities</b>", styles['Heading3']))
        dependencies_content = self.analysis_results.get('Dependencies', 'No dependency vulnerabilities found.')
        elements.append(Paragraph(dependencies_content.replace('\n', '<br/>'), styles['BodyText']))
        elements.append(Spacer(1, 12))

        # Coverage Section
        elements.append(Paragraph("<b>Code Coverage</b>", styles['Heading3']))
        coverage_content = self.analysis_results.get('Coverage', 'No coverage data available.')
        elements.append(Paragraph(coverage_content.replace('\n', '<br/>'), styles['BodyText']))
        elements.append(Spacer(1, 12))

        # Documentation Generation Section
        elements.append(Paragraph("<b>Documentation Generation</b>", styles['Heading3']))
        doc_gen_content = self.analysis_results.get('Documentation Generation', 'Documentation generation skipped.')
        elements.append(Paragraph(doc_gen_content.replace('\n', '<br/>'), styles['BodyText']))
        elements.append(Spacer(1, 12))

        # Build the PDF
        try:
            doc.build(elements)
            app_logger.info(f"Report successfully generated at {file_path}")
        except Exception as e:
            app_logger.error(f"Failed to generate the report: {e}")
            QMessageBox.critical(self, "Export Failed", f"An error occurred while generating the report:\n{e}")

    def analysis_finished(self):
        self.progress_bar.setValue(100)
        self.export_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.select_btn.setEnabled(True)
        self.git_clone_btn.setEnabled(self.settings.get("enable_git_integration", False))
        self.status_label.setText("Analysis completed.")
        app_logger.info("Analysis finished and export button enabled.")
        self.save_metrics()

    def save_metrics(self):
        if not self.settings.get("enable_metrics_tracking", True):
            app_logger.info("Metrics tracking is disabled. Skipping saving metrics.")
            return  # Do not save metrics if tracking is disabled

        metrics_file = os.path.join(self.tester_dir, 'metrics.json')
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
        else:
            metrics_data = []

        current_metrics = {
            'date': datetime.now().isoformat(),
            'lint_issues': self.lint_issues,
            'security_issues': self.security_issues,
            'formatting_issues': self.formatting_issues,
            'documentation_issues': self.documentation_issues,
            'duplication_issues': self.duplication_issues,
            'code_coverage': self.coverage,
            'vulnerabilities': self.vulnerabilities
        }

        metrics_data.append(current_metrics)

        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=4)

# ----------------------- Main Function -----------------------

def main():
    app = QApplication(sys.argv)
    window = AnalyzerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
