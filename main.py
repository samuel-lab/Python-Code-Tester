# main.py

import sys
import os
import subprocess
import shutil

def check_python_version():
    if sys.version_info < (3, 7):
        print("Python 3.7 or higher is required.")
        sys.exit(1)

def check_required_files():
    required_files = ['ui.py', 'analysis.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"Required file '{file}' not found.")
            sys.exit(1)

def check_python_packages():
    requirements_file = 'requirements.txt'
    if not os.path.exists(requirements_file):
        print(f"Requirements file '{requirements_file}' not found.")
        sys.exit(1)

    with open(requirements_file, 'r') as f:
        required_packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    missing_packages = []
    for package in required_packages:
        # Extract the package name without version specifiers
        package_name = package.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
        try:
            __import__(package_name)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("The following required Python packages are missing:")
        for pkg in missing_packages:
            print(f"- {pkg}")
        print("\nPlease install them by running:")
        print("    pip install -r requirements.txt")
        sys.exit(1)

def check_command_line_tools():
    required_tools = [
        'pylint', 'mypy', 'radon', 'bandit', 'black', 'pydocstyle',
        'pip-licenses', 'pytest', 'pip-audit', 'autopep8', 'isort',
        'flake8', 'pdoc'
    ]
    missing_tools = []
    for tool in required_tools:
        if shutil.which(tool) is None:
            missing_tools.append(tool)
    if missing_tools:
        print("The following required command-line tools are missing:")
        for tool in missing_tools:
            print(f"- {tool}")
        print("\nPlease install them by running:")
        print(f"    pip install {' '.join(missing_tools)}")
        sys.exit(1)

def check_syntax(file_name):
    try:
        subprocess.check_call([sys.executable, '-m', 'py_compile', file_name])
    except subprocess.CalledProcessError:
        print(f"Syntax errors detected in '{file_name}'. Please fix them and try again.")
        sys.exit(1)

def main():
    check_python_version()
    check_required_files()
    check_python_packages()
    check_command_line_tools()
    check_syntax('ui.py')
    check_syntax('analysis.py')

    # Run the UI application
    import ui
    ui.main()

if __name__ == '__main__':
    main()
