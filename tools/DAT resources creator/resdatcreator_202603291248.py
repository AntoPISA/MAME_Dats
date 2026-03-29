#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RDC - Resource DAT Creator v1.0 (dir2dat)
Tool for creating DAT files in Logiqx/MAME format
Version with multi-folder support - ONE MACHINE PER SUBFOLDER
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import hashlib
import zlib
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class ResourceDATCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("RDC v1.0")
        self.root.geometry("750x550")
        self.root.resizable(True, True)
        
        self.config_file = "resdatcreator_config.json"
        self.presets_file = "resdatcreator_presets.json"
        self.preferences = self.load_preferences()
        self.presets = self.load_presets()
        self.restore_window_size()
        
        self.source_folder = tk.StringVar(value=self.preferences.get('source_folder', ''))
        self.output_folder = tk.StringVar(value=self.preferences.get('output_folder', ''))
        self.file_type = tk.StringVar(value=self.preferences.get('file_type', 'png'))
        self.name = tk.StringVar(value=self.preferences.get('name', ''))
        self.dat_name = tk.StringVar(value=self.preferences.get('dat_name', ''))
        self.description = tk.StringVar(value=self.preferences.get('description', ''))
        self.category = tk.StringVar(value=self.preferences.get('category', 'MAME Arts'))
        self.date = tk.StringVar(value=self.preferences.get('date', datetime.now().strftime('%d/%m/%Y')))
        self.version = tk.StringVar(value=self.preferences.get('version', '0.272'))
        self.author = tk.StringVar(value=self.preferences.get('author', ''))
        self.email = tk.StringVar(value=self.preferences.get('email', ''))
        self.homepage = tk.StringVar(value=self.preferences.get('homepage', ''))
        self.url = tk.StringVar(value=self.preferences.get('url', ''))
        self.comment = tk.StringVar(value=self.preferences.get('comment', '-'))
        
        self.processing = False
        self.cancel_flag = False
        self.selected_preset = tk.StringVar(value="")
        self.window_width = 750
        self.window_height = 400
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<Configure>', self.on_window_resize)
        self.create_widgets()
        
    def on_window_resize(self, event):
        if event.widget == self.root:
            self.window_width = event.width
            self.window_height = event.height
            
    def on_closing(self):
        self.save_window_size()
        self.root.destroy()
        
    def restore_window_size(self):
        width = self.preferences.get('window_width', 750)
        height = self.preferences.get('window_height', 600)
        x = self.preferences.get('window_x', None)
        y = self.preferences.get('window_y', None)
        width = max(width, 750)
        height = max(height, 600)
        self.root.geometry(f"{width}x{height}")
        if x is not None and y is not None:
            self.root.geometry(f"+{x}+{y}")
        
    def save_window_size(self):
        try:
            geometry = self.root.geometry()
            parts = geometry.split('+')
            size_part = parts[0].split('x')
            width = int(size_part[0])
            height = int(size_part[1])
            x = int(parts[1]) if len(parts) > 1 else None
            y = int(parts[2]) if len(parts) > 2 else None
            self.preferences['window_width'] = width
            self.preferences['window_height'] = height
            if x is not None:
                self.preferences['window_x'] = x
            if y is not None:
                self.preferences['window_y'] = y
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving window size: {e}")
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        profile_frame = ttk.LabelFrame(scrollable_frame, text="Profile Management", padding="10")
        profile_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        profile_frame.columnconfigure(1, weight=1)
        ttk.Label(profile_frame, text="Profile:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.preset_combo = ttk.Combobox(profile_frame, textvariable=self.selected_preset, width=30)
        self.preset_combo['values'] = list(self.presets.keys()) if self.presets else ["No saved profiles"]
        self.preset_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        self.preset_combo.bind('<<ComboboxSelected>>', self.load_preset_selected)
        ttk.Button(profile_frame, text="Load", command=self.load_preset, width=10).grid(row=0, column=2, pady=3, padx=2)
        ttk.Button(profile_frame, text="Profiles", command=self.open_profile_settings, width=10).grid(row=0, column=3, pady=3, padx=2)
        
        config_frame = ttk.LabelFrame(scrollable_frame, text="File Configuration", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        config_frame.columnconfigure(1, weight=1)
        ttk.Label(config_frame, text="Source folder:").grid(row=0, column=0, sticky=tk.W, pady=3)
        ttk.Entry(config_frame, textvariable=self.source_folder, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Button(config_frame, text="Browse...", command=self.browse_source).grid(row=0, column=2, pady=3)
        ttk.Label(config_frame, text="Output folder:").grid(row=1, column=0, sticky=tk.W, pady=3)
        ttk.Entry(config_frame, textvariable=self.output_folder, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Button(config_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2, pady=3)
        ttk.Label(config_frame, text="File type:").grid(row=2, column=0, sticky=tk.W, pady=3)
        file_types = ['png', 'jpg', 'jpeg', 'pdf', 'ico', 'zip', 'mp4', 'avi', 'mkv', 'gif', 'bmp']
        ttk.Combobox(config_frame, textvariable=self.file_type, values=file_types, width=20).grid(row=2, column=1, sticky=tk.W, pady=3, padx=5)
        
        action_frame = ttk.Frame(scrollable_frame, padding="10")
        action_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        ttk.Button(action_frame, text="Save Preferences", command=self.save_preferences).pack(side=tk.LEFT, padx=5)
        self.btn_create = ttk.Button(action_frame, text="Scan and Create DAT", command=self.start_create_dat)
        self.btn_create.pack(side=tk.LEFT, padx=5)
        self.btn_cancel = ttk.Button(action_frame, text="Cancel", command=self.cancel_processing, state=tk.DISABLED)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Exit", command=self.on_closing).pack(side=tk.RIGHT, padx=5)
        
        progress_frame = ttk.LabelFrame(scrollable_frame, text="Progress", padding="10")
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=3)
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=1, column=0, sticky=tk.W, pady=3)
        self.status_label = ttk.Label(progress_frame, text="Waiting...")
        self.status_label.grid(row=2, column=0, sticky=tk.W, pady=3)
        
        log_frame = ttk.LabelFrame(scrollable_frame, text="Operation Log", padding="10")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=10, width=80, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_log = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar_log.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar_log.set)
        self.log("Resource DAT Creator v1.0 started")
        self.log(f"Loaded {len(self.presets)} saved profiles")
        
    def open_profile_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Profile Settings")
        dialog.geometry("600x650")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (650 // 2)
        dialog.geometry(f"+{x}+{y}")
        main_frame = ttk.Frame(dialog, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        name_frame = ttk.LabelFrame(main_frame, text="Profile Name", padding="10")
        name_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        name_frame.columnconfigure(1, weight=1)
        ttk.Label(name_frame, text="Profile name:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.profile_name_entry = ttk.Entry(name_frame, width=50)
        self.profile_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        self.profile_name_entry.insert(0, self.selected_preset.get())
        header_frame = ttk.LabelFrame(main_frame, text="DAT Header Information", padding="10")
        header_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        header_frame.columnconfigure(1, weight=1)
        ttk.Label(header_frame, text="Name (filename):").grid(row=0, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.name, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Label(header_frame, text="DAT Name (header):").grid(row=1, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.dat_name, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Label(header_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.description, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Label(header_frame, text="Category:").grid(row=3, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.category, width=50).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Label(header_frame, text="Version:").grid(row=4, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.version, width=20).grid(row=4, column=1, sticky=tk.W, pady=3, padx=5)
        ttk.Label(header_frame, text="Date (dd/mm/yyyy):").grid(row=5, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.date, width=20).grid(row=5, column=1, sticky=tk.W, pady=3, padx=5)
        ttk.Label(header_frame, text="Author:").grid(row=6, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.author, width=50).grid(row=6, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Label(header_frame, text="Email:").grid(row=7, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.email, width=50).grid(row=7, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Label(header_frame, text="Homepage:").grid(row=8, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.homepage, width=50).grid(row=8, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Label(header_frame, text="URL:").grid(row=9, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.url, width=50).grid(row=9, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        ttk.Label(header_frame, text="Comment:").grid(row=10, column=0, sticky=tk.W, pady=3)
        ttk.Entry(header_frame, textvariable=self.comment, width=50).grid(row=10, column=1, sticky=(tk.W, tk.E), pady=3, padx=5)
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        ttk.Button(button_frame, text="Save Profile", command=lambda: self.save_profile_from_dialog(dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Profile", command=lambda: self.delete_profile_from_dialog(dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        info_label = ttk.Label(main_frame, text="Note: 'Name' is used for the filename, 'DAT Name' appears in the XML header", font=('TkDefaultFont', 9, 'italic'))
        info_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
    def log(self, message):
        self.log_text.configure(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
        
    def browse_source(self):
        folder = filedialog.askdirectory(title="Select source folder")
        if folder:
            self.source_folder.set(folder)
            self.log(f"Source folder: {folder}")
            
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder.set(folder)
            self.log(f"Output folder: {folder}")

    def load_presets(self):
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading profiles: {e}")
        return {}

    def save_presets(self):
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.log(f"Error saving profiles: {e}")
            return False

    def save_profile_from_dialog(self, dialog):
        profile_name = self.profile_name_entry.get().strip()
        if not profile_name:
            messagebox.showerror("Error", "Enter a profile name", parent=dialog)
            return
        if profile_name in self.presets and profile_name != self.selected_preset.get():
            if not messagebox.askyesno("Confirm", f"Profile '{profile_name}' already exists.\nOverwrite?", parent=dialog):
                return
        preset_data = {
            'source_folder': self.source_folder.get(),
            'output_folder': self.output_folder.get(),
            'file_type': self.file_type.get(),
            'name': self.name.get(),
            'dat_name': self.dat_name.get(),
            'description': self.description.get(),
            'category': self.category.get(),
            'date': self.date.get(),
            'version': self.version.get(),
            'author': self.author.get(),
            'email': self.email.get(),
            'homepage': self.homepage.get(),
            'url': self.url.get(),
            'comment': self.comment.get()
        }
        self.presets[profile_name] = preset_data
        self.save_presets()
        self.update_preset_combo()
        self.selected_preset.set(profile_name)
        self.log(f"Profile '{profile_name}' saved successfully")
        messagebox.showinfo("Success", f"Profile '{profile_name}' saved correctly!", parent=dialog)
        dialog.destroy()

    def delete_profile_from_dialog(self, dialog):
        profile_name = self.profile_name_entry.get().strip()
        if not profile_name:
            messagebox.showerror("Error", "Enter a profile name to delete", parent=dialog)
            return
        if profile_name not in self.presets:
            messagebox.showerror("Error", f"Profile '{profile_name}' does not exist", parent=dialog)
            return
        if messagebox.askyesno("Confirm", f"Delete profile '{profile_name}'?", parent=dialog):
            del self.presets[profile_name]
            self.save_presets()
            self.update_preset_combo()
            self.selected_preset.set("")
            self.log(f"Profile '{profile_name}' deleted")
            messagebox.showinfo("Success", f"Profile '{profile_name}' deleted successfully!", parent=dialog)
            dialog.destroy()

    def load_preset_selected(self, event=None):
        pass

    def load_preset(self):
        profile_name = self.selected_preset.get()
        if not profile_name or profile_name == "No saved profiles":
            messagebox.showwarning("Warning", "Select a profile to load")
            return
        if profile_name not in self.presets:
            messagebox.showerror("Error", f"Profile '{profile_name}' does not exist")
            return
        preset = self.presets[profile_name]
        self.source_folder.set(preset.get('source_folder', ''))
        self.output_folder.set(preset.get('output_folder', ''))
        self.file_type.set(preset.get('file_type', 'png'))
        self.name.set(preset.get('name', ''))
        self.dat_name.set(preset.get('dat_name', ''))
        self.description.set(preset.get('description', ''))
        self.category.set(preset.get('category', 'MAME Arts'))
        self.date.set(preset.get('date', datetime.now().strftime('%d/%m/%Y')))
        self.version.set(preset.get('version', '0.272'))
        self.author.set(preset.get('author', ''))
        self.email.set(preset.get('email', ''))
        self.homepage.set(preset.get('homepage', ''))
        self.url.set(preset.get('url', ''))
        self.comment.set(preset.get('comment', '-'))
        self.log(f"Profile '{profile_name}' loaded successfully")

    def update_preset_combo(self):
        if self.presets:
            self.preset_combo['values'] = list(self.presets.keys())
        else:
            self.preset_combo['values'] = ["No saved profiles"]
            
    def load_preferences(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading preferences: {e}")
        return {}
        
    def save_preferences(self):
        try:
            prefs = {
                'source_folder': self.source_folder.get(),
                'output_folder': self.output_folder.get(),
                'file_type': self.file_type.get(),
                'name': self.name.get(),
                'dat_name': self.dat_name.get(),
                'description': self.description.get(),
                'category': self.category.get(),
                'date': self.date.get(),
                'version': self.version.get(),
                'author': self.author.get(),
                'email': self.email.get(),
                'homepage': self.homepage.get(),
                'url': self.url.get(),
                'comment': self.comment.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
            self.log("Preferences saved successfully")
            messagebox.showinfo("Success", "Preferences saved correctly!")
        except Exception as e:
            self.log(f"Error saving preferences: {e}")
            messagebox.showerror("Error", f"Unable to save preferences:\n{e}")

    def calculate_file_hash(self, filepath):
        try:
            crc = 0
            sha1 = hashlib.sha1()
            with open(filepath, 'rb') as f:
                while chunk := f.read(65536):
                    crc = zlib.crc32(chunk, crc)
                    sha1.update(chunk)
            crc_formatted = format(crc & 0xFFFFFFFF, '08x')
            sha1_formatted = sha1.hexdigest()
            return crc_formatted, sha1_formatted
        except Exception as e:
            return None, None

    def process_file(self, filepath):
        try:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            crc, sha1 = self.calculate_file_hash(filepath)
            if crc and sha1:
                return {'name': filename, 'size': filesize, 'crc': crc, 'sha1': sha1, 'success': True}
            else:
                return {'name': filename, 'success': False, 'error': 'Hash calculation failed'}
        except Exception as e:
            return {'name': os.path.basename(filepath), 'success': False, 'error': str(e)}

    def scan_folders_structure(self, source_folder, file_extension):
        """
        Scan source folder and group files by first-level subfolder.
        Returns dict: {machine_name: [(relative_path, absolute_path), ...]}
        """
        machines = {}
        try:
            items = os.listdir(source_folder)
            items.sort()
            for item in items:
                if self.cancel_flag:
                    break
                item_path = os.path.join(source_folder, item)
                if os.path.isdir(item_path):
                    machine_name = item
                    self.log(f"Scanning machine folder: {machine_name}")
                    machine_files = []
                    for root, dirs, files in os.walk(item_path):
                        dirs.sort()
                        files.sort()
                        for filename in files:
                            if filename.lower().endswith(f'.{file_extension.lower()}'):
                                abs_path = os.path.join(root, filename)
                                rel_path = os.path.relpath(abs_path, item_path)
                                rel_path = rel_path.replace('/', '\\')
                                machine_files.append((rel_path, abs_path))
                    if machine_files:
                        machines[machine_name] = machine_files
                        self.log(f"  Found {len(machine_files)} files")
            # CORRETTO: Questo log è FUORI dal ciclo for
            self.log(f"Total machines found: {len(machines)}")
        except Exception as e:
            self.log(f"Error during scan: {e}")
        return machines

    def get_folder_name(self, path):
        """Get the name of the last folder from the path"""
        normalized_path = os.path.normpath(path)
        folder_name = os.path.basename(normalized_path)
        if not folder_name and normalized_path:
            folder_name = os.path.basename(normalized_path.rstrip(os.sep))
        return folder_name if folder_name else "resource"

    def start_create_dat(self):
        """Start DAT creation in a separate thread"""
        if self.processing:
            return
        if not self.source_folder.get():
            messagebox.showerror("Error", "Select a source folder")
            return
        if not self.output_folder.get():
            messagebox.showerror("Error", "Select an output folder")
            return
        if not os.path.exists(self.source_folder.get()):
            messagebox.showerror("Error", "Source folder does not exist")
            return
        self.processing = True
        self.cancel_flag = False
        self.btn_create.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        self.progress_var.set(0)
        thread = threading.Thread(target=self.create_dat_thread, daemon=True)
        thread.start()

    def cancel_processing(self):
        """Cancel ongoing processing"""
        self.cancel_flag = True
        self.log("Cancellation requested...")

    def update_progress(self, current, total, status=""):
        """Update progress bar (thread-safe)"""
        def _update():
            percentage = int((current / total * 100)) if total > 0 else 0
            self.progress_var.set(percentage)
            self.progress_label.config(text=f"Progress: {percentage}%")
            self.status_label.config(text=status)
        self.root.after(0, _update)

    def create_dat_thread(self):
        """Thread for DAT creation"""
        error_msg = None
        try:
            self.log("=" * 60)
            self.log("Starting DAT file creation")
            file_extension = self.file_type.get()
            self.update_progress(0, 100, "Scanning folders...")
            self.log(f"Scanning for .{file_extension} files...")
            machines = self.scan_folders_structure(self.source_folder.get(), file_extension)
            total_machines = len(machines)
            self.log(f"Found {total_machines} machines (subfolders)")
            if total_machines == 0:
                error_msg = "No files or folders found"
                self.root.after(0, lambda: messagebox.showwarning("Warning", error_msg))
                self.reset_ui()
                return
            if self.cancel_flag:
                self.reset_ui()
                return
            all_rom_data = {}
            total_files = sum(len(files) for files in machines.values())
            processed_files = 0
            self.log(f"Total files to process: {total_files}")
            for machine_name, files in machines.items():
                if self.cancel_flag:
                    break
                self.log(f"Processing machine: {machine_name} ({len(files)} files)")
                rom_data = []
                max_workers = min(4, os.cpu_count() or 2)
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_path = {
                        executor.submit(self.process_file, abs_path): (rel_path, abs_path)
                        for rel_path, abs_path in files
                    }
                    for future in as_completed(future_to_path):
                        if self.cancel_flag:
                            executor.shutdown(wait=False)
                            break
                        rel_path, abs_path = future_to_path[future]
                        result = future.result()
                        if result['success']:
                            result['name'] = rel_path
                            rom_data.append(result)
                        processed_files += 1
                        if processed_files % 10 == 0 or processed_files == total_files:
                            progress_pct = int(10 + (processed_files / total_files * 80))
                            self.update_progress(progress_pct, 100, f"Processing files ({processed_files}/{total_files})...")
                if rom_data:
                    all_rom_data[machine_name] = rom_data
                    self.log(f"  Machine '{machine_name}': {len(rom_data)} files processed")
            if self.cancel_flag:
                self.log("Process cancelled by user")
                self.reset_ui()
                return
            successful = sum(len(roms) for roms in all_rom_data.values())
            failed = total_files - successful
            self.log(f"Files processed successfully: {successful}")
            if failed > 0:
                self.log(f"Failed files: {failed}")
            self.update_progress(90, 100, "Generating DAT file...")
            self.log("Generating XML structure...")
            xml_content = self.generate_xml(all_rom_data)
            self.update_progress(95, 100, "Saving file...")
            filename_base = self.name.get().strip()
            if not filename_base:
                filename_base = self.dat_name.get().strip()
            if not filename_base:
                filename_base = self.get_folder_name(self.source_folder.get())
            dat_filename = f"{filename_base}.dat"
            dat_path = os.path.join(self.output_folder.get(), dat_filename)
            with open(dat_path, 'wb') as f:
                f.write(xml_content.encode('utf-8'))
            self.update_progress(100, 100, "Completed!")
            self.log(f"DAT file created: {dat_path}")
            self.log(f"Total machines: {len(all_rom_data)}")
            self.log(f"Total ROMs: {successful}")
            self.log("Creation completed successfully!")
            self.root.after(0, lambda: messagebox.showinfo("Success", f"DAT file created successfully!\nMachines: {len(all_rom_data)}\nFiles processed: {successful}\nPath: {dat_path}"))
        except Exception as e:
            error_msg = str(e)
            self.log(f"Critical error: {error_msg}")
            self.root.after(0, lambda err=error_msg: messagebox.showerror("Error", f"Unable to create DAT file:\n{err}"))
        finally:
            self.root.after(0, self.reset_ui)

    def generate_xml(self, all_rom_data):
        """Generate DAT XML content with multiple machines"""
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">')
        lines.append('<datafile>')
        lines.append('\t<header>')
        lines.append(f'\t\t<name>{self.dat_name.get() or f"Resource DAT {datetime.now().strftime("%Y%m%d")}"}</name>')
        lines.append(f'\t\t<description>{self.description.get() or f"Resource {datetime.now().strftime("%Y%m%d")}"}</description>')
        lines.append(f'\t\t<category>{self.category.get()}</category>')
        lines.append(f'\t\t<version>{self.version.get()}</version>')
        lines.append(f'\t\t<date>{self.date.get()}</date>')
        lines.append(f'\t\t<author>{self.author.get()}</author>')
        lines.append(f'\t\t<email>{self.email.get()}</email>')
        lines.append(f'\t\t<homepage>{self.homepage.get()}</homepage>')
        lines.append(f'\t\t<url>{self.url.get()}</url>')
        lines.append(f'\t\t<comment>{self.comment.get()}</comment>')
        lines.append('\t\t<clrmamepro/>')
        lines.append('\t</header>')
        for machine_name in sorted(all_rom_data.keys()):
            rom_data = all_rom_data[machine_name]
            lines.append(f'\t<machine name="{machine_name}">')
            lines.append(f'\t\t<description>{machine_name}</description>')
            rom_data.sort(key=lambda x: x['name'])
            for rom in rom_data:
                lines.append(f'\t\t<rom name="{rom["name"]}" size="{rom["size"]}" crc="{rom["crc"]}" sha1="{rom["sha1"]}"/>')
            lines.append('\t</machine>')
        lines.append('</datafile>')
        lines.append('')
        return '\r\n'.join(lines)

    def reset_ui(self):
        """Reset interface after completion"""
        self.processing = False
        self.btn_create.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = ResourceDATCreator(root)
    root.mainloop()


if __name__ == '__main__':
    main()