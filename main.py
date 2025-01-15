import os
import customtkinter as ctk
from tkinter import filedialog
from Classes import window_position
from configparser import ConfigParser
import zipfile
import time
import win32com.client
from tkinter import messagebox

config = ConfigParser()
config.read("config.ini")

app = ctk.CTk()
app.title("Catania Installer")
window_position.center_window(app,400,200)
catania_installed = False
install_dir = os.path.expanduser("~/Catania")

def install():
    print("Install button clicked")
    show_progress_frame("Installation in progress...")
    zip_path = filedialog.askopenfilename(title="Select Catania zip file", filetypes=[("Zip files", "*.zip")])
    if not zip_path:
        show_main_frame()
        return

    install_dir = os.path.expanduser("~/Catania")
    os.makedirs(install_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        total_files = len(zip_ref.namelist())
        for i, file in enumerate(zip_ref.namelist()):
            zip_ref.extract(file, install_dir)
            progress_var.set((i + 1) / total_files * 100)
            app.update_idletasks()
            time.sleep(0.01)  # Simulate time delay for progress bar update

    write_to_ini("Game", "catania_path", install_dir)
    write_to_ini("Game", "installed", "True")

    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    shortcut_path = os.path.join(desktop, "Catania.lnk")

    create_shortcut(f"{install_dir}/Catania.exe", shortcut_path)

    show_main_frame()

def uninstall():
    print("Uninstall button clicked")
    if not messagebox.askyesno("Confirm Uninstall", "Are you sure you want to uninstall Catania?"):
        show_main_frame()
        return
    show_progress_frame("Uninstallation in progress...")
    install_dir = config["Game"]["catania_path"]
    if os.path.exists(install_dir):
        total_files = sum([len(files) for r, d, files in os.walk(install_dir)])
        count = 0
        for root, dirs, files in os.walk(install_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
                count += 1
                progress_var.set(count / total_files * 100)
                app.update_idletasks()
                time.sleep(0.01)  # Simulate time delay for progress bar update
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(install_dir)

    write_to_ini("Game", "catania_path", "")
    write_to_ini("Game", "installed", "False")

    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    shortcut_path = os.path.join(desktop, "Catania.lnk")
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)

    show_main_frame()

def update():
    print("Update button clicked")

def show_progress_frame(message):
    progress_label.configure(text=message)
    main.pack_forget()
    progress_frame.pack(pady=20, padx=20, fill="both", expand=True)

def show_main_frame():
    progress_frame.pack_forget()
    main.pack(pady=20, padx=20, fill="both", expand=True)
    checkPath()

#Widgets
main = ctk.CTkFrame(app)
main.pack(pady=20, padx=20, fill="both", expand=True)

progress_frame = ctk.CTkFrame(app)
progress_label = ctk.CTkLabel(progress_frame, text="Installation in progress...")
progress_label.pack(pady=20, padx=20)

progress_var = ctk.DoubleVar()
progress_bar = ctk.CTkProgressBar(progress_frame, variable=progress_var)
progress_bar.pack(pady=20, padx=20, fill="x")

install_button = ctk.CTkButton(main, text="Install", command=install)
install_button.place(relx=0.7, rely=0.5, anchor="center")

update_button = ctk.CTkButton(main, text="Update", command=update)
update_button.place(relx=0.3, rely=0.5, anchor="center")


def checkPath():
    if "Game" not in config:
        config["Game"] = {}
    if "catania_path" not in config["Game"]:
        config["Game"]["catania_path"] = ""
        with open("config.ini", "w") as configfile:
            config.write(configfile)
        print("Catania path not set")
        if os.path.exists(install_dir):
            print("Catania is installed")
            install_button.configure(text="Uninstall", command=uninstall)
            update_button.configure(state="normal")
            write_to_ini("Game", "catania_path", install_dir)
            write_to_ini("Game", "installed", "True")
            return True
        update_button.configure(state="disabled")
        install_button.configure(text="Install", command=install)
        return False
    if "installed" not in config["Game"]:
        write_to_ini("Game", "installed", "False")
        print("Installed not set")
        update_button.configure(state="disabled")
        install_button.configure(text="Install", command=install)
        return False
    else:
        if os.path.exists(config["Game"]["catania_path"]):
            print("Catania is installed")
            install_button.configure(text="Uninstall", command=uninstall)
            update_button.configure(state="normal")
            write_to_ini("Game", "installed", "True")
        else:
            print("Catania is not installed")
            install_button.configure(text="Install", command=install)
            update_button.configure(state="disabled")
        return os.path.exists(config["Game"]["catania_path"])

def create_shortcut(target_path, shortcut_path):
    """Creates a Windows shortcut."""
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    shortcut.save()

def start():
    global catania_installed
    catania_installed = checkPath()

def write_to_ini(section, key, value):
    if section not in config:
        config[section] = {}
    config[section][key] = value
    with open("config.ini", "w") as configfile:
        config.write(configfile)

#Mainloop
app.after(1, start)
app.mainloop()

