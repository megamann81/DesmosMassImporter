import os
import sys
import time
import glob
import traceback
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WDM = True
except ImportError:
    HAS_WDM = False


def copy_with_retry(text, max_retries=15, delay=0.25):
    """Copy text to Windows clipboard with retry logic for OpenClipboard errors."""
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            pyperclip.copy(text)
            if pyperclip.paste() == text:
                return True
        except Exception as e:
            last_err = e
        time.sleep(delay)
    raise RuntimeError(f"Failed to access Windows clipboard after {max_retries} attempts: {last_err}")


def start_chrome():
    """Start a single Chrome session and navigate to Desmos 3D."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    if HAS_WDM:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        driver = webdriver.Chrome(options=options)

    driver.get("https://www.desmos.com/3d")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".dcg-expressionlist"))
    )
    time.sleep(2.0)
    return driver


def create_desmos_folder(driver, folder_title):
    """Create a new folder in Desmos 3D using the Add Item (+) menu or 'folder' shortcut."""
    wait = WebDriverWait(driver, 15)
    add_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".dcg-add-expression-btn, [aria-label='Add Item']"))
    )
    add_btn.click()
    time.sleep(0.3)

    folder_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".dcg-add-folder, [aria-label='Folder']"))
    )
    folder_btn.click()
    time.sleep(0.3)

    active = driver.switch_to.active_element
    active.send_keys(folder_title)
    active.send_keys(Keys.ENTER)
    time.sleep(0.4)


def paste_expressions_into_graph(driver, expressions):
    """Paste a list of expressions into the currently open Desmos 3D graph."""
    batch_text = "\n".join(expressions)
    copy_with_retry(batch_text)

    active = driver.switch_to.active_element
    ActionChains(driver).key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
    time.sleep(1.5)


def collect_batches(base_dir="models/triangle_folders", chunk_size=500):
    """Read triangle files and group expressions into 500-triangle batches."""
    pattern = os.path.join(base_dir, "Folder_*", "triangles_*.txt")
    files = sorted(glob.glob(pattern))
    if not files:
        files = sorted(glob.glob("**/triangles_*.txt", recursive=True))

    batches = []
    for fpath in files:
        folder_label = os.path.basename(os.path.dirname(fpath))
        with open(fpath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

        if len(lines) <= chunk_size:
            batches.append((folder_label, lines))
        else:
            for idx in range(0, len(lines), chunk_size):
                part = (idx // chunk_size) + 1
                sub_label = f"{folder_label}_Part{part:02d}"
                batches.append((sub_label, lines[idx:idx + chunk_size]))

    return batches


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    batches = collect_batches(chunk_size=500)
    if not batches:
        print("No triangle batch files found under models/triangle_folders/.")
        return

    print(f"Found {len(batches)} batch(es) ready for Desmos 3D.")
    print("Opening Chrome once — all imported batches will reuse this same Desmos 3D graph.")
    driver = start_chrome()

    try:
        for i, (folder_name, triangles) in enumerate(batches, start=1):
            print(f"\n--- Batch {i}/{len(batches)}: {folder_name} ({len(triangles)} triangles) ---")
            while True:
                choice = input("Import this batch? [Y]es / [S]kip / [Q]uit (stop): ").strip().lower()
                if choice in ("", "y", "yes", "c", "continue"):
                    action = "import"
                    break
                elif choice in ("s", "skip"):
                    action = "skip"
                    break
                elif choice in ("q", "quit", "stop", "exit"):
                    action = "stop"
                    break
                else:
                    print("Invalid option. Enter Y (import), S (skip), or Q (stop).")

            if action == "stop":
                print("Stopping import as requested. Chrome will remain open with your current graph.")
                break
            elif action == "skip":
                print(f"Skipped {folder_name}.")
                continue

            print(f"Creating Desmos folder '{folder_name}'...")
            create_desmos_folder(driver, folder_name)

            print(f"Pasting {len(triangles)} triangles into '{folder_name}'...")
            paste_expressions_into_graph(driver, triangles)
            print(f"Done importing {folder_name}.")

    except Exception as e:
        print(f"\nError during import: {e}")
        traceback.print_exc()
    finally:
        print("\nImport session finished. Keeping Chrome open so you can save or inspect your graph.")


if __name__ == "__main__":
    main()
