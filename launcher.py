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
import webbrowser
from ftplib import FTP, error_perm, error_temp, error_proto, error_reply
import socket
from cpuinfo import get_cpu_info
import psutil
import GPUtil

ctk.set_appearance_mode("dark")

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

#FTP
FTP_HOST = "deinname.o2internet.de"
FTP_USER = "ftpuser"
FTP_PASS = "DEIN_PASSWORT"

game_path:str = ""
game_process = None
is_running = False
is_updating = False
installed = False
repo_url = "https://github.com/Charmander12345/GameInstaller/archive/refs/heads/main.zip"
extract_to = "VersionInfo"

progress_var = ctk.DoubleVar()
game_path_var = ctk.StringVar(value=game_path)

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
    game_path = read_from_ini("Game", "catania_path", default_value="")
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
        if os.path.exists(game_executable):
            game_process = subprocess.Popen(game_executable)
            is_running = True
            update_button_text()
            show_main_screen()
            if read_from_ini("Settings", "minimize_on_start", "True") == "True":
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
                if read_from_ini("Settings", "minimize_on_start", "True") == "True":
                    time.sleep(1)  # Wait for the game to start
                    app.iconify()  # Minimize the launcher window
            else:
                CTkMessagebox(master=app, title="Game not found", message= "Couldn't locate the executable.", option_1="OK", icon="warning")
        else:
            CTkMessagebox(master=app, title="Catania not installed", message= "Game path not found. Please install Catania first.", option_1="OK", icon="warning")

def install_game(action:str = ""):
    """
    Handles the installation process of the game based on the provided action.
    Parameters:
    action (str): The action to be performed. It can be one of the following:
        - "" (default): Checks the consent status and either shows the consent frame or proceeds with installation.
        - "consent": Writes consent to the INI file, hides the consent frame, and starts the game version retrieval process.
        - "manual": Hides the consent frame, prompts the user to select a zip file, and starts the installation from the selected zip file.
    Returns:
    None
    """
    if action == "consent":
        print("installing game with Launcher")
        write_to_ini("Installer","consent","True")
        show_main_screen()
        threading.Thread(target=get_GameVersions).start()
        abc = ctk_components.CTkNotification(app,message="Logging in...",side="right_top")
        time.sleep(2)
        abc.close_notification()
    elif action == "manual":
        show_main_screen()
        zip_path = filedialog.askopenfilename(title="Select Catania zip file", filetypes=[("Zip files", "*.zip")])
        if not zip_path:
            ctk_components.CTkNotification(app, message="No zip file selected.", side="right_top")
            return
        launch_button.pack_forget()
        threading.Thread(target=install_from_zip, args=(zip_path,)).start()
    else:
        show_install_info()

def update_game():
    global is_updating
    zip_path = filedialog.askopenfilename(title="Select Catania zip file", filetypes=[("Zip files", "*.zip")])
    if not zip_path:
        return
    is_updating = True
    launch_button.pack_forget()
    GameOptions.pack_forget()
    copy_button.pack_forget()
    direntry.pack_forget()
    filename.pack(pady=5, padx=5, side="top")
    install_progress.pack(pady=5, padx=5, side="left", fill="x", expand=True)
    filenamevar.set("Deleteing old files...")

    #uninstall the game
    install_dir = read_from_ini("Game", "catania_path")
    if os.path.exists(install_dir):
        for root, dirs, files in os.walk(install_dir, topdown=False):
            total_files = len(files)
            for name in files:
                os.remove(os.path.join(root, name))
                progress_var.set((files.index(name) + 1) / total_files)
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(install_dir)
    filenamevar.set("Installing new files...")
    progress_var.set(0)
    threading.Thread(target=install_from_zip, args=(zip_path, read_from_ini("Game", "catania_path"))).start()
    ctk_components.CTkNotification(app, message="Game updated successfully.", side="right_top")
    is_updating = False

def install_from_zip(zip_path,OWinstall_dir = ""):
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
    if OWinstall_dir:
        install_dir = OWinstall_dir
    else:
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
    """
    Closes the running game process if it is active.

    This function attempts to terminate the game process identified by the global variable `game_process`.
    It iterates through all running processes to find the one matching the PID of `game_process` or the executable name "Catania.exe".
    If found, it tries to terminate the process gracefully, and if it does not terminate within 5 seconds, it forces the process to kill.
    Additionally, it terminates any child processes of the game process.

    Globals:
        game_process (psutil.Process): The process object representing the running game.
        is_running (bool): A flag indicating whether the game is currently running.

    Side Effects:
        Updates the global variables `game_process` and `is_running`.
        Calls `update_button_text()` to update the UI button text.

    Exceptions:
        Handles `psutil.NoSuchProcess`, `psutil.AccessDenied`, and `psutil.ZombieProcess` exceptions during process termination.
    """
    global game_process
    global is_running
    if game_process:
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['pid'] == game_process.pid or "Catania.exe" in (proc.info['exe'] or ""):
                    close_notif = ctk_components.CTkNotification(app, message="Closing the game...", side="right_top")
                    proc.terminate()  # Versuche, den Prozess zu beenden
                    try:
                        proc.wait(timeout=5)  # Warte, bis der Prozess beendet ist
                    except psutil.TimeoutExpired:
                        proc.kill()  # Erzwinge die Beendigung
                    # Beende mögliche Kindprozesse
                    for child in proc.children(recursive=True):
                        child.terminate()
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                CTkMessagebox(master=app, title="Error", message=f"Failed to close the game: {e}", option_1="OK", icon="warning")
        game_process = None
        is_running = False
        update_button_text()
        close_notif.close_notification()

def update_button_text():
    """
    Updates the text and appearance of the launch button based on the state of the game process.

    This function checks if the game process is running and updates the launch button's text,
    color, and command accordingly. If the game is running, the button will allow the user to
    close the game. If the game is not running, the button will allow the user to launch the game.
    The function also ensures that the launcher window is brought to the front and focused when
    the game is not running.

    Globals:
        game_process: The process object representing the running game.
        is_running: A boolean indicating whether the game is currently running.

    Side Effects:
        Modifies the text, color, and command of the launch button.
        May bring the launcher window to the front and focus it.

    Schedule:
        This function schedules itself to run again after 1000 milliseconds (1 second) if the game
        is running.
    """
    global game_process
    global is_running
    if is_running:
        if game_process and game_process.poll() is None:  # Process is running
            launch_button.configure(text="Close Game", fg_color="red",hover_color="darkred", command=lambda: threading.Thread(target=close_game).start())
        else:
            if read_from_ini("Settings", "restore_on_exit", "True") == "True":
                app.deiconify()  # Restore the launcher window
                app.lift()  # Bring the launcher window to the front
                app.focus_force()  # Focus the launcher window
            launch_button.configure(text="Launch Catania",fg_color="green",hover_color="darkgreen",command=launch_game)
            game_process = None
            is_running = False
        app.after(1000, update_button_text)  # Check every second
    else:
        launch_button.configure(text="Launch Catania",fg_color="green",hover_color="darkgreen",command=launch_game)
        show_main_screen()

def update_buttons():
    """
    Updates the state and visibility of various buttons in the game installer UI based on whether the game is installed.

    This function checks if the game is installed by calling `checkGamePath()`. Depending on the result, it updates the 
    text, colors, and commands of the `launch_button`, and manages the visibility of `direntry`, `GameOptions`, and 
    `copy_button`.

    If the game is installed:
        - Displays the `launch_button` with text "Launch Catania" and green colors.
        - Packs `direntry`, `GameOptions`, and `copy_button` with specified padding and alignment.

    If the game is not installed:
        - Configures the `launch_button` with text "Install Catania" and blue colors.
        - Hides `direntry`, `GameOptions`, and `copy_button`.

    Globals:
        installed (bool): Indicates whether the game is installed.

    """
    global installed
    installed = checkGamePath()
    if installed:
        if not launch_button.winfo_viewable():
            launch_button.pack(pady=10, padx=10, side="right")
        launch_button.configure(text="Launch Catania", fg_color="green", hover_color="darkgreen", command=launch_game)
        select_folder_button.configure(state="normal")
        save_path_button.configure(state="normal")
        direntry.pack(pady=10, padx=5, side="left", fill="x", expand=True)
        GameOptions.pack(pady=10, padx=5, side="right")
        copy_button.pack(pady=10, padx=5, side="right")
        requirements_frame.pack_forget()
        game_info_frame.pack(pady=10, padx=10, fill="both", expand=True)
    else:
        if not launch_button.winfo_viewable():
            launch_button.pack(pady=10, padx=10, side="right")
        launch_button.configure(text="Install Catania", fg_color="#3B8ED0", hover_color="#36719F", command=install_game)
        save_path_button.configure(state="disabled")
        select_folder_button.configure(state="disabled")
        direntry.pack_forget()
        copy_button.pack_forget()
        GameOptions.pack_forget()
        requirements_frame.pack(pady=10, padx=10, fill="both", expand=True)
        game_info_frame.pack_forget()

def copy_path():
    app.clipboard_clear()
    app.clipboard_append(game_path_var.get())
    app.update()  # Keeps the clipboard content after the app is closed
    CTkMessagebox(master=app, title="Path Copied", message="Game path copied to clipboard.", option_1="OK", icon="info")

def show_patch_notes(Version: str = "0.5"):
    """
    Displays the patch notes for the specified version in the patch notes frame.
    Args:
        Version (str): The version number of the patch notes to display. Defaults to "0.5".
    Behavior:
        - Hides the settings frame.
        - Displays the patch notes frame.
        - Updates the title of the patch notes with the specified version.
        - Clears any existing widgets in the VersionInfo frame.
        - Loads and displays the patch notes from a file corresponding to the specified version.
        - If the file is not found, displays an error message indicating that the patch notes file was not found.
    Note:
        The patch notes are expected to be stored in text files named with the version number (e.g., "0.5.txt") 
        in the directory specified by `versioninfo_dir`.
    """
    launcher_info_frame.pack_forget()
    consentframe.pack_forget()
    requirements_frame.pack_forget()
    settings_frame.pack_forget()
    patch_notes_frame.pack(pady=10, padx=10, fill="both", expand=True)
    VersionTitle.configure(text=f"Patch Notes {Version}")

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
        ctk.CTkLabel(VersionInfo,text="Patch notes file not found.",wraplength=600,anchor="w",justify="left").pack(pady=2, padx=5, side="top")

def download_and_extract_github_repo(zip_url, extract_to):
    global progress_var
    global update_progress_popup
    # ZIP-Datei herunterladen
    response = requests.get(zip_url)
    if response.status_code == 200:
        progress_var.set(.5)
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
                    shutil.rmtree(versioninfo_dir)
                # Zielverzeichnis erstellen
                os.makedirs(versioninfo_dir, exist_ok=True)
                # Dateien extrahieren
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
        shutil.rmtree(os.path.join(versioninfo_dir, "GameInstaller-main"))
    else:
        CTkMessagebox(master=app, title="Error", message="Failed to download version info.", option_1="OK", icon="warning")

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
        total_files = sum([len(files) for r, d, files in os.walk(install_dir)])
        count = 0
        launch_button.pack_forget()
        GameOptions.pack_forget()
        copy_button.pack_forget()
        direntry.pack_forget()
        filename.pack(pady=5, padx=5, side="top")
        install_progress.pack(pady=5, padx=5, side="left", fill="x", expand=True)
        filenamevar.set("Uninstalling files...")
        for root, dirs, files in os.walk(install_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
                count += 1
                progress_var.set(count / total_files)
                app.update_idletasks()
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(install_dir)
        filename.pack_forget()
        install_progress.pack_forget()
    write_to_ini("Game", "catania_path", "")
    write_to_ini("Game", "installed", "False")
    update_buttons()

def show_popup_menu(event):
    popup_menu.tk_popup(event.x_root, event.y_root)

def on_closing():
    if is_running:
        CTkMessagebox(master=app, title="Game Running", message="Please close the game before exiting the launcher.", option_1="OK", icon="warning")
    elif is_updating:
        CTkMessagebox(master=app, title="Update in Progress", message="Please wait for the update to complete before exiting the launcher.", option_1="OK", icon="warning")
    else:
        app.destroy()

def get_game_info():
    """
    Retrieves information about the installed game, such as its size.
    Returns:
        dict: A dictionary containing game information.
    """
    game_info = {}
    game_path = read_from_ini("Game", "catania_path")
    if os.path.exists(game_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(game_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        game_info['size'] = total_size
        game_info['path'] = game_path
    return game_info

def show_main_screen():
    """
    Shows the main screen and hides other frames.
    """
    settings_frame.pack_forget()
    onedrive_info_frame.pack_forget()
    launcher_info_frame.pack_forget()
    consentframe.pack_forget()
    patch_notes_frame.pack_forget()
    if not installed:
        requirements_frame.pack(pady=10, padx=10, fill="both", expand=True)
    else:
        requirements_frame.pack_forget()
        game_info = get_game_info()
        game_info_text.set(f"Game Path: {game_info['path']}\nGame Size: {game_info['size'] / (1024**3):.2f} GB")
        game_info_frame.pack(pady=10, padx=10, fill="both", expand=True)
        if is_running:
            game_info_frame.pack_forget()
            usage_info_frame.pack(pady=10, padx=10, fill="both", expand=True)
            update_usage_info()
        else:
            usage_info_frame.pack_forget()

def show_settings():
    """
    Shows the settings frame and hides other frames.
    """
    patch_notes_frame.pack_forget()
    onedrive_info_frame.pack_forget()
    launcher_info_frame.pack_forget()
    requirements_frame.pack_forget()
    game_info_frame.pack_forget()
    usage_info_frame.pack_forget()
    settings_frame.pack(pady=10, padx=10, fill="both", expand=True)

def show_launcher_info():
    """
    Shows the launcher info frame and hides other frames.
    """
    patch_notes_frame.pack_forget()
    settings_frame.pack_forget()
    onedrive_info_frame.pack_forget()
    requirements_frame.pack_forget()
    game_info_frame.pack_forget()
    usage_info_frame.pack_forget()
    launcher_info_frame.pack(pady=10, padx=10, fill="both", expand=True)

def show_install_info():
    """
    Shows the install info
    """
    patch_notes_frame.pack_forget()
    settings_frame.pack_forget()
    onedrive_info_frame.pack_forget()
    requirements_frame.pack_forget()
    launcher_info_frame.pack_forget()
    game_info_frame.pack_forget()
    usage_info_frame.pack_forget()
    consentframe.pack(pady=10, padx=10, fill="both", expand=True)

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

def toggle_minimize_on_start():
    current_value = read_from_ini("Settings", "minimize_on_start", "True")
    new_value = "False" if current_value == "True" else "True"
    write_to_ini("Settings", "minimize_on_start", new_value)

def toggle_restore_on_exit():
    current_value = read_from_ini("Settings", "restore_on_exit", "True")
    new_value = "False" if current_value == "True" else "True"
    write_to_ini("Settings", "restore_on_exit", new_value)

def open_github_repo():
    webbrowser.open("https://github.com/Charmander12345/GameInstaller", new=2)

def get_GameVersions():
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER,FTP_PASS)
        availableVersions = ftp.nlst()
        # Handle the available versions as needed
    except error_perm:
        x = ctk_components.CTkNotification(app,"warning2","Unable to login to game build server.","right_top")
        time.sleep(2)
        if x.winfo_viewable:
            x.close_notification()
    except socket.gaierror:
        x = ctk_components.CTkNotification(app,"warning","The IP address of the game build server could not be resolved.","right_top")
        time.sleep(2)
        if x.winfo_viewable:
            x.close_notification()
    except error_temp:
        x = ctk_components.CTkNotification(app,"warning2","Temporary problem on the server.","right_top")
        time.sleep(2)
        if x.winfo_viewable:
            x.close_notification()
    except error_reply:
        x = ctk_components.CTkNotification(app,"warning","Unexpected response from game build server.","right_top")
        time.sleep(2)
        if x.winfo_viewable:
            x.close_notification()
    except TimeoutError:
        x = ctk_components.CTkNotification(app,"warning","Timeout while attempting to connect.","right_top")
        time.sleep(2)
        if x.winfo_viewable:
            x.close_notification()

def update_usage_info():
    """
    Updates the usage information for GPU, CPU, and RAM.
    """
    if is_running:
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        gpus = GPUtil.getGPUs()
        gpu_usage = gpus[0].load * 100 if gpus else 0

        usage_info_text.set(f"CPU Usage: {cpu_usage}%\nRAM Usage: {ram_usage}%\nGPU Usage: {gpu_usage}%")
        app.after(1000, update_usage_info)  # Update every second

# Widgets
menu = CTkMenuBar(app,bg_color="#2b2b2b",pady=5,padx=5,cursor="hand2")
PNButton = menu.add_cascade("Patch Notes")
SettingsButton = menu.add_cascade("Settings")
AboutButton = menu.add_cascade("About")

# Patch Notes
patch_notes_frame = ctk.CTkFrame(app)
back_button = ctk.CTkButton(patch_notes_frame, text="Back", command=show_main_screen)
back_button.pack(pady=5, padx=5, side="bottom")
VersionTitle = ctk.CTkLabel(patch_notes_frame, text=f"Patch Notes", font=("Arial", 20))
VersionTitle.pack(pady=5, padx=5, side="top")
VersionInfo = ctk.CTkScrollableFrame(patch_notes_frame)
VersionInfo.pack(pady=5, padx=10, fill="both", expand=True)

# Settings Frame
settings_frame = ctk.CTkFrame(app)
settings_label = ctk.CTkLabel(settings_frame, text="Launcher Settings", font=("Arial", 20))
settings_label.pack(pady=10, padx=10, side="top")
settings_back_button = ctk.CTkButton(settings_frame, text="Back", command=show_main_screen)
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

# Minimize on Start Setting
minimize_on_start_var = ctk.StringVar(value=read_from_ini("Settings", "minimize_on_start", "True"))
minimize_on_start_checkbox = ctk.CTkCheckBox(settings_scrollable_frame, text="Minimize on Game Start", variable=minimize_on_start_var, onvalue="True", offvalue="False", command=toggle_minimize_on_start)
minimize_on_start_checkbox.pack(pady=5, padx=10)

# Restore on Exit Setting
restore_on_exit_var = ctk.StringVar(value=read_from_ini("Settings", "restore_on_exit", "True"))
restore_on_exit_checkbox = ctk.CTkCheckBox(settings_scrollable_frame, text="Restore on Game Exit", variable=restore_on_exit_var, onvalue="True", offvalue="False", command=toggle_restore_on_exit)
restore_on_exit_checkbox.pack(pady=5, padx=10)

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

# Onedrive Info Frame
onedrive_info_frame = ctk.CTkFrame(app)
onedrive_info_title = ctk.CTkLabel(onedrive_info_frame, text="OneDrive Access", font=("Arial", 20))
onedrive_info_title.pack(pady=10, padx=10, side="top")
onedrive_info_text = ctk.CTkLabel(onedrive_info_frame, text="This app needs access to your OneDrive to locate and download the game files. You will be redirected to Microsoft to sign in and grant this permission. The app does not store your login details.\n The app also does not directly access your OneDrive. The permission is rather to check if you have permission to view the Folder. The launcher does not get to see any contents of your OneDrive nor can it request any of your personal data.\nFor more information, visit our GitHub repository:", wraplength=500, justify="center")
onedrive_info_text.pack(pady=10, padx=10, side="top")

github_button = ctk.CTkButton(onedrive_info_frame, text="GitHub Repository", command=open_github_repo)
github_button.pack(pady=10, padx=10, side="top")
onedrive_info_text.pack(pady=10, padx=10, side="top")
onedrive_info_back_button = ctk.CTkButton(onedrive_info_frame, text="Back", command=show_main_screen)
onedrive_info_back_button.pack(pady=10, padx=10, side="bottom")

# Launcher Info Frame
launcher_info_frame = ctk.CTkFrame(app)
launcher_info_title = ctk.CTkLabel(launcher_info_frame, text="Launcher Information", font=("Arial", 20))
launcher_info_title.pack(pady=10, padx=10, side="top")
launcher_info_text = ctk.CTkLabel(launcher_info_frame, text="This launcher is developed by Horizon Creations to manage the installation, updating, and uninstallation of the Catania game. For more information, visit our GitHub repository:", wraplength=500, justify="center")
launcher_info_text.pack(pady=10, padx=10, side="top")

github_button_launcher_info = ctk.CTkButton(launcher_info_frame, text="GitHub Repository", command=open_github_repo)
github_button_launcher_info.pack(pady=10, padx=10, side="top")
launcher_info_back_button = ctk.CTkButton(launcher_info_frame, text="Back", command=show_main_screen)
launcher_info_back_button.pack(pady=10, padx=10, side="bottom")

# Consent
consentframe = ctk.CTkFrame(app)
consenttext = ctk.CTkLabel(consentframe,text="The Launcher can download the game from a dedicated server. If you already have a downloaded zip file from the OneDrive folder you can use the Launcher to install that.",wraplength=500,justify="center")
consenttext.pack(pady=10, padx=10, side="top")
consentbutton = ctk.CTkButton(consentframe,text="Launcher download",command=lambda: threading.Thread(target=install_game("consent")).start())
consentbutton.pack(pady=10, padx=10, side="bottom")
manualbutton = ctk.CTkButton(consentframe,text="Install manually",command=lambda: install_game("manual"))
manualbutton.pack(pady=10, padx=10, side="bottom")
nothingbutton = ctk.CTkButton(consentframe,text="Go back",command=show_main_screen)
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
filenamevar = ctk.StringVar()
filename = ctk.CTkLabel(launchframe, textvariable=filenamevar,anchor="w",justify="left")
requirements_label = ctk.CTkLabel(launchframe, text="Checking system requirements...", anchor="w", justify="left")

# Popup Menu
popup_menu = tk.Menu(app, tearoff=0)
popup_menu.add_command(label="Update", command=lambda: threading.Thread(target=update_game).start())
popup_menu.add_command(label="Uninstall", command= lambda: threading.Thread(target=uninstall_game).start())

# Game path entry
direntry = ctk.CTkEntry(launchframe, textvariable=game_path_var, state="readonly")

# Load the icon image
base_dir = os.path.dirname(os.path.abspath(__file__))
copy_icon_path = os.path.join(base_dir, "icons/copy/Light.png")
copy_icon = ctk.CTkImage(Image.open(copy_icon_path))
copy_button = ctk.CTkButton(launchframe, image=copy_icon, text="", command=lambda: os.startfile(game_path_var.get()), width=30, height=30, fg_color="darkgray", hover_color="gray")

# Minimum Requirements Frame
requirements_frame = ctk.CTkFrame(app)
requirements_label = ctk.CTkLabel(requirements_frame, text="Minimum System Requirements", font=("Arial", 20))
requirements_label.pack(pady=10, padx=10, side="top")

requirements_text = """
- OS: Windows 10 or higher
- Processor: AMD Ryzen 5 3600X / Intel Core i5-10600K or better
- Memory: 16 GB RAM
- Graphics: NVIDIA RTX 3060 / AMD RX 6600 or better
- DirectX: Version 12
- Storage: 8 GB available space

Even tho you can technically still install and run the game we would not recommend it with a configuration below the minimum requirements.
"""
requirements_details = ctk.CTkLabel(requirements_frame, text=requirements_text, justify="left", anchor="w")
requirements_details.pack(pady=10, padx=10, side="top")

# Game Info Frame
game_info_frame = ctk.CTkFrame(app)
game_info_label = ctk.CTkLabel(game_info_frame, text="Game Information", font=("Arial", 20))
game_info_label.pack(pady=10, padx=10, side="top")

game_info_text = ctk.StringVar()
game_info = get_game_info()
game_info_text.set(f"Game Path: {game_info['path']}\nGame Size: {game_info['size'] / (1024**3):.2f} GB")
game_info_details = ctk.CTkLabel(game_info_frame, textvariable=game_info_text, justify="left", anchor="w")
game_info_details.pack(pady=10, padx=10, side="top")

# Usage Info Frame
usage_info_frame = ctk.CTkFrame(app)
usage_info_label = ctk.CTkLabel(usage_info_frame, text="System Usage Information", font=("Arial", 20))
usage_info_label.pack(pady=10, padx=10, side="top")

usage_info_text = tk.StringVar()
usage_info_details = ctk.CTkLabel(usage_info_frame, textvariable=usage_info_text, justify="left", anchor="w")
usage_info_details.pack(pady=10, padx=10, side="top")

# About Dropdown
AboutDropdown = CustomDropdownMenu(widget=AboutButton)
AboutDropdown.add_option(option="About the game")
AboutDropdown.add_separator()
launcher_submenu = AboutDropdown.add_submenu(submenu_name="About the launcher")
launcher_submenu.add_option(option="Info", command=show_launcher_info)
launcher_submenu.add_separator()
launcher_submenu.add_option(option="Author", command=lambda: CTkMessagebox(master=app, title="Author", message="Developed by Horizon Creations", option_1="OK", icon="info"))

app.protocol("WM_DELETE_WINDOW", on_closing)
app.after(100, update_buttons)
app.after(1000,lambda: threading.Thread(target=UpdatePND).start())
app.mainloop()
