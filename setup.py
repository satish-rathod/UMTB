import os
import sys
import subprocess
import winreg
import shutil
import time
from pathlib import Path

def clean_existing_environment():
    """Remove existing virtual environment if present."""
    print("Checking for existing virtual environment...")
    venv_path = Path("venv")
    if venv_path.exists():
        print("Found existing virtual environment. Removing it...")
        try:
            shutil.rmtree(venv_path)
            print("Existing virtual environment removed successfully.")
        except Exception as e:
            print(f"Error removing existing virtual environment: {e}")
            print("Please manually delete the 'venv' folder and try again.")
            raise

def create_virtual_environment():
    """Create a fresh virtual environment using subprocess."""
    print("Creating new virtual environment...")
    try:
        # Get the system Python path
        system_python = sys.executable
        print(f"Using system Python: {system_python}")
        
        # Create virtual environment using system Python
        process = subprocess.run(
            [system_python, "-m", "venv", "venv"],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        if process.returncode != 0:
            print("Error output:", process.stderr)
            raise Exception("Virtual environment creation failed")
            
        print("Virtual environment created successfully.")
        return Path("venv")
        
    except subprocess.TimeoutExpired:
        print("Virtual environment creation timed out after 60 seconds.")
        raise
    except Exception as e:
        print(f"Error creating virtual environment: {e}")
        raise

def get_python_executable(venv_path):
    """Get the Python executable path from the virtual environment."""
    print("Locating Python executable...")
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    
    print(f"Looking for Python executable at: {python_path}")
    if not python_path.exists():
        raise FileNotFoundError(f"Python executable not found at {python_path}")
    return python_path

def verify_installation(python_path):
    """Verify that the Python installation is working."""
    print("Verifying Python installation...")
    try:
        result = subprocess.run(
            [str(python_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"Python verification successful: {result.stdout.strip()}")
    except subprocess.TimeoutExpired:
        print("Python verification timed out")
        raise
    except Exception as e:
        print(f"Error verifying Python installation: {e}")
        raise

def install_dependencies(python_path):
    """Install required dependencies using pip."""
    print("\nInstalling dependencies...")
    try:
        print("Upgrading pip...")
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("Installing requirements...")
        process = subprocess.run(
            [str(python_path), "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
            timeout=180
        )
        print("Dependencies installed successfully.")
        
    except subprocess.TimeoutExpired:
        print("Dependency installation timed out")
        raise
    except Exception as e:
        print(f"Error during pip install: {e}")
        raise

def create_startup_script(python_path):
    """Create a batch script to run the program."""
    print("\nCreating startup batch script...")
    batch_content = f"""@echo off
cd /d "%~dp0"
echo Starting Camera Monitor...
"{python_path}" main.py
pause
"""
    try:
        with open("run_camera_monitor.bat", "w") as f:
            f.write(batch_content)
        batch_path = Path("run_camera_monitor.bat").absolute()
        print(f"Created batch script at: {batch_path}")
        return batch_path
    except Exception as e:
        print(f"Error creating batch script: {e}")
        raise

def add_to_startup(batch_path):
    """Add the batch script to Windows startup."""
    print("\nAdding to Windows startup...")
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "CameraMonitor", 0, winreg.REG_SZ, str(batch_path))
        print("Successfully added to startup registry!")
    except Exception as e:
        print(f"Failed to add to startup registry: {e}")
        raise

def main():
    try:
        print("Starting setup process...")
        print("Current working directory:", os.getcwd())
        print("System Python version:", sys.version)
        print("System Python path:", sys.executable)
        
        # Check if running as admin
        try:
            is_admin = os.getuid() == 0
        except AttributeError:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        
        if not is_admin:
            print("Warning: Script is not running with administrator privileges")
        
        # Check if required files exist
        if not Path("requirements.txt").exists():
            raise FileNotFoundError("requirements.txt not found in current directory")
        if not Path("main.py").exists():
            raise FileNotFoundError("main.py not found in current directory")

        # Clean existing environment
        clean_existing_environment()
        
        # Create fresh virtual environment
        venv_path = create_virtual_environment()
        
        # Small delay to ensure file system is updated
        time.sleep(2)
        
        # Get and verify Python executable path
        python_path = get_python_executable(venv_path)
        verify_installation(python_path)
        
        # Install dependencies
        install_dependencies(python_path)
        
        # Create and register startup script
        batch_path = create_startup_script(python_path)
        add_to_startup(batch_path)

        print("\nSetup completed successfully!")
        print("The camera monitor will now start automatically when you log in.")
        print(f"To run it manually, you can use the '{batch_path.name}' script.")

        # Start the program immediately
        print("\nStarting camera monitor...")
        subprocess.Popen([str(batch_path)], creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        print("\nSetup complete! Press Enter to exit...")
        input()

    except Exception as e:
        print(f"\nError during setup: {str(e)}")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

if __name__ == "__main__":
    main()