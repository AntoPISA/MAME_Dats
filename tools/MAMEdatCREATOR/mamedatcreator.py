# Internal version: 0.19
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import threading
import pickle
import re

class MAMEDiffGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("MAMEdat Creator v1.0")
        self.center_window(self.root, 1000, 700)
        
        # Variabili
        self.data_source = tk.StringVar()
        self.data_target = tk.StringVar()
        self.save_folder = tk.StringVar()
        self.auto_save = tk.BooleanVar(value=False)
        # Dizionari per memorizzare i dati caricati
        self.mame_files = {}  # Descrizione -> Percorso file
        self.file_descriptions = {} # Descrizione originale -> Descrizione personalizzata
        self.file_load_times = {} # Descrizione -> Data/ora caricamento
        
        self.current_file = None  # File corrente selezionato
        self.current_description = "" # Descrizione corrente selezionata
        
        # Frame principale
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pulsante per caricare i dati (SOLO questo)
        load_button = ttk.Button(main_frame, text="Load XML File", command=self.load_dat_files)
        load_button.pack(fill=tk.X, pady=5)
        
        # Tabella delle versioni
        self.create_version_table(main_frame)
        
        # Pulsanti di azione (in basso a destra)
        self.create_action_buttons(main_frame)
        
        # Dettagli dati
        self.create_data_details(main_frame)
        
        # Carica i dati dalla cache all'avvio
        self.load_cached_data()
        
    def center_window(self, window, width, height):
        """Centra una finestra sullo schermo."""
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def get_cache_file_path(self):
        """Ottiene il percorso del file di cache."""
        cache_dir = os.path.join(os.path.expanduser("~"), ".mamedatcompare", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, "mame_data_cache.pkl")

    def save_cached_data(self):
        """Salva i dati caricati e le descrizioni in formato compresso per caricamenti successivi"""
        cache_file = self.get_cache_file_path()
        
        # Combina tutti i dati in un dizionario unico da serializzare
        cache_data = {
            'files': self.mame_files,
            'descriptions': self.file_descriptions,
            'load_times': self.file_load_times
        }
        
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(cache_data, f)
            
            # Aggiungi un timestamp per sapere quando è stato creato
            timestamp_file = os.path.join(os.path.dirname(cache_file), "cache_timestamp.txt")
            with open(timestamp_file, "w") as f:
                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as e:
            print(f"Error saving cache: {str(e)}")

    def load_cached_data(self):
        """Carica i dati e le descrizioni dalla cache se disponibili"""
        cache_file = self.get_cache_file_path()
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    cache_data = pickle.load(f)
                
                # Ripristina i dizionari
                self.mame_files = cache_data.get('files', {})
                self.file_descriptions = cache_data.get('descriptions', {})
                self.file_load_times = cache_data.get('load_times', {})
                
                # Popola la tabella con i dati caricati
                for description, file_path in self.mame_files.items():
                    # Usa la descrizione personalizzata se presente, altrimenti quella originale
                    display_desc = self.file_descriptions.get(description, description)
                    # Usa la data di caricamento memorizzata o la data attuale se non presente
                    added_time = self.file_load_times.get(description, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    
                    # Recupera velocemente i conteggi se possibile
                    sets, roms, chds, devices, bioses, mechanicals, savestates = "?", "?", "?", "?", "?", "?", "?"
                    try:
                        tree = ET.parse(file_path)
                        root = tree.getroot()
                        games = root.findall("machine") or root.findall("game")
                        sets = len(games)
                        roms = sum(len(g.findall("rom")) for g in games)
                        chds = sum((len(g.findall("disk")) + len(g.findall("cdrom"))) for g in games)
                        devices = sum(1 for g in games if g.get("isdevice") == "yes")
                        bioses = sum(1 for g in games if g.get("isbios") == "yes" or g.get("bios") == "yes")
                        mechanicals = sum(1 for g in games if g.get("ismechanical") == "yes")
                        savestates = sum(1 for g in games if g.find("driver") is not None and g.find("driver").get("savestate") == "supported")
                    except:
                        pass
                    
                    self.tree.insert("", tk.END, values=(
                        display_desc,
                        str(sets),
                        str(roms),
                        str(chds),
                        str(devices),
                        str(bioses),
                        str(mechanicals),
                        str(savestates),
                        added_time
                    ))
                
                return True
            except Exception as e:
                print(f"Error loading cache: {str(e)}")
                # Se la cache è corrotta, inizializziamo i dizionari vuoti
                self.mame_files = {}
                self.file_descriptions = {}
                self.file_load_times = {}
        else:
            # Se non esiste, inizializziamo i dizionari vuoti
            self.mame_files = {}
            self.file_descriptions = {}
            self.file_load_times = {}
        
        return False

    def create_version_table(self, parent):
        # Frame per la tabella
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Titolo
        ttk.Label(table_frame, text="Data File Mode", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        # Tabella
        columns = ("description", "sets", "roms", "chds", "devices", "bioses", "mechanicals", "savestates", "added")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        
        # Configura le colonne
        self.tree.heading("description", text="Data Description")
        self.tree.heading("sets", text="Sets")
        self.tree.heading("roms", text="ROMs")
        self.tree.heading("chds", text="CHDs")
        self.tree.heading("devices", text="DEVICEs")
        self.tree.heading("bioses", text="BIOSes")
        self.tree.heading("mechanicals", text="MECHANICALs")
        self.tree.heading("savestates", text="SAVESTATES")
        self.tree.heading("added", text="Added")
        
        self.tree.column("description", width=200)
        self.tree.column("sets", width=80, anchor=tk.CENTER)
        self.tree.column("roms", width=80, anchor=tk.CENTER)
        self.tree.column("chds", width=80, anchor=tk.CENTER)
        self.tree.column("devices", width=80, anchor=tk.CENTER)
        self.tree.column("bioses", width=80, anchor=tk.CENTER)
        self.tree.column("mechanicals", width=80, anchor=tk.CENTER)
        self.tree.column("savestates", width=80, anchor=tk.CENTER)
        self.tree.column("added", width=180)
        
        # Barra di scorrimento
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Posizionamento
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Evento di selezione
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        # Evento click destro per il menu contestuale
        self.tree.bind("<Button-3>", self.show_context_menu)
        # Evento tastiera
        self.tree.bind("<F2>", self.rename_entry)
        self.tree.bind("<Delete>", self.delete_entry)
        
        # Menu contestuale
        self.context_menu = tk.Menu(parent, tearoff=0)
        self.context_menu.add_command(label="Rename", command=self.rename_entry)
        self.context_menu.add_command(label="Delete", command=self.delete_entry)
    
    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def rename_entry(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = selected[0]
        old_values = self.tree.item(item, "values")
        old_display_desc = old_values[0]
        
        # Cerca la chiave originale nel dizionario usando il valore visualizzato
        old_desc_key = None
        for key, value in self.file_descriptions.items():
            if value == old_display_desc:
                old_desc_key = key
                break
        # Se non trovata, cerca tra i percorsi
        if old_desc_key is None:
            for key, path in self.mame_files.items():
                if key == old_display_desc:
                    old_desc_key = key
                    break
        
        if old_desc_key is None:
            # Dovrebbe essere impossibile, ma per sicurezza
            messagebox.showerror("Error", "Could not find the original entry to rename.")
            return

        # Finestra di dialogo per rinominare
        dialog = tk.Toplevel(self.root)
        dialog.title("Rename Entry")
        dialog.geometry("400x150")
        self.center_window(dialog, 400, 150) # Centra la finestra
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="New Description:").pack(pady=10)
        entry_var = tk.StringVar(value=old_display_desc)
        entry = ttk.Entry(dialog, textvariable=entry_var, width=50)
        entry.pack(pady=5)
        
        def confirm_rename():
            new_desc = entry_var.get().strip()
            if new_desc and new_desc != old_display_desc:
                # Aggiorna la visualizzazione
                new_values = (new_desc,) + old_values[1:]
                self.tree.item(item, values=new_values)
                
                # Aggiorna i dizionari
                file_path = self.mame_files[old_desc_key]
                # Se la chiave era già personalizzata, aggiorna il dizionario delle descrizioni
                self.file_descriptions[old_desc_key] = new_desc
                
                # Aggiorna la selezione corrente se necessario
                if self.current_description == old_display_desc:
                    self.current_description = new_desc
                    self.current_file = file_path
                    self.create_detail_fields()
                
                # Salva la cache aggiornata
                self.save_cached_data()
            
            dialog.destroy()
        
        ttk.Button(dialog, text="OK", command=confirm_rename).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def delete_entry(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = selected[0]
        display_desc = self.tree.item(item, "values")[0]
        
        # Cerca la chiave originale nel dizionario usando il valore visualizzato
        desc_key_to_remove = None
        for key, value in self.file_descriptions.items():
            if value == display_desc:
                desc_key_to_remove = key
                break
        # Se non trovata, cerca tra i percorsi
        if desc_key_to_remove is None:
            for key, path in self.mame_files.items():
                if key == display_desc:
                    desc_key_to_remove = key
                    break
        
        if desc_key_to_remove is None:
            # Dovrebbe essere impossibile, ma per sicurezza
            messagebox.showerror("Error", "Could not find the original entry to delete.")
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{display_desc}'?"):
            self.tree.delete(item)
            
            # Rimuovi dal dizionario
            del self.mame_files[desc_key_to_remove]
            if desc_key_to_remove in self.file_descriptions:
                del self.file_descriptions[desc_key_to_remove]
            if desc_key_to_remove in self.file_load_times:
                del self.file_load_times[desc_key_to_remove]
            
            # Resetta la selezione corrente se era quella eliminata
            if self.current_description == display_desc:
                self.current_description = ""
                self.current_file = None
                self.create_detail_fields()
            
            # Salva la cache aggiornata
            self.save_cached_data()
    
    def create_action_buttons(self, parent):
        # Frame per i pulsanti (in basso a destra)
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Pulsante "Refresh" (a destra)
        ttk.Button(button_frame, text="Refresh", command=self.refresh_data).pack(side=tk.RIGHT, padx=5)
        
        # Pulsante "Generate DIFFs" (a destra)
        ttk.Button(button_frame, text="Generate DIFFs", command=self.show_save_dialog).pack(side=tk.RIGHT, padx=5)
        
        # Pulsante "Convert DATs" (a destra)
        ttk.Button(button_frame, text="Convert DATs", command=self.show_convert_options).pack(side=tk.RIGHT, padx=5)
        
        # Pulsante "Exit" (a destra)
        ttk.Button(button_frame, text="Exit", command=self.exit_app).pack(side=tk.RIGHT, padx=5)
    
    def create_data_details(self, parent):
        # Frame per i dettagli
        details_frame = ttk.Frame(parent)
        details_frame.pack(fill=tk.X, pady=5)
        
        # Titolo
        ttk.Label(details_frame, text="Data", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        # Frame per i dettagli
        self.details_frame = ttk.Frame(details_frame)
        self.details_frame.pack(fill=tk.X, expand=True)
        
        # Campi dettagli
        self.create_detail_fields()
        
    def create_detail_fields(self):
        # Pulisci il frame
        for widget in self.details_frame.winfo_children():
            widget.destroy()
            
        # Se non è selezionato nulla, mostra un messaggio
        if not self.current_description:
            ttk.Label(self.details_frame, text="Select a DAT file to view details", font=("Arial", 9, "italic")).pack(pady=20)
            return
            
        # Mostra i dettagli della selezione corrente
        # Estrai la versione dal nome
        version = "Unknown"
        if "v" in self.current_description:
            ver_match = re.search(r'v(\d+\.\d+[a-z]?)', self.current_description)
            if ver_match:
                version = ver_match.group(1)
        
        # Recupera i valori dal tree
        for item_id in self.tree.get_children():
            if self.tree.item(item_id, "values")[0] == self.current_description:
                values = self.tree.item(item_id, "values")
                break
        else:
            values = ("", "", "", "", "", "", "", "", "")

        # Campi di testo
        fields = [
            ("Name:", self.current_description),
            ("Description:", self.current_description),
            ("Version:", version),
            ("Sets:", values[1]),
            ("ROMs:", values[2]),
            ("CHDs:", values[3]),
            ("DEVICEs:", values[4]),
            ("BIOSes:", values[5]),
            ("MECHANICALs:", values[6]),
            ("SAVESTATES:", values[7])
        ]
        
        for i, (label, value) in enumerate(fields):
            ttk.Label(self.details_frame, text=label).grid(row=i//3, column=(i%3)*2, sticky=tk.W, padx=5, pady=2)
            ttk.Label(self.details_frame, text=value, font=("Arial", 9, "bold")).grid(row=i//3, column=(i%3)*2+1, sticky=tk.W, padx=5, pady=2)
    
    def load_dat_files(self):
        """Carica i file XML MAME selezionati dall'utente"""
        # Apri la finestra di dialogo per selezionare i file
        file_paths = filedialog.askopenfilenames(
            title="Select MAME XML Files",
            filetypes=[("XML Files", "*.xml"), ("All Files", "*.*")]
        )
        
        if not file_paths:
            return  # L'utente ha annullato
        
        # Carica e analizza i file
        for file_path in file_paths:
            try:
                # Analizza il file XML
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # Estrai la versione dal build attribute di <mame>
                build_attr = root.get("build", "")
                version = "Unknown"
                # Cerca pattern: v?X.XXX, es. "0.285", "v0.285", "0.285b", "0.285 (Jan)30 2026"
                ver_match = re.search(r'v?(\d+\.\d+[a-z]?)', build_attr)
                if ver_match:
                    version = ver_match.group(1)
                
                # Determina il tipo di sistema (MAME, MESS, HBMAME, etc.)
                root_tag_name = root.tag.lower()
                if root_tag_name == "mame":
                    system_type = "MAME"
                elif root_tag_name == "mess":
                    system_type = "MESS"
                else:
                    system_type = root_tag_name.upper()
                
                # Nome del file come fallback
                name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Estrai i giochi: supporta sia <machine> che <game>
                games = root.findall("machine") or root.findall("game")
                sets = len(games)
                
                # Conta ROMs, CHDs, Devices, Samples, Bios, Mechanicals, Savestates
                roms = 0
                chds = 0
                devices = 0
                samples = 0
                bioses = 0
                mechanicals = 0
                savestates = 0
                for game in games:
                    roms += len(game.findall("rom"))
                    chds += len(game.findall("disk")) + len(game.findall("cdrom"))
                    devices += len(game.findall("device"))
                    samples += len(game.findall("sample"))
                    # Conta i giochi che hanno bios="yes" o isbios="yes"
                    if game.get("bios") == "yes" or game.get("isbios") == "yes":
                        bioses += 1
                    # Conta i giochi che hanno isdevice="yes"
                    if game.get("isdevice") == "yes":
                        devices += 1
                    # Conta i giochi che hanno ismechanical="yes"
                    if game.get("ismechanical") == "yes":
                        mechanicals += 1
                    # Conta i giochi con driver.savestate="supported"
                    driver_el = game.find("driver")
                    if driver_el is not None and driver_el.get("savestate") == "supported":
                        savestates += 1
                
                # Costruisci descrizione originale
                if version != "Unknown":
                    original_description = f"{system_type} (v{version})"
                else:
                    original_description = f"{system_type} - {name}"
                
                # Evita duplicati
                counter = 1
                temp_desc = original_description
                while temp_desc in self.mame_files:
                    temp_desc = f"{original_description} ({counter})"
                    counter += 1
                original_description = temp_desc
                
                # Memorizza la data di caricamento
                load_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Memorizza nel dizionario
                self.mame_files[original_description] = file_path
                self.file_load_times[original_description] = load_time
                # La descrizione personalizzata inizialmente è uguale a quella originale
                self.file_descriptions[original_description] = original_description
                
                # Aggiungi alla tabella
                self.tree.insert("", tk.END, values=(
                    original_description,
                    str(sets),
                    str(roms),
                    str(chds),
                    str(devices),
                    str(bioses),
                    str(mechanicals),
                    str(savestates),
                    load_time
                ))

            except ET.ParseError as e:
                messagebox.showerror("XML Parse Error", f"Invalid XML in {os.path.basename(file_path)}:\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {os.path.basename(file_path)}:\n{type(e).__name__}: {str(e)}")
        
        # Salva la cache aggiornata
        self.save_cached_data()
    
    def on_select(self, event):
        # Aggiorna i dettagli in base alla selezione
        selected = self.tree.selection()
        if selected:
            self.current_description = self.tree.item(selected[0])["values"][0]
            # Cerca il percorso associato alla descrizione visualizzata
            file_path = None
            # Cerca prima tra le descrizioni personalizzate
            for key, custom_desc in self.file_descriptions.items():
                if custom_desc == self.current_description:
                    file_path = self.mame_files[key]
                    break
            # Se non trovata, cerca tra le chiavi originali
            if file_path is None:
                file_path = self.mame_files.get(self.current_description)
                
            self.current_file = file_path
        else:
            self.current_description = ""
            self.current_file = None
        self.create_detail_fields()
    
    def show_convert_options(self):
        """Mostra la finestra per scegliere le opzioni di conversione"""
        if not self.current_file:
            messagebox.showwarning("Warning", "Please select a file to convert first.")
            return
        
        # Creazione finestra di dialogo
        dialog = tk.Toplevel(self.root)
        dialog.title("Convert Options")
        self.center_window(dialog, 500, 350) # Centra la finestra
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame principale
        main = ttk.Frame(dialog)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Etichetta
        ttk.Label(main, text="Select conversion types:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        # Variabili per le opzioni
        self.convert_types = {
            "full": tk.BooleanVar(value=False),
            "bioses": tk.BooleanVar(value=False),
            "chds": tk.BooleanVar(value=False),
            "devices": tk.BooleanVar(value=False),
            "roms": tk.BooleanVar(value=False),
            "samples": tk.BooleanVar(value=False),
            "not_mechanical": tk.BooleanVar(value=False)
        }
        
        # Opzioni — ripristinate tutte le 7 conversioni
        options = [
            ("Complete conversion", "full"),
            ("BIOSes only", "bioses"),
            ("CHDs only", "chds"),
            ("DEVICEs only", "devices"),
            ("ROMs only", "roms"),
            ("SAMPLEs only", "samples"),
            ("NOT MECHANICAL only", "not_mechanical")
        ]
        
        for text, key in options:
            ttk.Checkbutton(main, text=text, variable=self.convert_types[key]).pack(anchor=tk.W, pady=2)
        
        # Pulsanti All / None
        all_none_frame = ttk.Frame(main)
        all_none_frame.pack(pady=5)
        ttk.Button(all_none_frame, text="All", command=lambda: [v.set(True) for v in self.convert_types.values()]).pack(side=tk.LEFT, padx=2)
        ttk.Button(all_none_frame, text="None", command=lambda: [v.set(False) for v in self.convert_types.values()]).pack(side=tk.LEFT, padx=2)
        
        # Frame pulsanti
        button_frame = ttk.Frame(main)
        button_frame.pack(pady=10)
        
        def start_conversion():
            # Ottieni le selezioni
            selected_types = [key for key, var in self.convert_types.items() if var.get()]
            if not selected_types:
                messagebox.showwarning("Warning", "Please select at least one conversion type.")
                return
            dialog.destroy()
            self.start_actual_conversion(selected_types)
        
        ttk.Button(button_frame, text="Convert", command=start_conversion).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def start_actual_conversion(self, selected_types):
        """Avvia la conversione vera e propria per i tipi selezionati"""
        if not self.current_file or not self.current_description:
            return
        
        # Determina il nome base del file di output
        base_name = os.path.splitext(os.path.basename(self.current_file))[0]
        version_match = re.search(r'v(\d+\.\d+[a-z]?)', self.current_description)
        version = version_match.group(1) if version_match else "unknown"
        
        type_name_map = {
            "full": "FULL",
            "bioses": "BIOSes",
            "chds": "CHDs",
            "devices": "DEVICEs",
            "roms": "ROMs",
            "samples": "SAMPLEs",
            "not_mechanical": "NOTMECHANICALs"
        }
        
        # Itera attraverso i tipi selezionati
        for convert_type in selected_types:
            suffix = type_name_map.get(convert_type, "Custom")
            output_file = f"{suffix}_{base_name}_v{version}.dat"
            
            # Chiedi all'utente dove salvare
            output_path = filedialog.asksaveasfilename(
                title=f"Save {type_name_map[convert_type]} DAT File",
                defaultextension=".dat",
                initialfile=output_file,
                filetypes=[("DAT Files", "*.dat"), ("All Files", "*.*")]
            )
            
            if not output_path:
                continue  # Passa al prossimo tipo se l'utente annulla
            
            # Mostra un messaggio di progresso
            progress = tk.Toplevel(self.root)
            progress.title("Converting to DAT")
            self.center_window(progress, 300, 100) # Centra la finestra
            progress.geometry("300x100")
            progress.resizable(False, False)
            
            ttk.Label(progress, text=f"Converting to DAT ({type_name_map[convert_type]})...").pack(pady=20)
            progress_bar = ttk.Progressbar(progress, orient=tk.HORIZONTAL, length=250, mode='determinate')
            progress_bar.pack(pady=10)
            
            # Avvia il processo in un thread separato
            threading.Thread(target=self.convert_to_dat_worker_with_type, args=(progress, progress_bar, self.current_file, output_path, convert_type), daemon=True).start()
    
    def convert_to_dat_worker_with_type(self, progress, progress_bar, source_file, output_file, convert_type):
        try:
            # Simula il processo di conversione
            for i in range(101):
                progress_bar['value'] = i
                progress.update_idletasks()
                import time
                time.sleep(0.01)
            
            # Esegui la conversione specifica
            success = False
            if convert_type == "full":
                success = self.convert_to_dat_internal(source_file, output_file)
            elif convert_type == "roms":
                success = self.filter_and_export(source_file, output_file, lambda g: len(g.findall("rom")) > 0, include_roms_only=True)
            elif convert_type == "chds":
                success = self.filter_and_export(source_file, output_file, lambda g: len(g.findall("disk")) > 0, include_chds_only=True)
            elif convert_type == "devices":
                success = self.filter_and_export(source_file, output_file, lambda g: g.get("isdevice") == "yes", include_devices_only=True)
            elif convert_type == "samples":
                success = self.filter_and_export(source_file, output_file, lambda g: g.get("sampleof"), include_samples_only=True)
            elif convert_type == "bioses":
                success = self.filter_and_export(source_file, output_file, lambda g: g.get("isbios") == "yes" or g.get("bios") == "yes", include_bioses_only=True)
            elif convert_type == "not_mechanical":
                success = self.filter_and_export(source_file, output_file, lambda g: g.get("ismechanical") != "yes", include_not_mechanical_only=True)
            
            if success:
                messagebox.showinfo("Success", f"File converted to DAT successfully!\n\n{output_file}")
            else:
                messagebox.showerror("Error", "Failed to convert file to DAT")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            progress.destroy()
    
    def filter_and_export(self, source_file, output_file, filter_func, include_roms_only=False, include_chds_only=False, include_samples_only=False, include_devices_only=False, include_bioses_only=False, include_not_mechanical_only=False):
        """Filtra i giochi e li esporta — versione corretta per ogni tipo"""
        try:
            tree = ET.parse(source_file)
            root = tree.getroot()
            new_root = ET.Element("datafile")
            header = ET.SubElement(new_root, "header")
            ET.SubElement(header, "name").text = "MAME"
            
            # Costruisci la description come: "MAME [tipo] <build>"
            export_label = ""
            if include_roms_only: export_label = "ROMs"
            elif include_chds_only: export_label = "CHDs"
            elif include_devices_only: export_label = "DEVICEs"
            elif include_samples_only: export_label = "SAMPLEs"
            elif include_bioses_only: export_label = "BIOSes"
            elif include_not_mechanical_only: export_label = "NOTMECHANICALs"
            else: export_label = "FULL"
            ET.SubElement(header, "description").text = f"MAME {export_label} {root.get('build', '').strip()}"
            
            ET.SubElement(header, "category").text = "Emulation"
            ET.SubElement(header, "version").text = "1.0"
            ET.SubElement(header, "date").text = datetime.now().strftime("%d/%m/%Y")
            ET.SubElement(header, "author").text = "AntoPISA"
            ET.SubElement(header, "email").text = "progettosnaps@gmail.com"
            ET.SubElement(header, "homepage").text = "http://www.progettosnaps.net/"
            ET.SubElement(header, "url").text = "http://www.progettosnaps.net/dats/MAME"
            ET.SubElement(header, "comment").text = f"Latest editing on {datetime.now().strftime('%d/%m/%Y')} by AntoPISA with MAMEdat Creator v1.0"
            ET.SubElement(header, "clrmamepro")
            
            games = root.findall("machine") or root.findall("game")
            filtered = [g for g in games if filter_func(g)]
            
            for game in filtered:
                # Per NOTMECHANICALs only: escludi macchine con isbios="yes" o isdevice="yes"
                if include_not_mechanical_only:
                    if game.get("isbios") == "yes" or game.get("isdevice") == "yes":
                        continue  # salta questa macchina
                
                # Crea attributi per <machine>
                attrs = {k: v for k, v in game.attrib.items() if k in ["name", "sourcefile", "cloneof", "romof", "sampleof"]}
                # Rimuovi attributi con valore "no"
                attrs = {k: v for k, v in attrs.items() if v != "no"}
                mg = ET.SubElement(new_root, "machine", attrib=attrs)
                
                # Copia solo i tag richiesti per ogni tipo
                for child in game:
                    tag = child.tag
                    if include_roms_only and tag == "rom":
                        nc = ET.SubElement(mg, "rom")
                        for a in ["name", "size", "crc", "sha1"]:
                            if child.get(a):
                                nc.set(a, child.get(a))
                        if child.text:
                            nc.text = child.text
                    elif include_chds_only and tag == "disk":
                        nc = ET.SubElement(mg, "disk")
                        for a in ["name", "sha1", "status"]:
                            if child.get(a):
                                nc.set(a, child.get(a))
                        if child.text:
                            nc.text = child.text
                    elif include_samples_only and tag == "sample":
                        nc = ET.SubElement(mg, "sample")
                        if child.get("name"):
                            nc.set("name", child.get("name"))
                        if child.text:
                            nc.text = child.text
                    elif include_devices_only and tag in ["rom", "biosset", "disk"]:
                        nc = ET.SubElement(mg, tag)
                        for a, v in child.attrib.items():
                            if a in ["name", "size", "crc", "sha1"]:
                                nc.set(a, v)
                        if child.text:
                            nc.text = child.text
                    elif include_bioses_only and tag == "rom":
                        nc = ET.SubElement(mg, "rom")
                        for a, v in child.attrib.items():
                            if a in ["name", "size", "crc", "sha1"]:
                                nc.set(a, v)
                        if child.text:
                            nc.text = child.text
                    elif include_not_mechanical_only and tag in ["description", "year", "manufacturer", "rom", "disk", "sample", "device_ref", "biosset", "driver"]:
                        nc = ET.SubElement(mg, tag)
                        for a, v in child.attrib.items():
                            if v != "no":
                                nc.set(a, v)
                        if child.text:
                            nc.text = child.text
                    # Per "full", copia tutto
                    elif not (include_roms_only or include_chds_only or include_samples_only or include_devices_only or include_bioses_only or include_not_mechanical_only):
                        nc = ET.SubElement(mg, tag)
                        for a, v in child.attrib.items():
                            if v != "no":
                                nc.set(a, v)
                        if child.text:
                            nc.text = child.text
            
            with open(output_file, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n')
                rough = ET.tostring(new_root, encoding='unicode')
                from xml.dom import minidom
                pretty = minidom.parseString(rough).toprettyxml(indent="  ")
                lines = [l for l in pretty.split('\n') if l.strip() and not l.strip().startswith('<?xml')]
                f.write('\n'.join(lines).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error in filtered DAT conversion: {str(e)}")
            return False

    def prettify(self, elem):
        """Restituisce una stringa formattata con indentazione per un elemento ElementTree."""
        from xml.dom import minidom
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        reparsed.normalize()
        pretty_str = reparsed.toprettyxml(indent="  ", newl="\n", encoding=None)
        lines = pretty_str.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('<?xml'):
                start_idx = i
                break
        return '\n'.join(lines[start_idx:]).strip()

    def convert_to_dat_internal(self, source_file, output_file):
        """Converte un file XML in formato DAT standard"""
        try:
            tree = ET.parse(source_file)
            root = tree.getroot()
            new_root = ET.Element("datafile")
            header = ET.SubElement(new_root, "header")
            ET.SubElement(header, "name").text = "MAME"
            ET.SubElement(header, "description").text = root.get("build", "")
            ET.SubElement(header, "category").text = "Emulation"
            ET.SubElement(header, "version").text = "1.0"
            ET.SubElement(header, "date").text = datetime.now().strftime("%d/%m/%Y")
            ET.SubElement(header, "author").text = "AntoPISA"
            ET.SubElement(header, "email").text = "progettosnaps@gmail.com"
            ET.SubElement(header, "homepage").text = "http://www.progettosnaps.net/"
            ET.SubElement(header, "url").text = "http://www.progettosnaps.net/dats/MAME"
            ET.SubElement(header, "comment").text = f"Latest editing on {datetime.now().strftime('%d/%m/%Y')} by AntoPISA with MAMEdat Creator v1.0"
            ET.SubElement(header, "clrmamepro")
            
            games = root.findall("machine") or root.findall("game")
            for game in games:
                attrs = {k: v for k, v in game.attrib.items() if k in ["name", "sourcefile", "cloneof", "romof", "sampleof"]}
                for k, v in game.attrib.items():
                    if k in ["isdevice", "isbios", "ismechanical"] and v == "yes":
                        attrs[k] = "yes"
                mg = ET.SubElement(new_root, "machine", attrib=attrs)
                for child in game:
                    if child.tag in ["description", "year", "manufacturer", "rom", "disk", "sample", "device_ref", "biosset", "driver"]:
                        nc = ET.SubElement(mg, child.tag)
                        for a, v in child.attrib.items():
                            nc.set(a, v)
                        if child.text:
                            nc.text = child.text
            with open(output_file, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n')
                rough = ET.tostring(new_root, encoding='unicode')
                from xml.dom import minidom
                pretty = minidom.parseString(rough).toprettyxml(indent="  ")
                lines = [l for l in pretty.split('\n') if l.strip() and not l.strip().startswith('<?xml')]
                f.write('\n'.join(lines).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error in DAT conversion: {str(e)}")
            return False
    
    def show_save_dialog(self):
        # Controlla se ci sono almeno due file caricati
        if len(self.mame_files) < 2:
            messagebox.showwarning("Warning", "Please load at least two DAT files to proceed.")
            return
            
        # Crea la finestra di dialogo
        dialog = tk.Toplevel(self.root)
        dialog.title("Generate DIFFs")
        self.center_window(dialog, 600, 350) # Centra la finestra
        dialog.grab_set()  # Blocca la finestra principale
        
        # Frame principale del dialogo
        main = ttk.Frame(dialog)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # XML old
        ttk.Label(main, text="XML old:").grid(row=0, column=0, sticky=tk.W, pady=5)
        source_combo = ttk.Combobox(main, textvariable=self.data_source, width=40)
        source_combo.grid(row=0, column=1, sticky=tk.W)
        source_combo['values'] = list(self.file_descriptions.values()) # Usa le descrizioni visualizzate
        if self.current_description:
            source_combo.set(self.current_description)
        else:
            source_combo.current(0)
        
        # XML new
        ttk.Label(main, text="XML new:").grid(row=1, column=0, sticky=tk.W, pady=5)
        target_combo = ttk.Combobox(main, textvariable=self.data_target, width=40)
        target_combo.grid(row=1, column=1, sticky=tk.W)
        target_combo['values'] = list(self.file_descriptions.values()) # Usa le descrizioni visualizzate
        if self.current_description:
            target_combo.set(self.current_description)
        else:
            target_combo.current(0)
        
        # Sezione Data Process
        ttk.Label(main, text="Data Process", font=("Arial", 9, "bold")).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Frame per i processi
        process_frame = ttk.Frame(main)
        process_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W)
        
        # Checkbox per i processi — layout 2 righe × 3 colonne
        self.process_vars = {
            "updated": tk.BooleanVar(),
            "updated_roms": tk.BooleanVar(),
            "updated_chds": tk.BooleanVar(),
            "updated_devices": tk.BooleanVar(),
            "updated_samples": tk.BooleanVar(),
            "updated_bioses": tk.BooleanVar()
        }
        
        # Righe
        ttk.Checkbutton(process_frame, text="Updated", variable=self.process_vars["updated"]).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(process_frame, text="Updated ROMs", variable=self.process_vars["updated_roms"]).grid(row=0, column=1, sticky=tk.W)
        ttk.Checkbutton(process_frame, text="Updated CHDs", variable=self.process_vars["updated_chds"]).grid(row=0, column=2, sticky=tk.W)
        ttk.Checkbutton(process_frame, text="Updated DEVICEs", variable=self.process_vars["updated_devices"]).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(process_frame, text="Updated SAMPLEs", variable=self.process_vars["updated_samples"]).grid(row=1, column=1, sticky=tk.W)
        ttk.Checkbutton(process_frame, text="Updated BIOSes", variable=self.process_vars["updated_bioses"]).grid(row=1, column=2, sticky=tk.W)
        
        # Sezione Data Save Folder
        ttk.Label(main, text="Data Save Folder", font=("Arial", 9, "bold")).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        folder_frame = ttk.Frame(main)
        folder_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Entry(folder_frame, textvariable=self.save_folder, width=40).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).grid(row=0, column=1, padx=5)
        
        # Auto Save
        ttk.Checkbutton(main, text="Auto Save", variable=self.auto_save).grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Label(main, text="Disabled. Each process will ask for save file location.").grid(row=6, column=1, sticky=tk.W)
        
        # Pulsanti del dialogo
        button_frame = ttk.Frame(main)
        button_frame.grid(row=7, column=0, columnspan=2, sticky=tk.E, pady=10)
        
        ttk.Button(button_frame, text="OK", command=lambda: self.process_save_data(dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_folder.set(folder)
    
    def process_save_data(self, dialog):
        # Controlla se è stato selezionato almeno un processo
        processes = [
            "updated", "updated_roms", "updated_chds", "updated_devices", "updated_samples", "updated_bioses"
        ]
        
        selected = any(self.process_vars[p].get() for p in processes)
        if not selected:
            messagebox.showwarning("Warning", "Please select at least one process to execute.")
            return
        
        # Chiudi il dialogo
        dialog.destroy()
        
        # Genera il diff
        self.generate_diff()
    
    def generate_diff(self):
        # Ottieni i valori selezionati
        source_desc = self.data_source.get()
        target_desc = self.data_target.get()
        
        # Cerca la chiave originale corrispondente alla descrizione visualizzata
        source_key = None
        for key, value in self.file_descriptions.items():
            if value == source_desc:
                source_key = key
                break
        # Se non trovata, cerca tra i percorsi
        if source_key is None:
            source_key = source_desc
        
        target_key = None
        for key, value in self.file_descriptions.items():
            if value == target_desc:
                target_key = key
                break
        # Se non trovata, cerca tra i percorsi
        if target_key is None:
            target_key = target_desc
        
        source_file = self.mame_files.get(source_key, "")
        target_file = self.mame_files.get(target_key, "")
        
        if not source_file or not target_file:
            messagebox.showerror("Error", "Invalid source or target file selected.")
            return
        
        # Estrai le versioni
        src_ver = source_desc.split("(v")[1].split(")")[0] if "(v" in source_desc else "0.000"
        tgt_ver = target_desc.split("(v")[1].split(")")[0] if "(v" in target_desc else "0.000"
        
        # Mostra un messaggio di progresso
        progress = tk.Toplevel(self.root)
        progress.title("Generating Data")
        self.center_window(progress, 300, 100) # Centra la finestra
        progress.geometry("300x100")
        progress.resizable(False, False)
        
        ttk.Label(progress, text=f"Generating data for {src_ver} to {tgt_ver}...").pack(pady=20)
        progress_bar = ttk.Progressbar(progress, orient=tk.HORIZONTAL, length=250, mode='determinate')
        progress_bar.pack(pady=10)
        
        # Avvia il processo in un thread separato
        threading.Thread(target=self.generate_diff_worker, args=(progress, progress_bar, source_file, target_file, src_ver, tgt_ver), daemon=True).start()
    
    def generate_diff_worker(self, progress, progress_bar, source_file, target_file, src_ver, tgt_ver):
        try:
            # Simula il processo di conversione
            for i in range(101):
                progress_bar['value'] = i
                progress.update_idletasks()
                import time
                time.sleep(0.01)
            
            # Determina quali processi sono stati selezionati
            processes = {
                "updated": self.process_vars["updated"].get(),
                "updated_roms": self.process_vars["updated_roms"].get(),
                "updated_chds": self.process_vars["updated_chds"].get(),
                "updated_devices": self.process_vars["updated_devices"].get(),
                "updated_samples": self.process_vars["updated_samples"].get(),
                "updated_bioses": self.process_vars["updated_bioses"].get()
            }
            
            # Elabora in base ai processi selezionati
            results = []
            
            if processes["updated"]:
                output_file = f"MAME (v{src_ver}) to MAME (v{tgt_ver}).dat"
                if self.generate_updated_diff(source_file, target_file, output_file, src_ver, tgt_ver):
                    results.append(output_file)
            
            if processes["updated_roms"]:
                output_file = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - ROMs.dat"
                if self.generate_updated_roms_diff(source_file, target_file, output_file, src_ver, tgt_ver):
                    results.append(output_file)
            
            if processes["updated_chds"]:
                output_file = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - CHDs.dat"
                if self.generate_updated_chds_diff(source_file, target_file, output_file, src_ver, tgt_ver):
                    results.append(output_file)
            
            if processes["updated_devices"]:
                output_file = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - DEVICEs.dat"
                if self.generate_updated_devices_diff(source_file, target_file, output_file, src_ver, tgt_ver):
                    results.append(output_file)
            
            if processes["updated_samples"]:
                output_file = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - SAMPLEs.dat"
                if self.generate_updated_samples_diff(source_file, target_file, output_file, src_ver, tgt_ver):
                    results.append(output_file)
            
            if processes["updated_bioses"]:
                output_file = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - BIOSes.dat"
                if self.generate_updated_bioses_diff(source_file, target_file, output_file, src_ver, tgt_ver):
                    results.append(output_file)
            
            if results:
                messagebox.showinfo("Success", f"Files generated successfully!\n\n" + "\n".join(results))
            else:
                messagebox.showinfo("Info", "No processes were selected or all failed.")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            progress.destroy()
    
    def generate_updated_diff(self, source_file, target_file, output_file, src_ver, tgt_ver):
        """Genera un DAT con TUTTE LE DIFFERENZE (macchina per macchina)"""
        try:
            tree_old = ET.parse(source_file)
            tree_new = ET.parse(target_file)
            root_old = tree_old.getroot()
            root_new = tree_new.getroot()
            
            # Crea nuovo albero
            new_root = ET.Element("datafile")
            header = ET.SubElement(new_root, "header")
            ET.SubElement(header, "name").text = "MAME"
            ET.SubElement(header, "description").text = f"MAME (v{src_ver}) to MAME (v{tgt_ver})"
            ET.SubElement(header, "category").text = "Emulation"
            ET.SubElement(header, "date").text = datetime.now().strftime("%d/%m/%Y")
            ET.SubElement(header, "author").text = "AntoPISA"
            ET.SubElement(header, "email").text = "progettosnaps@gmail.com"
            ET.SubElement(header, "homepage").text = "http://www.progettosnaps.net/"
            ET.SubElement(header, "url").text = "http://www.progettosnaps.net/dats/MAME"
            ET.SubElement(header, "comment").text = f"Latest editing on {datetime.now().strftime('%d/%m/%Y')} by AntoPISA with MAMEdat Creator v1.0"
            ET.SubElement(header, "clrmamepro")
            
            # Ottieni giochi
            old_games = {game.get("name"): game for game in root_old.findall("machine") or root_old.findall("game")}
            new_games = {game.get("name"): game for game in root_new.findall("machine") or root_new.findall("game")}
            
            # Trova differenze
            all_names = set(old_games.keys()).union(set(new_games.keys()))
            for name in all_names:
                old_game = old_games.get(name)
                new_game = new_games.get(name)
                
                # Nuovo gioco
                if new_game is not None and old_game is None:
                    mg = self._create_machine_element(new_game, include_all=True)
                    new_root.append(mg)
                # Modificato
                elif old_game is not None and new_game is not None and self._game_differs(old_game, new_game):
                    mg = self._create_machine_element(new_game, include_all=True)
                    new_root.append(mg)
            
            # Non scrivere se vuoto
            if len(new_root.findall("machine")) == 0:
                return False
            
            # Applica cartella di salvataggio
            if self.save_folder.get():
                output_file = os.path.join(self.save_folder.get(), os.path.basename(output_file))
            
            # Scrivi
            with open(output_file, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n')
                rough = ET.tostring(new_root, encoding='unicode')
                from xml.dom import minidom
                pretty = minidom.parseString(rough).toprettyxml(indent="  ")
                lines = [l for l in pretty.split('\n') if l.strip() and not l.strip().startswith('<?xml')]
                f.write('\n'.join(lines).encode('utf-8'))
            
            return True
        except Exception as e:
            print(f"Error in generate_updated_diff: {e}")
            return False
    
    def _create_machine_element(self, game, include_all=False):
        """Crea un <machine> con solo attributi validi e tag rilevanti"""
        attrs = {k: v for k, v in game.attrib.items() if v != "no"}
        # Rimuovi isbios="yes", isdevice="yes", ismechanical="yes" se non richiesti
        for k, v in list(attrs.items()):
            if k in ["isbios", "isdevice", "ismechanical"] and v == "yes":
                del attrs[k]
        
        mg = ET.Element("machine", attrib=attrs)
        
        # Copia solo tag rilevanti
        for child in game:
            tag = child.tag
            if tag in ["description", "year", "manufacturer"]:
                nc = ET.SubElement(mg, tag)
                for a, v in child.attrib.items():
                    if v != "no":
                        nc.set(a, v)
                if child.text:
                    nc.text = child.text
            elif tag == "rom":
                nc = ET.SubElement(mg, "rom")
                for a in ["name", "size", "crc", "sha1"]:
                    if child.get(a):
                        nc.set(a, child.get(a))
                if child.text:
                    nc.text = child.text
            elif tag == "disk":
                nc = ET.SubElement(mg, "disk")
                for a in ["name", "sha1", "status"]:
                    if child.get(a):
                        nc.set(a, child.get(a))
                if child.text:
                    nc.text = child.text
            elif tag == "sample":
                nc = ET.SubElement(mg, "sample")
                if child.get("name"):
                    nc.set("name", child.get("name"))
                if child.text:
                    nc.text = child.text
            elif tag == "biosset" and include_all:
                nc = ET.SubElement(mg, "biosset")
                for a, v in child.attrib.items():
                    if v != "no":
                        nc.set(a, v)
                if child.text:
                    nc.text = child.text
            elif tag == "device_ref" and include_all:
                nc = ET.SubElement(mg, "device_ref")
                for a, v in child.attrib.items():
                    if v != "no":
                        nc.set(a, v)
                if child.text:
                    nc.text = child.text
        
        return mg
    
    def _game_differs(self, old_game, new_game):
        """Controlla se due giochi differiscono in ROM, CHD, SAMPLE, ecc."""
        # Confronta ROM
        if self._rom_lists_differ(old_game, new_game):
            return True
        # Confronta DISK
        if self._disk_lists_differ(old_game, new_game):
            return True
        # Confronta SAMPLE
        if self._sample_lists_differ(old_game, new_game):
            return True
        # Confronta attributi base
        for attr in ["description", "year", "manufacturer"]:
            o = old_game.find(attr)
            n = new_game.find(attr)
            if (o is None) != (n is None):
                return True
            if o is not None and n is not None and o.text != n.text:
                return True
        return False
    
    def _rom_lists_differ(self, old_game, new_game):
        old_roms = {(r.get("name"), r.get("size"), r.get("crc"), r.get("sha1")) for r in old_game.findall("rom")}
        new_roms = {(r.get("name"), r.get("size"), r.get("crc"), r.get("sha1")) for r in new_game.findall("rom")}
        return old_roms != new_roms
    
    def _disk_lists_differ(self, old_game, new_game):
        old_disks = {(r.get("name"), r.get("sha1")) for r in old_game.findall("disk")}
        new_disks = {(r.get("name"), r.get("sha1")) for r in new_game.findall("disk")}
        return old_disks != new_disks
    
    def _sample_lists_differ(self, old_game, new_game):
        old_samples = {r.get("name") for r in old_game.findall("sample")}
        new_samples = {r.get("name") for r in new_game.findall("sample")}
        return old_samples != new_samples
    
    def generate_updated_roms_diff(self, source_file, target_file, output_file, src_ver, tgt_ver):
        try:
            tree_old = ET.parse(source_file)
            tree_new = ET.parse(target_file)
            root_old = tree_old.getroot()
            root_new = tree_new.getroot()
            
            new_root = ET.Element("datafile")
            header = ET.SubElement(new_root, "header")
            ET.SubElement(header, "name").text = "MAME"
            ET.SubElement(header, "description").text = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - ROMs"
            ET.SubElement(header, "category").text = "Emulation"
            ET.SubElement(header, "date").text = datetime.now().strftime("%d/%m/%Y")
            ET.SubElement(header, "author").text = "AntoPISA"
            ET.SubElement(header, "email").text = "progettosnaps@gmail.com"
            ET.SubElement(header, "homepage").text = "http://www.progettosnaps.net/"
            ET.SubElement(header, "url").text = "http://www.progettosnaps.net/dats/MAME"
            ET.SubElement(header, "comment").text = f"Latest editing on {datetime.now().strftime('%d/%m/%Y')} by AntoPISA with MAMEdat Creator v1.0"
            ET.SubElement(header, "clrmamepro")
            
            old_games = {game.get("name"): game for game in root_old.findall("machine") or root_old.findall("game")}
            new_games = {game.get("name"): game for game in root_new.findall("machine") or root_new.findall("game")}
            
            all_names = set(old_games.keys()).union(set(new_games.keys()))
            for name in all_names:
                old_game = old_games.get(name)
                new_game = new_games.get(name)
                if new_game is not None and (old_game is None or self._rom_lists_differ(old_game, new_game)):
                    mg = ET.Element("machine", attrib={k: v for k, v in new_game.attrib.items() if v != "no" and k not in ["isbios", "isdevice", "ismechanical"]})
                    for rom in new_game.findall("rom"):
                        nc = ET.SubElement(mg, "rom")
                        for a in ["name", "size", "crc", "sha1"]:
                            if rom.get(a):
                                nc.set(a, rom.get(a))
                    new_root.append(mg)
            
            if len(new_root.findall("machine")) == 0:
                return False
            
            # Applica cartella di salvataggio
            if self.save_folder.get():
                output_file = os.path.join(self.save_folder.get(), os.path.basename(output_file))
            
            with open(output_file, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n')
                rough = ET.tostring(new_root, encoding='unicode')
                from xml.dom import minidom
                pretty = minidom.parseString(rough).toprettyxml(indent="  ")
                lines = [l for l in pretty.split('\n') if l.strip() and not l.strip().startswith('<?xml')]
                f.write('\n'.join(lines).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error in generate_updated_roms_diff: {e}")
            return False
    
    def generate_updated_chds_diff(self, source_file, target_file, output_file, src_ver, tgt_ver):
        try:
            tree_old = ET.parse(source_file)
            tree_new = ET.parse(target_file)
            root_old = tree_old.getroot()
            root_new = tree_new.getroot()
            
            new_root = ET.Element("datafile")
            header = ET.SubElement(new_root, "header")
            ET.SubElement(header, "name").text = "MAME"
            ET.SubElement(header, "description").text = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - CHDs"
            ET.SubElement(header, "category").text = "Emulation"
            ET.SubElement(header, "date").text = datetime.now().strftime("%d/%m/%Y")
            ET.SubElement(header, "author").text = "AntoPISA"
            ET.SubElement(header, "email").text = "progettosnaps@gmail.com"
            ET.SubElement(header, "homepage").text = "http://www.progettosnaps.net/"
            ET.SubElement(header, "url").text = "http://www.progettosnaps.net/dats/MAME"
            ET.SubElement(header, "comment").text = f"Latest editing on {datetime.now().strftime('%d/%m/%Y')} by AntoPISA with MAMEdat Creator v1.0"
            ET.SubElement(header, "clrmamepro")
            
            old_games = {game.get("name"): game for game in root_old.findall("machine") or root_old.findall("game")}
            new_games = {game.get("name"): game for game in root_new.findall("machine") or root_new.findall("game")}
            
            all_names = set(old_games.keys()).union(set(new_games.keys()))
            for name in all_names:
                old_game = old_games.get(name)
                new_game = new_games.get(name)
                if new_game is not None and (old_game is None or self._disk_lists_differ(old_game, new_game)):
                    mg = ET.Element("machine", attrib={k: v for k, v in new_game.attrib.items() if v != "no" and k not in ["isbios", "isdevice", "ismechanical"]})
                    for disk in new_game.findall("disk"):
                        nc = ET.SubElement(mg, "disk")
                        for a, v in disk.attrib.items():
                            if a in ["name", "sha1", "status"]:
                                nc.set(a, v)
                    new_root.append(mg)
            
            if len(new_root.findall("machine")) == 0:
                return False
            
            # Applica cartella di salvataggio
            if self.save_folder.get():
                output_file = os.path.join(self.save_folder.get(), os.path.basename(output_file))
            
            with open(output_file, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n')
                rough = ET.tostring(new_root, encoding='unicode')
                from xml.dom import minidom
                pretty = minidom.parseString(rough).toprettyxml(indent="  ")
                lines = [l for l in pretty.split('\n') if l.strip() and not l.strip().startswith('<?xml')]
                f.write('\n'.join(lines).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error in generate_updated_chds_diff: {e}")
            return False
    
    def generate_updated_devices_diff(self, source_file, target_file, output_file, src_ver, tgt_ver):
        try:
            tree_old = ET.parse(source_file)
            tree_new = ET.parse(target_file)
            root_old = tree_old.getroot()
            root_new = tree_new.getroot()
            
            new_root = ET.Element("datafile")
            header = ET.SubElement(new_root, "header")
            ET.SubElement(header, "name").text = "MAME"
            ET.SubElement(header, "description").text = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - DEVICEs"
            ET.SubElement(header, "category").text = "Emulation"
            ET.SubElement(header, "date").text = datetime.now().strftime("%d/%m/%Y")
            ET.SubElement(header, "author").text = "AntoPISA"
            ET.SubElement(header, "email").text = "progettosnaps@gmail.com"
            ET.SubElement(header, "homepage").text = "http://www.progettosnaps.net/"
            ET.SubElement(header, "url").text = "http://www.progettosnaps.net/dats/MAME"
            ET.SubElement(header, "comment").text = f"Latest editing on {datetime.now().strftime('%d/%m/%Y')} by AntoPISA with MAMEdat Creator v1.0"
            ET.SubElement(header, "clrmamepro")
            
            old_devices = {game.get("name"): game for game in root_old.findall("machine") or root_old.findall("game") if game.get("isdevice") == "yes"}
            new_devices = {game.get("name"): game for game in root_new.findall("machine") or root_new.findall("game") if game.get("isdevice") == "yes"}
            
            all_names = set(old_devices.keys()).union(set(new_devices.keys()))
            for name in all_names:
                old_device = old_devices.get(name)
                new_device = new_devices.get(name)
                if new_device is not None and (old_device is None or self._rom_lists_differ(old_device, new_device)):
                    attrs = {k: v for k, v in new_device.attrib.items() if v != "no" and k not in ["isbios", "ismechanical"]}
                    mg = ET.Element("machine", attrib=attrs)
                    # Copia rom, biosset, disk se presenti
                    for rom in new_device.findall("rom"):
                        nc = ET.SubElement(mg, "rom")
                        for a, v in rom.attrib.items():
                            if a in ["name", "size", "crc", "sha1"]:
                                nc.set(a, v)
                        if rom.text:
                            nc.text = rom.text
                    for biosset in new_device.findall("biosset"):
                        nc = ET.SubElement(mg, "biosset")
                        for a, v in biosset.attrib.items():
                            if v != "no":
                                nc.set(a, v)
                        if biosset.text:
                            nc.text = biosset.text
                    for disk in new_device.findall("disk"):
                        nc = ET.SubElement(mg, "disk")
                        for a, v in disk.attrib.items():
                            if a in ["name", "sha1", "status"]:
                                nc.set(a, v)
                        if disk.text:
                            nc.text = disk.text
                    new_root.append(mg)
            
            if len(new_root.findall("machine")) == 0:
                return False
            
            # Applica cartella di salvataggio
            if self.save_folder.get():
                output_file = os.path.join(self.save_folder.get(), os.path.basename(output_file))
            
            with open(output_file, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n')
                rough = ET.tostring(new_root, encoding='unicode')
                from xml.dom import minidom
                pretty = minidom.parseString(rough).toprettyxml(indent="  ")
                lines = [l for l in pretty.split('\n') if l.strip() and not l.strip().startswith('<?xml')]
                f.write('\n'.join(lines).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error in generate_updated_devices_diff: {e}")
            return False

    def generate_updated_samples_diff(self, source_file, target_file, output_file, src_ver, tgt_ver):
        try:
            tree_old = ET.parse(source_file)
            tree_new = ET.parse(target_file)
            root_old = tree_old.getroot()
            root_new = tree_new.getroot()
            
            new_root = ET.Element("datafile")
            header = ET.SubElement(new_root, "header")
            ET.SubElement(header, "name").text = "MAME"
            ET.SubElement(header, "description").text = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - SAMPLEs"
            ET.SubElement(header, "category").text = "Emulation"
            ET.SubElement(header, "date").text = datetime.now().strftime("%d/%m/%Y")
            ET.SubElement(header, "author").text = "AntoPISA"
            ET.SubElement(header, "email").text = "progettosnaps@gmail.com"
            ET.SubElement(header, "homepage").text = "http://www.progettosnaps.net/"
            ET.SubElement(header, "url").text = "http://www.progettosnaps.net/dats/MAME"
            ET.SubElement(header, "comment").text = f"Latest editing on {datetime.now().strftime('%d/%m/%Y')} by AntoPISA with MAMEdat Creator v1.0"
            ET.SubElement(header, "clrmamepro")
            
            old_games = {game.get("name"): game for game in root_old.findall("machine") or root_old.findall("game")}
            new_games = {game.get("name"): game for game in root_new.findall("machine") or root_new.findall("game")}
            
            all_names = set(old_games.keys()).union(set(new_games.keys()))
            for name in all_names:
                old_game = old_games.get(name)
                new_game = new_games.get(name)
                if new_game is not None and (old_game is None or self._sample_lists_differ(old_game, new_game)):
                    attrs = {k: v for k, v in new_game.attrib.items() if v != "no" and k not in ["isbios", "isdevice", "ismechanical"]}
                    mg = ET.Element("machine", attrib=attrs)
                    # Copia SOLO <sample name>
                    for sample in new_game.findall("sample"):
                        nc = ET.SubElement(mg, "sample")
                        if sample.get("name"):
                            nc.set("name", sample.get("name"))
                        if sample.text:
                            nc.text = sample.text
                    new_root.append(mg)
            
            if len(new_root.findall("machine")) == 0:
                return False
            
            # Applica cartella di salvataggio
            if self.save_folder.get():
                output_file = os.path.join(self.save_folder.get(), os.path.basename(output_file))
            
            with open(output_file, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n')
                rough = ET.tostring(new_root, encoding='unicode')
                from xml.dom import minidom
                pretty = minidom.parseString(rough).toprettyxml(indent="  ")
                lines = [l for l in pretty.split('\n') if l.strip() and not l.strip().startswith('<?xml')]
                f.write('\n'.join(lines).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error in generate_updated_samples_diff: {e}")
            return False

    def generate_updated_bioses_diff(self, source_file, target_file, output_file, src_ver, tgt_ver):
        try:
            tree_old = ET.parse(source_file)
            tree_new = ET.parse(target_file)
            root_old = tree_old.getroot()
            root_new = tree_new.getroot()
            
            new_root = ET.Element("datafile")
            header = ET.SubElement(new_root, "header")
            ET.SubElement(header, "name").text = "MAME"
            ET.SubElement(header, "description").text = f"MAME (v{src_ver}) to MAME (v{tgt_ver}) - BIOSes"
            ET.SubElement(header, "category").text = "Emulation"
            ET.SubElement(header, "date").text = datetime.now().strftime("%d/%m/%Y")
            ET.SubElement(header, "author").text = "AntoPISA"
            ET.SubElement(header, "email").text = "progettosnaps@gmail.com"
            ET.SubElement(header, "homepage").text = "http://www.progettosnaps.net/"
            ET.SubElement(header, "url").text = "http://www.progettosnaps.net/dats/MAME"
            ET.SubElement(header, "comment").text = f"Latest editing on {datetime.now().strftime('%d/%m/%Y')} by AntoPISA with MAMEdat Creator v1.0"
            ET.SubElement(header, "clrmamepro")
            
            old_bioses = {game.get("name"): game for game in root_old.findall("machine") or root_old.findall("game") if game.get("isbios") == "yes" or game.get("bios") == "yes"}
            new_bioses = {game.get("name"): game for game in root_new.findall("machine") or root_new.findall("game") if game.get("isbios") == "yes" or game.get("bios") == "yes"}
            
            all_names = set(old_bioses.keys()).union(set(new_bioses.keys()))
            for name in all_names:
                old_bios = old_bioses.get(name)
                new_bios = new_bioses.get(name)
                if new_bios is not None and (old_bios is None or self._rom_lists_differ(old_bios, new_bios)):
                    attrs = {k: v for k, v in new_bios.attrib.items() if v != "no" and k not in ["isdevice", "ismechanical"]}
                    mg = ET.Element("machine", attrib=attrs)
                    # Copia SOLO <rom> (senza isbios="yes" nell'elemento machine)
                    for rom in new_bios.findall("rom"):
                        nc = ET.SubElement(mg, "rom")
                        for a, v in rom.attrib.items():
                            if a in ["name", "size", "crc", "sha1"]:
                                nc.set(a, v)
                        if rom.text:
                            nc.text = rom.text
                    new_root.append(mg)
            
            if len(new_root.findall("machine")) == 0:
                return False
            
            # Applica cartella di salvataggio
            if self.save_folder.get():
                output_file = os.path.join(self.save_folder.get(), os.path.basename(output_file))
            
            with open(output_file, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">\n\n')
                rough = ET.tostring(new_root, encoding='unicode')
                from xml.dom import minidom
                pretty = minidom.parseString(rough).toprettyxml(indent="  ")
                lines = [l for l in pretty.split('\n') if l.strip() and not l.strip().startswith('<?xml')]
                f.write('\n'.join(lines).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error in generate_updated_bioses_diff: {e}")
            return False

    def compare_versions(self):
        if len(self.mame_files) < 2:
            messagebox.showwarning("Warning", "Please load at least two DAT files to compare.")
            return
            
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a version to compare.")
            return
            
        # Mostra un messaggio di confronto
        messagebox.showinfo("Compare", "Comparing versions...")

    def refresh_data(self):
        # Non facciamo nulla per il refresh, a meno che non vogliamo ricaricare i dati
        pass

    def exit_app(self):
        # Prima di uscire, salva la cache aggiornata
        self.save_cached_data()
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MAMEDiffGenerator(root)
    root.mainloop()