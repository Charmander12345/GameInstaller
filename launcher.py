import os
import customtkinter as ctk
from configparser import ConfigParser
import subprocess
import psutil
from Classes import window_position, ctk_components
import time
from CTkMessagebox import *
from PIL import Image
from hPyT import *
from CTkMenuBar import *
import tkinter as tk
import requests
import zipfile
import io
import shutil

config = ConfigParser()
config.read("config.ini")

app = ctk.CTk()
app.title("Catania Launcher")
app.resizable(False, False)
#maximize_minimize_button.hide(app)
window_position.center_window(app, 650, 400)

game_path:str = ""
game_process = None
is_running = False
installed = False

def checkGamePath():
    game_path = config.get("Game", "catania_path", fallback="")
    if not game_path:
        game_path = os.path.expanduser("~/Catania")
        if not os.path.exists(game_path):
            return False
        else:
            if not "Game" in config.sections():
                config.add_section("Game")
            config.set("Game", "catania_path", game_path)
            config.set("Game", "installed", "True")
            with open("config.ini", "w") as configfile:
                config.write(configfile)
        return True
    else:
        return os.path.exists(game_path)

def launch_game():
    global game_process
    global is_running
    if checkGamePath():
        game_path = config.get("Game", "catania_path")
        game_executable = os.path.join(game_path, "Catania.exe")
        if os.path.exists(game_executable):
            game_process = subprocess.Popen(game_executable)
            is_running = True
            update_button_text()
            time.sleep(1)  # Wait for the game to start
            app.iconify()  # Minimize the launcher window
        else:
            CTkMessagebox(master=app, title="Game not found", message= "Couldn't locate the executable.", option_1="OK", icon="warning")
    else:
        if os.path.exists(os.path.expanduser("~/Catania")):
            game_executable = os.path.join(game_path, "Catania.exe")
            if os.path.exists(game_executable):
                game_process = subprocess.Popen(game_executable)
                is_running = True
                update_button_text()
                time.sleep(1)  # Wait for the game to start
                app.iconify()  # Minimize the launcher window
            else:
                CTkMessagebox(master=app, title="Game not found", message= "Couldn't locate the executable.", option_1="OK", icon="warning")
        else:
            CTkMessagebox(master=app, title="Catania not installed", message= "Game path not found. Please install Catania first.", option_1="OK", icon="warning")

def close_game():
    global game_process
    global is_running
    if game_process:
        print("Trying to close game process with PID:", game_process.pid)
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['pid'] == game_process.pid or "Catania.exe" in (proc.info['exe'] or ""):
                    print("Terminating process:", proc.info)
                    proc.terminate()  # Versuche, den Prozess zu beenden
                    try:
                        proc.wait(timeout=5)  # Warte, bis der Prozess beendet ist
                    except psutil.TimeoutExpired:
                        print("Process did not terminate in time, forcing kill...")
                        proc.kill()  # Erzwinge die Beendigung
                    # Beende mögliche Kindprozesse
                    for child in proc.children(recursive=True):
                        child.terminate()
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                print("Error with process:", e)
        game_process = None
        is_running = False
        update_button_text()

def update_button_text():
    global game_process
    global is_running
    if is_running:
        if game_process and game_process.poll() is None:  # Process is running
            launch_button.configure(text="Close Game", command=close_game)
        else:
            app.deiconify()  # Restore the launcher window
            app.lift()  # Bring the launcher window to the front
            app.focus_force()  # Focus the launcher window
            launch_button.configure(text="Launch Catania", command=launch_game)
            game_process = None
            is_running = False
        app.after(1000, update_button_text)  # Check every second
    else:
        launch_button.configure(text="Launch Catania", command=launch_game)

def update_buttons():
    global installed
    installed = checkGamePath()
    if installed:
        launch_button.configure(state="normal")
    else:
        launch_button.configure(state="disabled")

def copy_path():
    app.clipboard_clear()
    app.clipboard_append(game_path_var.get())
    app.update()  # Keeps the clipboard content after the app is closed
    CTkMessagebox(master=app, title="Path Copied", message="Game path copied to clipboard.", option_1="OK", icon="info")

def show_patch_notes(Version: str = "0.5"):
    patch_notes_frame.pack(pady=10, padx=10, fill="both", expand=True)
    VersionTitle.configure(text=f"Patch Notes {Version}")
    print(f"Showing patch notes for version {Version}")

    # Entferne vorhandene Widgets in VersionInfo
    for widget in VersionInfo.winfo_children():
        widget.destroy()

    # Lade die Patch Notes aus der Datei
    try:
        with open(f"VersionInfo/{Version}.txt", "r") as file:
            for line in file:
                ctk.CTkLabel(
                    VersionInfo,
                    text=line.strip(),  # Entferne überflüssige Leerzeichen/Zeilenumbrüche
                    wraplength=500,     # Text wird bei 500 Pixeln umgebrochen
                    anchor="w",         # Linksbündige Ausrichtung
                    justify="left"      # Linksbündige Textausrichtung
                ).pack(pady=2, padx=5, side="top")
    except FileNotFoundError:
        ctk.CTkLabel(
            VersionInfo,
            text="Patch notes file not found.",
            wraplength=600,
            anchor="w",
            justify="left"
        ).pack(pady=2, padx=5, side="top")


def download_and_extract_github_repo(zip_url, extract_to):
    # ZIP-Datei herunterladen
    print("Lade ZIP-Datei herunter...")
    response = requests.get(zip_url)
    if response.status_code == 200:
        print("Download erfolgreich!")
        with io.BytesIO(response.content) as zip_file:
            # ZIP-Datei öffnen
            with zipfile.ZipFile(zip_file) as zf:
                # Überprüfen, welche Dateien im Ordner "VersionInfo" liegen
                files_to_extract = [
                    file for file in zf.namelist() if file.startswith("GameInstaller-main/VersionInfo/")
                ]
                # Dateien extrahieren
                print(f"Extrahiere {len(files_to_extract)} Dateien...")
                zf.extractall(extract_to, members=files_to_extract)

        # Dateien ins Zielverzeichnis verschieben
        extracted_dir = os.path.join(extract_to, "GameInstaller-main", "VersionInfo")
        for root, _, files in os.walk(extracted_dir):
            for file in files:
                source = os.path.join(root, file)
                relative_path = os.path.relpath(root, extracted_dir)
                destination = os.path.join(extract_to, relative_path, file)
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                shutil.move(source, destination)

        # Ursprünglichen Ordner löschen
        print("Bereinige temporäre Dateien...")
        shutil.rmtree(os.path.join(extract_to, "GameInstaller-main"))
        print(f"Fertig! Dateien wurden in '{extract_to}' entpackt.")
    else:
        print(f"Fehler beim Herunterladen: {response.status_code}")

def UpdatePND():
    if os.path.exists("VersionInfo"):
        PNDropdown = CustomDropdownMenu(widget=PNButton)
        VersionInfofile = os.listdir("VersionInfo")
        for Version in VersionInfofile:
            Versionedit = Version.replace(".txt","")
            PNDropdown.add_option(option=Versionedit,command=lambda Versionedit=Versionedit: show_patch_notes(Version=Versionedit))
            PNDropdown.add_separator()

# Widgets
menu = CTkMenuBar(app,bg_color="#2b2b2b",pady=5,padx=5,cursor="hand2")
PNButton = menu.add_cascade("Patch Notes")
SettingsButton = menu.add_cascade("Settings")
AboutButton = menu.add_cascade("About")
ExitButton = menu.add_cascade("Exit",command=app.quit)

# Patch Notes
patch_notes_frame = ctk.CTkFrame(app)
back_button = ctk.CTkButton(patch_notes_frame, text="Back", command=lambda: patch_notes_frame.pack_forget())
back_button.pack(pady=5, padx=5, side="bottom")
VersionTitle = ctk.CTkLabel(patch_notes_frame, text=f"Patch Notes", font=("Arial", 20))
VersionTitle.pack(pady=5, padx=5, side="top")
VersionInfo = ctk.CTkScrollableFrame(patch_notes_frame)
VersionInfo.pack(pady=5, padx=10, fill="both", expand=True)

# Patch Notes Dropdown
if os.path.exists("VersionInfo"):
    PNDropdown = CustomDropdownMenu(widget=PNButton)
    VersionInfofile = os.listdir("VersionInfo")
    for Version in VersionInfofile:
        Versionedit = Version.replace(".txt","")
        PNDropdown.add_option(option=Versionedit,command=lambda Versionedit=Versionedit: show_patch_notes(Version=Versionedit))
        PNDropdown.add_separator()
else:
    os.makedirs("VersionInfo")
    repo_url = "https://github.com/Charmander12345/GameInstaller/archive/refs/heads/main.zip"
    extract_to = "VersionInfo"
    download_and_extract_github_repo(repo_url, extract_to)
    UpdatePND()

# Settings Dropdown
SettingsDropdown = CustomDropdownMenu(widget=SettingsButton)
SettingsDropdown.add_option(option="Game Settings")
SettingsDropdown.add_separator()
SettingsDropdown.add_option(option="Launcher Settings")
SettingsDropdown.add_separator()
SettingsDropdown.add_option(option="Check game path")

launchframe = ctk.CTkFrame(app)
launchframe.pack(pady=10, padx=10, fill="x", side="bottom")
base_dir = os.path.dirname(os.path.abspath(__file__))
dots_icon_path = os.path.join(base_dir, "icons/Dots/Light.png")
dots = ctk.CTkImage(Image.open(dots_icon_path))
GameOptions = ctk.CTkButton(launchframe, image=dots, text="",width=20, height=30, fg_color="darkgray", hover_color="gray")
GameOptions.pack(pady=10, padx=5, side="right")
launch_button = ctk.CTkButton(launchframe, text="Launch Catania", command=launch_game)
launch_button.pack(pady=10, padx=5, side="right")

# Dots Dropdown
dots_dropdown = CustomDropdownMenu(widget=GameOptions)
dots_dropdown.add_option(option="Launch Game",command=launch_game)
dots_dropdown.add_separator()
dots_dropdown.add_option(option="Close Game",command=close_game)
dots_dropdown.add_separator()
dots_dropdown.add_option(option="Uninstall Catania")
dots_dropdown.add_separator()
dots_dropdown.add_option(option="Update")

# Game path entry
if checkGamePath():
    game_path = os.path.abspath(config.get("Game", "catania_path", fallback=""))
else:
    game_path = ""
game_path_var = tk.StringVar(value=game_path)
direntry = ctk.CTkEntry(launchframe, textvariable=game_path_var,state="readonly")
direntry.pack(pady=10, padx=5, side="left",fill="x", expand=True)

# Load the icon image
base_dir = os.path.dirname(os.path.abspath(__file__))
copy_icon_path = os.path.join(base_dir, "icons/copy/Light.png")
copy_icon = ctk.CTkImage(Image.open(copy_icon_path))

copy_button = ctk.CTkButton(
    launchframe, 
    image=copy_icon, 
    text="", 
    command=copy_path, 
    width=30, 
    height=30, 
    fg_color="darkgray", 
    hover_color="gray"
)
copy_button.pack(pady=10, padx=5, side="right")
app.after(1, update_buttons)
app.mainloop()
