import os
import customtkinter as ctk
from customtkinter import CTk
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
from tkinter import messagebox
import requests
import zipfile
import io
import shutil
from tkinter import filedialog
from os.path import exists
import threading

# Define paths for configuration and version info
appdata_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'CataniaLauncher')
config_path = os.path.join(appdata_dir, 'config.ini')
versioninfo_dir = os.path.join(appdata_dir, 'VersionInfo')

# Ensure the directories exist
os.makedirs(appdata_dir, exist_ok=True)
os.makedirs(versioninfo_dir, exist_ok=True)

config = ConfigParser()
config.read(config_path)

app = ctk.CTk()
app.title("Catania Launcher")
app.resizable(False, False)
#maximize_minimize_button.hide(app)
window_position.center_window(app, 1000, 600)

#Microsoft Onedrive
Tenant_ID = "e26f77c3-1dee-42ba-ae48-7ba44efd4dea"
Client_ID = "188446fc-2aa3-4557-bf5e-595461d1533d"

game_path:str = ""
game_process = None
is_running = False
installed = False
repo_url = "https://github.com/Charmander12345/GameInstaller/archive/refs/heads/main.zip"
extract_to = "VersionInfo"

progress_var = ctk.DoubleVar()
game_path_var = tk.StringVar(value=game_path)

def write_to_ini(section, key, value):
    if section not in config:
        config[section] = {}
    config[section][key] = value
    with open(config_path, "w") as configfile:
        config.write(configfile)

def read_from_ini(section, key, default_value=""):
    if section not in config:
        config[section] = {}
    if key not in config[section]:
        config[section][key] = default_value
        with open(config_path, "w") as configfile:
            config.write(configfile)
    return config[section][key]

def checkGamePath():
    """
    Checks and sets the game installation path.

    This function reads the game path from an INI configuration file. If the path is not found or invalid,
    it attempts to set a default path and update the configuration file accordingly. It also ensures that
    the game path exists on the filesystem.

    Returns:
        bool: True if the game path exists and is valid, False otherwise.
    """
    global game_path
    game_path = os.path.abspath(read_from_ini("Game", "catania_path", default_value=""))
    if not game_path or not exists(game_path):
        return False
    else:
        game_path_var.set(game_path)
        if "Game" not in config.sections():
            config.add_section("Game")
        write_to_ini("Game", "catania_path", game_path)
        write_to_ini("Game", "installed", "True")
        return True

def launch_game():
    """
    Launches the Catania game if the executable is found.

    This function checks if the game path is valid and attempts to launch the game executable.
    If the game executable is found, it starts the game process, updates the button text, and minimizes the launcher window.
    If the game executable is not found, it displays an appropriate error message.

    Global Variables:
    - game_process: Stores the process of the launched game.
    - is_running: Boolean flag indicating if the game is currently running.

    Raises:
    - CTkMessagebox: Displays a message box if the game executable is not found or if the game path is not found.

    Returns:
    None
    """
    global game_process
    global is_running
    if checkGamePath():
        game_path = read_from_ini("Game", "catania_path")
        game_executable = os.path.join(game_path, "Catania.exe")
        print("Launching game from path:", game_executable)
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

def install_game(action:str = ""):
    """
    Handles the installation process of the game.

    Parameters:
    action (str): The action to be performed. It can be:
        - "" (default): Checks for user consent and displays the consent frame if not given.
        - "consent": Records user consent and prompts for the game zip file.
        - "manual": Skips consent check and directly prompts for the game zip file.

    The function performs the following steps based on the action:
        - If no action is provided and consent is not given, it displays the consent frame.
        - If no action is provided and consent is given, it proceeds to the consent action.
        - If the action is "consent", it records the consent, hides the consent frame, and prompts the user to select the game zip file.
        - If the action is "manual", it hides the consent frame and prompts the user to select the game zip file, then starts the installation in a separate thread.

    Returns:
    None
    """
    consent = read_from_ini("Installer","consent","False")
    if not action:
        if consent == "False":
            consentframe.pack(pady=10, padx=10, fill="both", expand=True)
        else:
            install_game(action="consent")
    elif action == "consent":
        write_to_ini("Installer","consent","True")
        consentframe.pack_forget()
        zip_path = filedialog.askopenfilename(title="Select Catania zip file", filetypes=[("Zip files", "*.zip")])
        if not zip_path:
            return
    elif action == "manual":
        consentframe.pack_forget()
        zip_path = filedialog.askopenfilename(title="Select Catania zip file", filetypes=[("Zip files", "*.zip")])
        if not zip_path:
            return
        threading.Thread(target=install_from_zip, args=(zip_path,)).start()

def install_from_zip(zip_path):
    """
    Extracts the contents of a ZIP file to a specified directory and updates the installation progress.
    Args:
        zip_path (str): The path to the ZIP file to be extracted.
    Side Effects:
        - Updates the progress bar and filename display during extraction.
        - Creates the installation directory if it does not exist.
        - Writes installation details to an INI file.
        - Updates the UI buttons after installation.
    Raises:
        OSError: If there is an error creating the installation directory.
        zipfile.BadZipFile: If the ZIP file is corrupt or not a ZIP file.
    """
    filename.pack(pady=5, padx=5, side="top")
    install_progress.pack(pady=5, padx=5, side="left", fill="x", expand=True)
    filenamevar.set("Extracting files...")
    install_dir = os.path.expanduser("~/Catania")
    os.makedirs(install_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        total_files = len(zip_ref.namelist())
        for i, file in enumerate(zip_ref.namelist()):
            filenamevar.set(f"Extracting: {file}")
            zip_ref.extract(file, install_dir)
            progress_var.set((i + 1) / total_files)
            app.update_idletasks()
            time.sleep(0.01)  # Simulate time delay for progress bar update

    write_to_ini("Game", "catania_path", install_dir)
    write_to_ini("Game", "installed", "True")
    install_progress.pack_forget()
    filename.pack_forget()
    update_buttons()

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
            launch_button.configure(text="Close Game", fg_color="red",hover_color="darkred", command=close_game)
        else:
            app.deiconify()  # Restore the launcher window
            app.lift()  # Bring the launcher window to the front
            app.focus_force()  # Focus the launcher window
            launch_button.configure(text="Launch Catania",fg_color="green",hover_color="darkgreen",command=launch_game)
            game_process = None
            is_running = False
        app.after(1000, update_button_text)  # Check every second
    else:
        launch_button.configure(text="Launch Catania",fg_color="green",hover_color="darkgreen",command=launch_game)

def update_buttons():
    global installed
    installed = checkGamePath()
    if installed:
        if not launch_button.winfo_viewable():
            launch_button.pack(pady=10, padx=10, side="right")
        launch_button.configure(text="Launch Catania",fg_color="green",hover_color="darkgreen",command=launch_game)
        direntry.pack(pady=10, padx=5, side="left", fill="x", expand=True)
        GameOptions.pack(pady=10, padx=5, side="right")
        copy_button.pack(pady=10, padx=5, side="right")
    else:
        launch_button.configure(text="Install Catania",fg_color="#3B8ED0",hover_color="#36719F",command=install_game)
        direntry.pack_forget()
        copy_button.pack_forget()
        GameOptions.pack_forget()

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
        with open(f"{versioninfo_dir}/{Version}.txt", "r") as file:
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
    global progress_var
    global update_progress_popup
    # ZIP-Datei herunterladen
    print("Lade ZIP-Datei herunter...")
    response = requests.get(zip_url)
    if response.status_code == 200:
        progress_var.set(.5)
        print("Download erfolgreich!")
        with io.BytesIO(response.content) as zip_file:
            progress_var.set(1)
            # ZIP-Datei öffnen
            with zipfile.ZipFile(zip_file) as zf:
                update_progress_popup.update_label("Extracting files...")
                update_progress_popup.update_progress(0)
                # Überprüfen, welche Dateien im Ordner "VersionInfo" liegen
                files_to_extract = [
                    file for file in zf.namelist() if file.startswith("GameInstaller-main/VersionInfo/")
                ]
                total_files = len(files_to_extract)
                # Falls der Ordner bereits existiert, löschen
                if os.path.exists(versioninfo_dir):
                    print(f"Lösche bestehenden Ordner '{versioninfo_dir}'...")
                    shutil.rmtree(versioninfo_dir)
                # Zielverzeichnis erstellen
                os.makedirs(versioninfo_dir, exist_ok=True)
                # Dateien extrahieren
                print(f"Extrahiere {total_files} Dateien...")
                for i, file in enumerate(files_to_extract):
                    zf.extract(file, versioninfo_dir)
                    progress = (i + 1) / total_files
                    update_progress_popup.update_progress(progress)
                    update_progress_popup.update_label(f"Extracting file {i + 1} of {total_files}...")
                    app.update_idletasks()

        # Dateien ins Zielverzeichnis verschieben
        extracted_dir = os.path.join(versioninfo_dir, "GameInstaller-main", "VersionInfo")
        for root, _, files in os.walk(extracted_dir):
            for file in files:
                source = os.path.join(root, file)
                relative_path = os.path.relpath(root, extracted_dir)
                destination = os.path.join(versioninfo_dir, relative_path, file)
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                shutil.move(source, destination)

        # Ursprünglichen Ordner löschen
        print("Bereinige temporäre Dateien...")
        shutil.rmtree(os.path.join(versioninfo_dir, "GameInstaller-main"))
        print(f"Fertig! Dateien wurden in '{versioninfo_dir}' entpackt.")
    else:
        print(f"Fehler beim Herunterladen: {response.status_code}")

def show_update_progress():
    global update_progress_popup
    update_progress_popup = ctk_components.CTkProgressPopup(app, title="Updating Version Info", label="Please wait...", message="Downloading and extracting files...",side="right_top")
    update_progress_popup.update_progress(0)
    app.update_idletasks()

def hide_update_progress():
    global update_progress_popup
    update_progress_popup.close_progress_popup()

def UpdatePND():
    global progress_var
    global update_progress_popup
    show_update_progress()
    download_and_extract_github_repo(repo_url, extract_to)
    hide_update_progress()
    if os.path.exists(versioninfo_dir):
        PNDropdown = CustomDropdownMenu(widget=PNButton)
        VersionInfofile = os.listdir(versioninfo_dir)
        for Version in VersionInfofile:
            Versionedit = Version.replace(".txt","")
            PNDropdown.add_option(option=Versionedit,command=lambda Versionedit=Versionedit: show_patch_notes(Version=Versionedit))
            if VersionInfofile.index(Version) != len(VersionInfofile) - 1: # Check if it is the last element
                PNDropdown.add_separator()

def uninstall_game():
    if not messagebox.askyesno("Confirm Uninstall", "Are you sure you want to uninstall Catania?"):
        return
    install_dir = read_from_ini("Game", "catania_path")
    if os.path.exists(install_dir):
        for root, dirs, files in os.walk(install_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(install_dir)
    write_to_ini("Game", "catania_path", "")
    write_to_ini("Game", "installed", "False")
    update_buttons()

def show_popup_menu(event):
    popup_menu.tk_popup(event.x_root, event.y_root)

def on_closing():
    if is_running:
        CTkMessagebox(master=app, title="Game Running", message="Please close the game before exiting the launcher.", option_1="OK", icon="warning")
    else:
        app.destroy()

def show_settings():
    settings_frame.pack(pady=10, padx=10, fill="both", expand=True)

def move_game_files(new_path):
    old_path = read_from_ini("Game", "catania_path")
    new_game_path = os.path.join(new_path, "CataniaGame")
    if os.path.exists(old_path): 
        try:
            # Hide all elements in the launch frame
            for widget in launchframe.winfo_children():
                widget.pack_forget()

            filename.pack(pady=5, padx=5, side="top")
            install_progress.pack(pady=5, padx=5, side="left", fill="x", expand=True)
            filenamevar.set("Moving files...")

            os.makedirs(new_game_path, exist_ok=True)
            total_files = sum([len(files) for r, d, files in os.walk(old_path)])
            count = 0
            for root, dirs, files in os.walk(old_path):
                for name in files:
                    src_file = os.path.join(root, name)
                    rel_path = os.path.relpath(src_file, old_path)
                    dest_file = os.path.join(new_game_path, rel_path)
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                    shutil.move(src_file, dest_file)
                    count += 1
                    progress_var.set(count / total_files)
                    app.update_idletasks()
                    time.sleep(0.01)  # Simulate time delay for progress bar update

            # Remove old directory structure
            shutil.rmtree(old_path)

            write_to_ini("Game", "catania_path", new_game_path)
            ctk_components.CTkNotification(app, message="Game files moved successfully.", side="right_top")
        except Exception as e:
            CTkMessagebox(master=app, title="Error", message=f"Failed to move game files: {e}", option_1="OK", icon="warning")
        finally:
            install_progress.pack_forget()
            filename.pack_forget()
            update_buttons()
    else:
        CTkMessagebox(master=app, title="Error", message="Old game path does not exist.", option_1="OK", icon="warning")

def save_game_path():
    new_path = game_path_var.get()
    if os.path.exists(new_path):
        move_game_files(new_path)
    else:
        CTkMessagebox(master=app, title="Invalid Path", message="The specified path does not exist.", option_1="OK", icon="warning")

def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        game_path_var.set(folder_selected)

# Widgets
menu = CTkMenuBar(app,bg_color="#2b2b2b",pady=5,padx=5,cursor="hand2")
PNButton = menu.add_cascade("Patch Notes")
SettingsButton = menu.add_cascade("Settings")
AboutButton = menu.add_cascade("About")

# Patch Notes
patch_notes_frame = ctk.CTkFrame(app)
back_button = ctk.CTkButton(patch_notes_frame, text="Back", command=lambda: patch_notes_frame.pack_forget())
back_button.pack(pady=5, padx=5, side="bottom")
VersionTitle = ctk.CTkLabel(patch_notes_frame, text=f"Patch Notes", font=("Arial", 20))
VersionTitle.pack(pady=5, padx=5, side="top")
VersionInfo = ctk.CTkScrollableFrame(patch_notes_frame)
VersionInfo.pack(pady=5, padx=10, fill="both", expand=True)

# Settings Frame
settings_frame = ctk.CTkFrame(app)
settings_label = ctk.CTkLabel(settings_frame, text="Launcher Settings", font=("Arial", 20))
settings_label.pack(pady=10, padx=10, side="top")
settings_back_button = ctk.CTkButton(settings_frame, text="Back", command=lambda: settings_frame.pack_forget())
settings_back_button.pack(pady=10, padx=10, side="bottom")

# Scrollable Frame for Settings
settings_scrollable_frame = ctk.CTkScrollableFrame(settings_frame)
settings_scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)

# Game Path Setting
game_path_label = ctk.CTkLabel(settings_scrollable_frame, text="Game Path:", anchor="w")
game_path_label.pack(pady=5, padx=10, fill="x")
game_path_var = tk.StringVar(value=read_from_ini("Game", "catania_path"))
game_path_frame = ctk.CTkFrame(settings_scrollable_frame)
game_path_frame.pack(pady=5, padx=10, fill="x")
game_path_entry = ctk.CTkEntry(game_path_frame, textvariable=game_path_var)
game_path_entry.pack(side="left", fill="x", expand=True)
select_folder_button = ctk.CTkButton(game_path_frame, text="Browse", command=select_folder)
select_folder_button.pack(side="right")
save_path_button = ctk.CTkButton(settings_scrollable_frame, text="Save Path", command=save_game_path)
save_path_button.pack(pady=5, padx=10)

# Patch Notes Dropdown
if os.path.exists(versioninfo_dir):
    PNDropdown = CustomDropdownMenu(widget=PNButton)
    VersionInfofile = os.listdir(versioninfo_dir)
    for Version in VersionInfofile:
        Versionedit = Version.replace(".txt","")
        PNDropdown.add_option(option=Versionedit,command=lambda Versionedit=Versionedit: show_patch_notes(Version=Versionedit))
        PNDropdown.add_separator()
else:
    UpdatePND()

# Settings Dropdown
SettingsDropdown = CustomDropdownMenu(widget=SettingsButton)
SettingsDropdown.add_option(option="Launcher Settings", command=show_settings)
SettingsDropdown.add_separator()
SettingsDropdown.add_option(option="Update Version info",command=lambda: threading.Thread(target=UpdatePND).start())
SettingsDropdown.add_separator()
SettingsDropdown.add_option(option="Check game path")

# Consent
consentframe = ctk.CTkFrame(app)
consenttext = ctk.CTkLabel(consentframe,text="If you install the game using the launcher, you will be redirected to microsoft to sing in and allow this app to access your OneDrive. This app cannot collect your login data during login process. OneDrive access is only used to locate the game files and request them from the API. If you do not wish for the app to do this you can download the zip file manually from OneDrive and let the launcher install a predownloaded Version.",wraplength=500,justify="center")
consenttext.pack(pady=10, padx=10, side="top")
consentbutton = ctk.CTkButton(consentframe,text="I agree",command=lambda: install_game("consent"))
consentbutton.pack(pady=10, padx=10, side="bottom")
manualbutton = ctk.CTkButton(consentframe,text="Install manually",command=lambda: install_game("manual"))
manualbutton.pack(pady=10, padx=10, side="bottom")
nothingbutton = ctk.CTkButton(consentframe,text="Go back",command=consentframe.pack_forget)
nothingbutton.pack(pady=10, padx=10, side="bottom")

# Launch Frame
launchframe = ctk.CTkFrame(app)
launchframe.pack(pady=10, padx=10, fill="x", side="bottom")
base_dir = os.path.dirname(os.path.abspath(__file__))
dots_icon_path = os.path.join(base_dir, "icons/Dots/Light.png")
dots = ctk.CTkImage(Image.open(dots_icon_path))
launch_button = ctk.CTkButton(launchframe, text="Launch Catania", command=launch_game)
launch_button.pack(pady=10, padx=10, side="right")
GameOptions = ctk.CTkButton(launchframe, image=dots, text="", width=20, height=30, fg_color="darkgray", hover_color="gray",cursor="hand2")
GameOptions.pack(pady=10, padx=5, side="right")
GameOptions.bind("<Button-1>", show_popup_menu)
install_progress = ctk.CTkProgressBar(launchframe, variable=progress_var)
filenamevar = tk.StringVar()
filename = ctk.CTkLabel(launchframe, textvariable=filenamevar,anchor="w",justify="left")

# Popup Menu
popup_menu = tk.Menu(app, tearoff=0)
popup_menu.add_command(label="Update", command=UpdatePND)
popup_menu.add_command(label="Uninstall", command=uninstall_game)

# Game path entry
checkGamePath()
direntry = ctk.CTkEntry(launchframe, textvariable=game_path_var, state="readonly")

# Load the icon image
base_dir = os.path.dirname(os.path.abspath(__file__))
copy_icon_path = os.path.join(base_dir, "icons/copy/Light.png")
copy_icon = ctk.CTkImage(Image.open(copy_icon_path))

copy_button = ctk.CTkButton(
    launchframe, 
    image=copy_icon, 
    text="", 
    command=lambda: os.startfile(game_path_var.get()), 
    width=30, 
    height=30, 
    fg_color="darkgray", 
    hover_color="gray"
)

# Initial state
update_buttons()

app.protocol("WM_DELETE_WINDOW", on_closing)
app.after(1, update_buttons)
app.after(1000,lambda: threading.Thread(target=UpdatePND).start())
app.mainloop()
