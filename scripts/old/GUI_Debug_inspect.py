# filename: GUI_Debug_inspect.py
import os
from pathlib import Path

def print_header(title):
    print(f"\n=== {title} ===")

def main():
    base_dir = Path(__file__).resolve().parent.parent

    print_header("Inspecting Streamlit Project Structure")
    print(f"Base directory: {base_dir}")

    # Check for app.py
    app_file = base_dir / "app.py"
    if app_file.exists():
        print("✅ Found app.py")
    else:
        print("❌ Missing app.py (must be at root of project)")

    # Check for pages/ directory
    pages_dir = base_dir / "pages"
    if not pages_dir.exists() or not pages_dir.is_dir():
        print("❌ Missing pages/ directory")
        return
    else:
        print("✅ Found pages/ directory")

    # List page scripts
    print_header("Pages Found")
    page_files = sorted(p for p in pages_dir.glob("*.py"))
    if not page_files:
        print("❌ No .py files in pages/")
    else:
        for f in page_files:
            print(f"📄 {f.name}")

    # Check for misplacements
    print_header("Common Issues Check")
    misplaced_app = pages_dir / "app.py"
    if misplaced_app.exists():
        print("❌ app.py is incorrectly inside pages/. Move it to root.")
    else:
        print("✅ app.py is correctly located")

    non_py_files = [f for f in pages_dir.iterdir() if not f.name.endswith(".py")]
    if non_py_files:
        print("⚠️ Non-Python files in pages/:")
        for f in non_py_files:
            print(f"   - {f.name}")
    else:
        print("✅ All files in pages/ are Python scripts")

    print_header("Final Tip")
    print("Run your app like this:\n\n  streamlit run app.py\n")

if __name__ == "__main__":
    main()