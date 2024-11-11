# analysis.py

import subprocess
import json
import os
import shutil
import logging
from logging.handlers import RotatingFileHandler
from PyQt5.QtCore import QThread, pyqtSignal

# ----------------------- Logging Setup -----------------------

# Create a rotating file handler
log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
log_file = 'app.log'
my_handler = RotatingFileHandler(log_file, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.INFO)

# Get the root logger
app_logger = logging.getLogger()
app_logger.setLevel(logging.INFO)
app_logger.addHandler(my_handler)

# ----------------------- Analysis Thread -----------------------

class AnalysisThread(QThread):
    # Define signals for each analysis step
    lint_completed = pyqtSignal(str)
    typecheck_completed = pyqtSignal(str)
    complexity_completed = pyqtSignal(str)
    security_completed = pyqtSignal(str)
    formatting_completed = pyqtSignal(str)
    documentation_completed = pyqtSignal(str)
    license_completed = pyqtSignal(str)
    profiling_completed = pyqtSignal(str)
    test_completed = pyqtSignal(str)
    coverage_completed = pyqtSignal(str)
    dependency_audit_completed = pyqtSignal(str)
    code_duplication_completed = pyqtSignal(str)
    documentation_generated = pyqtSignal(str)
    recommendations = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, project_path, tester_dir, settings):
        super().__init__()
        self.project_path = project_path
        self.tester_dir = tester_dir
        self.is_running = True
        self.settings = settings
        self.selected_tools = settings.get('selected_tools', [])
        self.enable_autofix = settings.get('enable_autofix', False)
        self.recommendations_list = []

    def is_tool_available(self, tool_name):
        return shutil.which(tool_name) is not None

    def run(self):
        app_logger.info("Analysis thread started.")
        try:
            # Run selected tools
            if 'Pylint' in self.selected_tools and self.is_running:
                self.run_pylint()
            else:
                self.lint_completed.emit("Pylint analysis skipped.")

            if 'Mypy' in self.selected_tools and self.is_running:
                self.run_mypy()
            else:
                self.typecheck_completed.emit("Mypy analysis skipped.")

            if 'Radon' in self.selected_tools and self.is_running:
                self.run_radon()
            else:
                self.complexity_completed.emit("Radon analysis skipped.")

            if 'Bandit' in self.selected_tools and self.is_running:
                self.run_bandit()
            else:
                self.security_completed.emit("Bandit analysis skipped.")

            if 'Black' in self.selected_tools and self.is_running:
                self.run_black()
            else:
                self.formatting_completed.emit("Black formatting check skipped.")

            if 'Pydocstyle' in self.selected_tools and self.is_running:
                self.run_pydocstyle()
            else:
                self.documentation_completed.emit("Pydocstyle analysis skipped.")

            if 'Pip-Licenses' in self.selected_tools and self.is_running:
                self.run_pip_licenses()
            else:
                self.license_completed.emit("License compliance check skipped.")

            if 'Pytest' in self.selected_tools and self.is_running:
                self.run_pytest()
            else:
                self.test_completed.emit("Testing skipped.")
                self.coverage_completed.emit("Coverage analysis skipped.")

            if 'Pip-Audit' in self.selected_tools and self.is_running:
                self.run_pip_audit()
            else:
                self.dependency_audit_completed.emit("Dependency audit skipped.")

            if self.enable_autofix and self.is_running:
                if 'Autopep8' in self.selected_tools:
                    self.run_autopep8()
                if 'Isort' in self.selected_tools:
                    self.run_isort()

            if 'Flake8' in self.selected_tools and self.is_running:
                self.run_flake8_duplication()
            else:
                self.code_duplication_completed.emit("Flake8 code duplication analysis skipped.")

            if 'Documentation Generation' in self.selected_tools and self.is_running:
                self.generate_documentation()
            else:
                self.documentation_generated.emit("Documentation generation skipped.")

            # Emit recommendations
            self.recommendations.emit('\n'.join(self.recommendations_list))

            self.progress.emit("Analysis completed.")
            app_logger.info("Analysis thread completed.")

        except Exception as e:
            app_logger.exception("An unexpected error occurred in analysis thread.")
            self.progress.emit(f"Error: {e}")

    # ----------------------- Analysis Methods -----------------------

    def run_pylint(self):
        if not self.is_running:
            return
        if not self.is_tool_available('pylint'):
            self.progress.emit("Error: pylint is not available. Please install it.")
            self.lint_completed.emit("pylint is not available.")
            app_logger.error("pylint is not available.")
        else:
            self.progress.emit("Starting linting...")
            app_logger.info("Running pylint...")
            pylint_cmd = [
                'pylint', self.project_path, '--output-format=json'
            ]
            self.progress.emit("Running pylint...")
            lint_output = self.run_command(pylint_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.lint_completed.emit(lint_output)
            self.generate_pylint_recommendations(lint_output)

    def generate_pylint_recommendations(self, output):
        try:
            issues = json.loads(output)
            if not issues:
                self.recommendations_list.append("Pylint: No issues found. Great job!")
                return
            error_types = set(issue['type'] for issue in issues)
            for error_type in error_types:
                self.recommendations_list.append(f"Pylint: Address {error_type} issues for better code quality.")
        except json.JSONDecodeError:
            app_logger.warning("Failed to parse pylint output as JSON.")

    def run_mypy(self):
        if not self.is_running:
            return
        if not self.is_tool_available('mypy'):
            self.progress.emit("Error: mypy is not available. Please install it.")
            self.typecheck_completed.emit("mypy is not available.")
            app_logger.error("mypy is not available.")
        else:
            self.progress.emit("Starting type checking with mypy...")
            app_logger.info("Running mypy...")
            mypy_cmd = [
                'mypy', self.project_path, '--pretty'
            ]
            if self.settings.get("mypy_ignore_missing_imports", True):
                mypy_cmd.append('--ignore-missing-imports')
            self.progress.emit("Running mypy...")
            typecheck_output = self.run_command(mypy_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.typecheck_completed.emit(typecheck_output)
            self.generate_mypy_recommendations(typecheck_output)

    def generate_mypy_recommendations(self, output):
        if "Success: no issues found in" in output:
            self.recommendations_list.append("Mypy: No type issues found. Excellent!")
        else:
            self.recommendations_list.append("Mypy: Consider adding type annotations to improve code reliability.")

    def run_radon(self):
        if not self.is_running:
            return
        if not self.is_tool_available('radon'):
            self.progress.emit("Error: radon is not available. Please install it.")
            self.complexity_completed.emit("radon is not available.")
            app_logger.error("radon is not available.")
        else:
            self.progress.emit("Analyzing code complexity with radon...")
            app_logger.info("Running radon...")
            radon_cmd = [
                'radon', 'cc', '.', '-s', '-j'
            ]
            self.progress.emit("Running radon...")
            complexity_output = self.run_command(radon_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.complexity_completed.emit(complexity_output)
            self.generate_radon_recommendations(complexity_output)

    def generate_radon_recommendations(self, output):
        try:
            complexities = json.loads(output)
            high_complexity = False
            for module, metrics in complexities.items():
                for block in metrics:
                    if block['complexity'] > self.settings.get('radon_threshold', 10):
                        high_complexity = True
                        break
            if high_complexity:
                self.recommendations_list.append("Radon: Simplify complex functions to reduce cognitive load.")
            else:
                self.recommendations_list.append("Radon: Code complexity is within acceptable limits.")
        except json.JSONDecodeError:
            app_logger.warning("Failed to parse radon output as JSON.")

    def run_bandit(self):
        if not self.is_running:
            return
        if not self.is_tool_available('bandit'):
            self.progress.emit("Error: bandit is not available. Please install it.")
            self.security_completed.emit("bandit is not available.")
            app_logger.error("bandit is not available.")
        else:
            self.progress.emit("Starting security analysis with bandit...")
            app_logger.info("Running bandit...")
            bandit_cmd = [
                'bandit', '-r', '.', '-f', 'json'
            ]
            confidence_level = self.settings.get("bandit_confidence", "MEDIUM").lower()
            bandit_cmd.extend(['--confidence-level', confidence_level])
            self.progress.emit("Running bandit...")
            security_output = self.run_command(bandit_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.security_completed.emit(security_output)
            self.generate_bandit_recommendations(security_output)

    def generate_bandit_recommendations(self, output):
        try:
            data = json.loads(output)
            issues = data.get('results', [])
            if issues:
                self.recommendations_list.append("Bandit: Address the identified security issues to secure your code.")
            else:
                self.recommendations_list.append("Bandit: No security issues found. Good job!")
        except json.JSONDecodeError:
            app_logger.warning("Failed to parse bandit output as JSON.")

    def run_black(self):
        if not self.is_running:
            return
        if not self.is_tool_available('black'):
            self.progress.emit("Error: black is not available. Please install it.")
            self.formatting_completed.emit("black is not available.")
            app_logger.error("black is not available.")
        else:
            self.progress.emit("Checking code formatting with black...")
            app_logger.info("Running black...")
            black_cmd = [
                'black', '--check', '.'
            ]
            self.progress.emit("Running black...")
            formatting_output = self.run_command(black_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.formatting_completed.emit(formatting_output)
            self.generate_black_recommendations(formatting_output)

            if self.enable_autofix and self.is_running:
                self.progress.emit("Auto-formatting code with black...")
                black_fix_cmd = [
                    'black', '.'
                ]
                self.run_command(black_fix_cmd, cwd=self.project_path)
                self.recommendations_list.append("Black: Code formatted automatically.")

    def generate_black_recommendations(self, output):
        if "would reformat" in output or "1 file would be reformatted" in output:
            self.recommendations_list.append("Black: Consider formatting your code for better readability.")
        else:
            self.recommendations_list.append("Black: Code is properly formatted.")

    def run_pydocstyle(self):
        if not self.is_running:
            return
        if not self.is_tool_available('pydocstyle'):
            self.progress.emit("Error: pydocstyle is not available. Please install it.")
            self.documentation_completed.emit("pydocstyle is not available.")
            app_logger.error("pydocstyle is not available.")
        else:
            self.progress.emit("Checking documentation style with pydocstyle...")
            app_logger.info("Running pydocstyle...")
            pydocstyle_cmd = [
                'pydocstyle', '.'
            ]
            self.progress.emit("Running pydocstyle...")
            documentation_output = self.run_command(pydocstyle_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.documentation_completed.emit(documentation_output)
            self.generate_pydocstyle_recommendations(documentation_output)

    def generate_pydocstyle_recommendations(self, output):
        if output.strip() == '':
            self.recommendations_list.append("Pydocstyle: Documentation complies with style guidelines.")
        else:
            self.recommendations_list.append("Pydocstyle: Improve docstrings to enhance code maintainability.")

    def run_pip_licenses(self):
        if not self.is_running:
            return
        if not self.is_tool_available('pip-licenses'):
            self.progress.emit("Error: pip-licenses is not available. Please install it.")
            self.license_completed.emit("pip-licenses is not available.")
            app_logger.error("pip-licenses is not available.")
        else:
            self.progress.emit("Checking license compliance with pip-licenses...")
            app_logger.info("Running pip-licenses...")
            pip_licenses_cmd = [
                'pip-licenses', '--format=json'
            ]
            self.progress.emit("Running pip-licenses...")
            license_output = self.run_command(pip_licenses_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.license_completed.emit(license_output)
            self.generate_pip_licenses_recommendations(license_output)

    def generate_pip_licenses_recommendations(self, output):
        try:
            licenses = json.loads(output)
            non_compliant = []
            for package in licenses:
                if package['License'] not in ['MIT', 'BSD', 'Apache 2.0', 'GPLv3', 'LGPL', 'MPL']:
                    non_compliant.append(package['Name'])
            if non_compliant:
                self.recommendations_list.append(f"Pip-Licenses: Review licenses of {', '.join(non_compliant)} for compliance.")
            else:
                self.recommendations_list.append("Pip-Licenses: All dependencies have compliant licenses.")
        except json.JSONDecodeError:
            app_logger.warning("Failed to parse pip-licenses output as JSON.")

    def run_pytest(self):
        if not self.is_running:
            return
        if not self.is_tool_available('pytest'):
            self.progress.emit("Error: pytest is not available. Please install it.")
            self.test_completed.emit("pytest is not available.")
            self.coverage_completed.emit("Coverage analysis skipped.")
            app_logger.error("pytest is not available.")
        else:
            self.progress.emit("Running tests with pytest and coverage...")
            app_logger.info("Running pytest with coverage...")
            coverage_report_path = os.path.join(self.tester_dir, 'coverage.json')
            pytest_cmd = [
                'pytest', '--cov=.', '--cov-report=term-missing', f'--cov-report=json:{coverage_report_path}'
            ]
            self.progress.emit("Running pytest...")
            test_output = self.run_command(pytest_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.test_completed.emit(test_output)
            self.generate_pytest_recommendations(test_output)

            # Process coverage report
            self.progress.emit("Processing coverage report...")
            app_logger.info("Processing coverage report...")
            if os.path.exists(coverage_report_path):
                try:
                    with open(coverage_report_path, 'r') as f:
                        coverage_data = json.load(f)
                    self.coverage_completed.emit(json.dumps(coverage_data, indent=4))
                    self.generate_coverage_recommendations(coverage_data)
                except json.JSONDecodeError:
                    self.coverage_completed.emit("Failed to parse coverage report.")
                    app_logger.error("Failed to parse coverage report.")
                finally:
                    os.remove(coverage_report_path)
            else:
                self.coverage_completed.emit("Coverage report not found.")
                app_logger.error("Coverage report not found.")

    def generate_pytest_recommendations(self, output):
        if "no tests ran" in output.lower():
            self.recommendations_list.append("Pytest: No tests found. Consider adding tests to improve code reliability.")
        else:
            self.recommendations_list.append("Pytest: Tests executed. Review test results for failures.")

    def generate_coverage_recommendations(self, coverage_data):
        total_coverage = coverage_data.get('meta', {}).get('coverage_percent', 0)
        if total_coverage < 80:
            self.recommendations_list.append(f"Coverage: Code coverage is {total_coverage:.2f}%. Aim for at least 80%.")
        else:
            self.recommendations_list.append(f"Coverage: Good job! Code coverage is {total_coverage:.2f}%.")

    def run_pip_audit(self):
        if not self.is_running:
            return
        if not self.is_tool_available('pip-audit'):
            self.progress.emit("Error: pip-audit is not available. Please install it.")
            self.dependency_audit_completed.emit("pip-audit is not available.")
            app_logger.error("pip-audit is not available.")
        else:
            self.progress.emit("Auditing dependencies for vulnerabilities with pip-audit...")
            app_logger.info("Running pip-audit...")
            pip_audit_cmd = ['pip-audit', '--format', 'json']
            self.progress.emit("Running pip-audit...")
            dependency_output = self.run_command(pip_audit_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.dependency_audit_completed.emit(dependency_output)
            self.generate_pip_audit_recommendations(dependency_output)

    def generate_pip_audit_recommendations(self, output):
        try:
            vulnerabilities = json.loads(output)
            if vulnerabilities:
                self.recommendations_list.append("Pip-Audit: Update dependencies to address vulnerabilities.")
            else:
                self.recommendations_list.append("Pip-Audit: No vulnerabilities found in dependencies.")
        except json.JSONDecodeError:
            app_logger.warning("Failed to parse pip-audit output as JSON.")

    def run_autopep8(self):
        if not self.is_running:
            return
        if not self.is_tool_available('autopep8'):
            self.progress.emit("Error: autopep8 is not available. Please install it.")
            app_logger.error("autopep8 is not available.")
        else:
            self.progress.emit("Auto-fixing code with autopep8...")
            app_logger.info("Running autopep8...")
            autopep8_cmd = [
                'autopep8', '--in-place', '--recursive', '.'
            ]
            self.run_command(autopep8_cmd, cwd=self.project_path)
            self.recommendations_list.append("Autopep8: Code auto-formatted to comply with PEP 8.")

    def run_isort(self):
        if not self.is_running:
            return
        if not self.is_tool_available('isort'):
            self.progress.emit("Error: isort is not available. Please install it.")
            app_logger.error("isort is not available.")
        else:
            self.progress.emit("Sorting imports with isort...")
            app_logger.info("Running isort...")
            isort_cmd = [
                'isort', '.'
            ]
            self.run_command(isort_cmd, cwd=self.project_path)
            self.recommendations_list.append("Isort: Imports sorted according to style guidelines.")

    def run_flake8_duplication(self):
        if not self.is_running:
            return
        if not self.is_tool_available('flake8'):
            self.progress.emit("Error: flake8 is not available. Please install it.")
            self.code_duplication_completed.emit("Flake8 is not available.")
            app_logger.error("flake8 is not available.")
        else:
            self.progress.emit("Analyzing code duplication with flake8...")
            app_logger.info("Running flake8 with duplication plugin...")
            flake8_cmd = [
                'flake8', '--select=DUO', '--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s', '.'
            ]
            self.progress.emit("Running flake8...")
            duplication_output = self.run_command(flake8_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            self.code_duplication_completed.emit(duplication_output)
            self.generate_flake8_duplication_recommendations(duplication_output)

    def generate_flake8_duplication_recommendations(self, output):
        if output.strip() == '':
            self.recommendations_list.append("Flake8: No code duplication issues found.")
        else:
            self.recommendations_list.append("Flake8: Consider refactoring duplicated code to improve maintainability.")

    def generate_documentation(self):
        if not self.is_running:
            return
        if not self.is_tool_available('pdoc'):
            self.progress.emit("Error: pdoc is not available. Please install it.")
            self.documentation_generated.emit("pdoc is not available.")
            app_logger.error("pdoc is not available.")
        else:
            self.progress.emit("Generating documentation with pdoc...")
            app_logger.info("Running pdoc...")
            output_dir = os.path.join(self.project_path, 'docs')
            pdoc_cmd = [
                'pdoc', '--html', self.project_path, '--output-dir', output_dir, '--force'
            ]
            self.progress.emit("Running pdoc...")
            documentation_output = self.run_command(pdoc_cmd, cwd=self.project_path)
            if not self.is_running:
                return
            if "Error" in documentation_output:
                self.documentation_generated.emit("Documentation generation failed.")
                self.recommendations_list.append("Documentation: Failed to generate documentation.")
                app_logger.error("pdoc encountered an error during documentation generation.")
            else:
                self.documentation_generated.emit(f"Documentation generated at {output_dir}")
                self.recommendations_list.append("Documentation: Project documentation generated using pdoc.")

    # ----------------------- Utility Methods -----------------------

    def run_command(self, command, cwd=None):
        if not self.is_running:
            return ""
        try:
            result = subprocess.run(
                command, cwd=cwd, capture_output=True, text=True, check=True, timeout=300
            )
            app_logger.info(f"Command {' '.join(command)} executed successfully.")
            return result.stdout
        except subprocess.TimeoutExpired:
            error_message = f"Command {' '.join(command)} timed out."
            app_logger.error(error_message)
            self.progress.emit(error_message)
            return ""
        except FileNotFoundError:
            error_message = f"Command not found: {' '.join(command)}. Please ensure it is installed and in your PATH."
            app_logger.error(error_message)
            self.progress.emit(error_message)
            return ""
        except subprocess.CalledProcessError as e:
            stdout_output = e.stdout.strip() if e.stdout else ''
            stderr_output = e.stderr.strip() if e.stderr else ''
            error_message = f"Error running {' '.join(command)}: {stderr_output}"
            app_logger.error(error_message)
            self.progress.emit(error_message)
            # Return both stdout and stderr
            return stdout_output + "\n" + stderr_output
        except Exception as e:
            error_message = f"An error occurred while running {' '.join(command)}: {e}"
            app_logger.exception(error_message)
            self.progress.emit(error_message)
            return ""

    def stop(self):
        self.is_running = False
        app_logger.info("Analysis thread termination requested by user.")
        self.wait(1000)  # Wait for a short while to let the thread stop gracefully.
        if self.isRunning():
            app_logger.warning("Analysis thread did not stop gracefully. Terminating.")
            self.terminate()
            self.wait()
