#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import configparser
from typing import Dict, List, Tuple, Optional
import threading

# Assicurati di installare: pip install packaging
try:
    from packaging import version as packaging_version
except ImportError:
    messagebox.showerror("Errore", "Richiesto il pacchetto 'packaging'.\nInstalla con: pip install packaging")
    sys.exit(1)


class AttributeSelectionDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.selected_attributes = {}
        
        # Lista di tutti gli attributi disponibili
        self.available_attributes = {
            'sourcefile': 'Sourcefile (attributo del tag game)',
            'mameID': 'MAME ID (info)',
            'machine_type': 'Machine Type (info)',
            'add_by': 'Add By (info)',
            'add_in': 'Add In (info)',
            'sound_channels': 'Sound Channels',
            'video_screen': 'Video Screen',
            'orientation': 'Video Orientation',
            'input_players': 'Input Players',
            'driver_status': 'Driver Status',
            'driver_emulation': 'Driver Emulation',
            'driver_color': 'Driver Color',
            'driver_sound': 'Driver Sound',
            'driver_graphic': 'Driver Graphic',
            'driver_savestate': 'Driver Savestate'
        }
        
        self.create_dialog()
    
    def create_dialog(self):
        """Crea il dialog per la selezione degli attributi"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Selezione Attributi da Modificare")
        self.dialog.geometry("600x650")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centra il dialog
        self.dialog.geometry("+%d+%d" % (self.parent.winfo_rootx() + 100, self.parent.winfo_rooty() + 50))
        
        # Frame principale
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        ttk.Label(main_frame, text="Seleziona gli attributi da modificare/aggiungere:", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        # Frame per le checkbox
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea le checkbox per ogni attributo
        self.checkbox_vars = {}
        for attr_key, attr_desc in self.available_attributes.items():
            var = tk.BooleanVar(value=True)  # Selezionati per default
            self.checkbox_vars[attr_key] = var
            ttk.Checkbutton(checkbox_frame, text=attr_desc, variable=var).pack(anchor=tk.W, pady=2)
        
        # Pulsanti di controllo
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=10)
        
        ttk.Button(control_frame, text="Seleziona Tutto", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Deseleziona Tutto", command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        
        # Frame per i pulsanti finali
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annulla", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
    
    def select_all(self):
        """Seleziona tutti gli attributi"""
        for var in self.checkbox_vars.values():
            var.set(True)
    
    def deselect_all(self):
        """Deseleziona tutti gli attributi"""
        for var in self.checkbox_vars.values():
            var.set(False)
    
    def on_ok(self):
        """Conferma la selezione"""
        self.selected_attributes = {
            attr: var.get() for attr, var in self.checkbox_vars.items()
        }
        self.result = True
        self.dialog.destroy()
    
    def on_cancel(self):
        """Annulla la selezione"""
        self.result = False
        self.dialog.destroy()
    
    def show(self):
        """Mostra il dialog e restituisce il risultato"""
        self.dialog.wait_window()
        return self.result, self.selected_attributes


class MAMEXMLProcessorGUI:
    def __init__(self):
        self.games_data = {}
        self.xml2_games_data = {}
        self.duplicates = {}
        self.not_modified_games = []
        self.modify_driver = True
        self.selected_attributes = {}
        self.xml_folder = ""
        self.txt_folder = ""
        self.xml2_folder = ""
        
        # Crea la finestra principale
        self.root = tk.Tk()
        self.root.title("MAME XML Processor v2.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Carica la configurazione
        self.load_config()
        
        # Crea l'interfaccia
        self.create_widgets()
        
        # Messaggi iniziali (dopo la creazione dell'interfaccia)
        self.log_message("=== MAME XML Processor GUI v2.0 ===")
        self.log_message("Seleziona i file e clicca 'Elabora XML' per iniziare")
        
        # Log della configurazione caricata
        if self.xml_folder:
            self.log_message(f"Cartella XML configurata: {self.xml_folder}")
        if self.txt_folder:
            self.log_message(f"Cartella TXT configurata: {self.txt_folder}")
        if self.xml2_folder:
            self.log_message(f"Cartella XML2 configurata: {self.xml2_folder}")
        
    def load_config(self):
        """Carica la configurazione dal file config.ini"""
        config = configparser.ConfigParser()
        config_file = "config.ini"
        
        if os.path.exists(config_file):
            try:
                config.read(config_file, encoding='utf-8')
                if 'Folders' in config:
                    self.xml_folder = config['Folders'].get('xml_folder', '')
                    self.txt_folder = config['Folders'].get('txt_folder', '')
                    self.xml2_folder = config['Folders'].get('xml2_folder', '')
            except Exception as e:
                print(f"Errore nel caricamento della configurazione: {e}")
        
        if not os.path.exists(config_file):
            # Crea un file di configurazione di esempio
            self.create_sample_config()
    
    def create_sample_config(self):
        """Crea un file config.ini di esempio"""
        config = configparser.ConfigParser()
        config['Folders'] = {
            'xml_folder': 'X:/MAME/archives/',
            'txt_folder': 'C:/MAME/MAME_XML_Updater/',
            'xml2_folder': 'X:/MAME/archives/mame.xml'
        }
        
        try:
            with open('config.ini', 'w', encoding='utf-8') as f:
                config.write(f)
        except Exception as e:
            print(f"Errore nella creazione del config.ini: {e}")
    
    def create_widgets(self):
        """Crea l'interfaccia grafica"""
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configura il ridimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
        # Titolo
        title_label = ttk.Label(main_frame, text="MAME XML Processor v1.0d", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Selezione file XML principale
        ttk.Label(main_frame, text="File XML MAME (principale):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.xml_var = tk.StringVar()
        self.xml_entry = ttk.Entry(main_frame, textvariable=self.xml_var, width=50)
        self.xml_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Sfoglia", command=self.browse_xml_file).grid(row=1, column=2, pady=5)
        
        # Selezione file XML di riferimento
        ttk.Label(main_frame, text="File XML di riferimento (opzionale):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.xml2_var = tk.StringVar()
        self.xml2_entry = ttk.Entry(main_frame, textvariable=self.xml2_var, width=50)
        self.xml2_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Sfoglia", command=self.browse_xml2_file).grid(row=2, column=2, pady=5)
        
        # Selezione file dati
        ttk.Label(main_frame, text="File dati TXT:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.txt_var = tk.StringVar()
        self.txt_entry = ttk.Entry(main_frame, textvariable=self.txt_var, width=50)
        self.txt_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Sfoglia", command=self.browse_txt_file).grid(row=3, column=2, pady=5)
        
        # Opzione modifica driver
        self.driver_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Modifica anche i valori dei driver", 
                       variable=self.driver_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.process_button = ttk.Button(button_frame, text="Elabora XML", command=self.start_processing)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Pulisci Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Esci", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # Barra di progresso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Separatore
        ttk.Separator(main_frame, orient='horizontal').grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Area di log
        ttk.Label(main_frame, text="Log:").grid(row=8, column=0, sticky=(tk.W, tk.N), pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=20, width=100)
        self.log_text.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
    
    def log_message(self, message):
        """Aggiunge un messaggio al log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Pulisce il log"""
        self.log_text.delete(1.0, tk.END)
    
    def browse_xml_file(self):
        """Apre il dialog per selezionare il file XML principale"""
        initial_dir = self.xml_folder if os.path.exists(self.xml_folder) else ""
        filename = filedialog.askopenfilename(
            title="Seleziona file XML MAME principale",
            initialdir=initial_dir,
            filetypes=[("File XML", "*.xml"), ("Tutti i file", "*.*")]
        )
        if filename:
            self.xml_var.set(filename)
    
    def browse_xml2_file(self):
        """Apre il dialog per selezionare il file XML di riferimento"""
        initial_dir = os.path.dirname(self.xml2_folder) if os.path.exists(os.path.dirname(self.xml2_folder)) else ""
        filename = filedialog.askopenfilename(
            title="Seleziona file XML di riferimento",
            initialdir=initial_dir,
            filetypes=[("File XML", "*.xml"), ("Tutti i file", "*.*")]
        )
        if filename:
            self.xml2_var.set(filename)
    
    def browse_txt_file(self):
        """Apre il dialog per selezionare il file dati"""
        initial_dir = self.txt_folder if os.path.exists(self.txt_folder) else ""
        filename = filedialog.askopenfilename(
            title="Seleziona file dati TXT",
            initialdir=initial_dir,
            filetypes=[("File di testo", "*.txt"), ("Tutti i file", "*.*")]
        )
        if filename:
            self.txt_var.set(filename)
    
    def start_processing(self):
        """Avvia l'elaborazione in un thread separato"""
        xml_file = self.xml_var.get().strip()
        txt_file = self.txt_var.get().strip()
        xml2_file = self.xml2_var.get().strip()
        
        if not xml_file or not txt_file:
            messagebox.showerror("Errore", "Seleziona almeno il file XML principale e il file dati TXT")
            return
        
        if not os.path.exists(xml_file):
            messagebox.showerror("Errore", "File XML principale non trovato")
            return
        
        if not os.path.exists(txt_file):
            messagebox.showerror("Errore", "File dati non trovato")
            return
        
        if xml2_file and not os.path.exists(xml2_file):
            messagebox.showerror("Errore", "File XML di riferimento non trovato")
            return
        
        # Mostra il dialog per la selezione degli attributi
        attr_dialog = AttributeSelectionDialog(self.root)
        result, selected_attrs = attr_dialog.show()
        
        if not result:
            self.log_message("Operazione annullata dall'utente")
            return
        
        self.selected_attributes = selected_attrs
        
        # Disabilita il pulsante e avvia la barra di progresso
        self.process_button.config(state='disabled')
        self.progress.start()
        
        # Avvia l'elaborazione in un thread separato
        self.modify_driver = self.driver_var.get()
        thread = threading.Thread(target=self.process_files, args=(xml_file, txt_file, xml2_file))
        thread.daemon = True
        thread.start()
    
    def process_files(self, xml_file, txt_file, xml2_file):
        """Elabora i file (eseguito in un thread separato)"""
        try:
            # Reset dei dati
            self.games_data = {}
            self.xml2_games_data = {}
            self.duplicates = {}
            self.not_modified_games = []
            
            # FASE 1: Carica l'XML principale per identificare i giochi presenti
            self.log_message("\n=== FASE 1: Caricamento XML principale ===")
            xml_games = self.get_xml_games(xml_file)
            if not xml_games:
                return
            
            self.log_message(f"Trovati {len(xml_games)} giochi nell'XML principale")
            
            # FASE 2a: Carica il secondo XML se presente
            if xml2_file:
                self.log_message("\n=== FASE 2a: Caricamento XML di riferimento ===")
                if not self.load_xml2_data(xml2_file, xml_games):
                    return
            
            # FASE 2b: Carica i dati dal file di testo
            self.log_message("\n=== FASE 2b: Caricamento file dati TXT ===")
            if not self.load_data_file(txt_file, xml_games, self.xml2_games_data):
                return
            
            # Gestisce i duplicati (solo per i dati dal file TXT)
            if not self.handle_duplicates_txt():
                return
            
            # FASE 3: Elabora l'XML
            self.log_message("\n=== FASE 3: Elaborazione XML ===")
            if self.process_xml(xml_file):
                self.save_log(xml_file)
                self.log_message("\n=== Operazione completata con successo! ===")
            
        except Exception as e:
            self.log_message(f"Errore durante l'elaborazione: {e}")
        finally:
            # Riabilita il pulsante e ferma la barra di progresso
            self.root.after(0, self.finish_processing)
    
    def get_xml_games(self, xml_file_path: str) -> set:
        """Estrae l'elenco dei nomi dei giochi dall'XML"""
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            games = set()
            for game in root.findall('game'):
                game_name = game.attrib.get('name', '')
                if game_name:
                    games.add(game_name)
            
            return games
            
        except Exception as e:
            self.log_message(f"Errore durante la lettura dell'XML: {e}")
            return set()
    
    def load_xml2_data(self, xml2_file_path: str, xml_games: set) -> bool:
        """Carica i dati dal secondo XML di riferimento"""
        try:
            tree = ET.parse(xml2_file_path)
            root = tree.getroot()
            
            self.log_message(f"Caricamento da XML di riferimento: {xml2_file_path}")
            
            loaded_games = 0
            
            for game in root.findall('game'):
                game_name = game.attrib.get('name', '')
                
                # Considera solo i giochi presenti nell'XML principale
                if game_name not in xml_games:
                    continue
                
                # Estrae i dati dal gioco
                game_data = {}
                
                # Sourcefile
                if 'sourcefile' in game.attrib:
                    game_data['sourcefile'] = game.attrib['sourcefile']
                
                # Info elements
                for info in game.findall('info'):
                    info_name = info.get('name', '')
                    info_value = info.get('value', '')
                    if info_name in ['mameID', 'machine_type', 'add_by', 'add_in']:
                        game_data[info_name] = info_value
                
                # Sound
                sound_elem = game.find('sound')
                if sound_elem is not None:
                    game_data['sound_channels'] = sound_elem.get('channels', '')
                
                # Video
                video_elem = game.find('video')
                if video_elem is not None:
                    game_data['video_screen'] = video_elem.get('screen', '')
                    game_data['orientation'] = video_elem.get('orientation', '')
                
                # Input
                input_elem = game.find('input')
                if input_elem is not None:
                    game_data['input_players'] = input_elem.get('players', '')
                
                # Driver
                driver_elem = game.find('driver')
                if driver_elem is not None:
                    game_data['status'] = driver_elem.get('status', '')
                    game_data['emulation'] = driver_elem.get('emulation', '')
                    game_data['color'] = driver_elem.get('color', '')
                    game_data['sound'] = driver_elem.get('sound', '')
                    game_data['graphic'] = driver_elem.get('graphic', '')
                    game_data['savestate'] = driver_elem.get('savestate', '')
                
                # Salva solo se ha almeno un dato utile
                if game_data:
                    self.xml2_games_data[game_name] = game_data
                    loaded_games += 1
            
            self.log_message(f"Caricati {loaded_games} giochi dall'XML di riferimento")
            return True
            
        except Exception as e:
            self.log_message(f"Errore durante il caricamento dell'XML di riferimento: {e}")
            return False
    
    def finish_processing(self):
        """Chiamata al termine dell'elaborazione"""
        self.progress.stop()
        self.process_button.config(state='normal')
    
    def load_data_file(self, data_file_path: str, xml_games: set, xml2_data: dict) -> bool:
        """Carica il file di testo con i dati dei giochi"""
        try:
            with open(data_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.log_message(f"Caricamento da file TXT: {data_file_path}")
            
            total_lines = 0
            skipped_lines = 0
            skipped_xml2 = 0
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                total_lines += 1
                    
                parts = line.split(';')
                if len(parts) != 16:
                    self.log_message(f"Errore alla riga {line_num}: numero di campi non corretto ({len(parts)} invece di 16)")
                    continue
                
                game_name = parts[0].strip()
                
                # Considera solo i giochi presenti nell'XML principale
                if game_name not in xml_games:
                    skipped_lines += 1
                    continue
                
                # Se il gioco è già presente nell'XML2, non considerare il file TXT
                if game_name in xml2_data:
                    skipped_xml2 += 1
                    continue
                
                game_data = {
                    'sourcefile': parts[1].strip(),
                    'mameID': parts[2].strip(),
                    'machine_type': parts[3].strip(),
                    'add_by': parts[4].strip(),
                    'add_in': parts[5].strip(),
                    'sound_channels': parts[6].strip(),
                    'video_screen': parts[7].strip(),
                    'orientation': parts[8].strip(),
                    'input_players': parts[9].strip(),
                    'status': parts[10].strip(),
                    'emulation': parts[11].strip(),
                    'color': parts[12].strip(),
                    'sound': parts[13].strip(),
                    'graphic': parts[14].strip(),
                    'savestate': parts[15].strip()
                }
                
                # Gestione duplicati
                if game_name in self.games_data:
                    if game_name not in self.duplicates:
                        self.duplicates[game_name] = [self.games_data[game_name]]
                    self.duplicates[game_name].append(game_data)
                else:
                    self.games_data[game_name] = game_data
            
            self.log_message(f"Righe totali elaborate: {total_lines}")
            self.log_message(f"Giochi saltati (non presenti nell'XML): {skipped_lines}")
            self.log_message(f"Giochi saltati (già presenti nell'XML2): {skipped_xml2}")
            self.log_message(f"Giochi caricati dal file TXT: {len(self.games_data)}")
            if self.duplicates:
                self.log_message(f"Trovati {len(self.duplicates)} giochi con nomi duplicati")
            
            return True
            
        except FileNotFoundError:
            self.log_message(f"Errore: File {data_file_path} non trovato")
            return False
        except Exception as e:
            self.log_message(f"Errore durante il caricamento del file dati: {e}")
            return False
    
    def extract_mame_version(self, xml_file_path):
        """Estrae la versione MAME dal nome del file (es. 'mame_039_0.33b3.xml' → '0.33b3')"""
        base_name = os.path.basename(xml_file_path)
        name_without_ext = os.path.splitext(base_name)[0]
        parts = name_without_ext.split('_')
        if len(parts) >= 3:
            return parts[2]  # Es. "0.33b3"
        return None

    def handle_duplicates_txt(self) -> bool:
        """Gestisce i giochi duplicati con dialog GUI (filtra per versione MAME)"""
        if not self.duplicates:
            return True
        
        # Estrai la versione MAME dal file XML
        xml_version_str = self.extract_mame_version(self.xml_var.get())
        if not xml_version_str:
            self.log_message("Errore: Impossibile determinare la versione MAME dal nome del file")
            return True
        
        try:
            xml_version = packaging_version.parse(xml_version_str)
        except Exception as e:
            self.log_message(f"Errore nel parsing della versione: {e}")
            return True
        
        self.log_message(f"Versione MAME del file XML: {xml_version_str}")
        
        for game_name, duplicates_list in self.duplicates.items():
            # Filtra solo le versioni <= alla versione del file XML
            filtered = []
            for data in duplicates_list:
                add_in = data['add_in']
                try:
                    add_in_version = packaging_version.parse(add_in)
                    if add_in_version <= xml_version:
                        filtered.append(data)
                except Exception as e:
                    self.log_message(f"Errore nel parsing della versione 'add_in': {add_in} - {e}")
                    continue
            
            # Se non ci sono versioni valide, salta
            if not filtered:
                self.log_message(f"Nessuna versione valida trovata per '{game_name}'")
                continue
            
            # Se c'è solo una versione, selezionala automaticamente
            if len(filtered) == 1:
                self.games_data[game_name] = filtered[0]
                self.log_message(f"Selezionata automaticamente la versione per '{game_name}'")
                continue
            
            # Altrimenti mostra il dialogo
            choice = self.show_duplicate_dialog(game_name, filtered)
            if choice is None:  # Utente ha annullato
                self.log_message("Operazione annullata dall'utente")
                return False
            
            self.games_data[game_name] = filtered[choice]
            self.log_message(f"Selezionata versione {choice + 1} per '{game_name}'")
        
        # Pulisce i duplicati dopo la selezione
        self.duplicates.clear()
        return True
    
    def show_duplicate_dialog(self, game_name, duplicates_list):
        """Mostra un dialog per scegliere tra i duplicati"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Duplicato trovato: {game_name}")
        dialog.geometry("400x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centra il dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        result = None
        
        # Frame principale
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        ttk.Label(main_frame, text=f"Gioco duplicato: {game_name}", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        ttk.Label(main_frame, text="Scegli quale versione utilizzare:").pack(pady=(0, 10))
        
        # Frame per i radio button
        radio_frame = ttk.Frame(main_frame)
        radio_frame.pack(fill=tk.BOTH, expand=True)
        
        # Variabile per la selezione
        selection_var = tk.IntVar(value=0)
        
        # Crea i radio button per ogni duplicato
        for i, data in enumerate(duplicates_list):
            frame = ttk.LabelFrame(radio_frame, text=f"Versione {i + 1}", padding="5")
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Radiobutton(frame, text="Seleziona questa versione", 
                           variable=selection_var, value=i).pack(anchor=tk.W)
            
            # Mostra i dettagli
            details = [
                f"Sourcefile: {data['sourcefile']}",
                f"MAME ID: {data['mameID']}",
                f"Machine Type: {data['machine_type']}",
                f"Add By: {data['add_by']}",
                f"Add In: {data['add_in']}"
            ]
            
            for detail in details:
                ttk.Label(frame, text=detail, font=('Arial', 8)).pack(anchor=tk.W, padx=20)
        
        # Frame per i pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        def on_ok():
            nonlocal result
            result = selection_var.get()
            dialog.destroy()
        
        def on_cancel():
            nonlocal result
            result = None
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annulla", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Aspetta che il dialog venga chiuso
        dialog.wait_window()
        
        return result
    
    def preserve_formatting(self, element: ET.Element) -> str:
        """Preserva la formattazione originale dell'XML con tabulazioni"""
        if element.tag == "game":
            # Costruisce manualmente il tag game PRESERVANDO TUTTI GLI ATTRIBUTI ESISTENTI
            attrs = []
            for attr_name, attr_value in element.attrib.items():
                attrs.append(f'{attr_name}="{attr_value}"')
            
            result = f'\t<game {" ".join(attrs)}>\n'
            
            # Ordine preciso degli elementi:
            # 1. description, year, manufacturer
            # 2. info elements
            # 3. rom elements
            # 4. sample elements
            # 5. sound, video, input, driver
            
            # 1. Description, year, manufacturer
            for child in element:
                if child.tag in ['description', 'year', 'manufacturer']:
                    result += f'\t\t<{child.tag}>{child.text}</{child.tag}>\n'
            
            # 2. Info elements
            for child in element:
                if child.tag == 'info':
                    result += f'\t\t<info name="{child.attrib["name"]}" value="{child.attrib["value"]}"/>\n'
            
            # 3. ROM elements
            for child in element:
                if child.tag == 'rom':
                    attrs_str = ' '.join([f'{k}="{v}"' for k, v in child.attrib.items()])
                    result += f'\t\t<rom {attrs_str}/>\n'
            
            # 4. Sample elements
            for child in element:
                if child.tag == 'sample':
                    attrs_str = ' '.join([f'{k}="{v}"' for k, v in child.attrib.items()])
                    result += f'\t\t<sample {attrs_str}/>\n'
            
            # 5. Sound, video, input, driver
            for child in element:
                if child.tag == 'sound':
                    result += f'\t\t<sound channels="{child.attrib["channels"]}"/>\n'
            
            for child in element:
                if child.tag == 'video':
                    attrs_str = ' '.join([f'{k}="{v}"' for k, v in child.attrib.items()])
                    result += f'\t\t<video {attrs_str}/>\n'
            
            for child in element:
                if child.tag == 'input':
                    result += f'\t\t<input players="{child.attrib["players"]}"/>\n'
            
            for child in element:
                if child.tag == 'driver':
                    attrs_str = ' '.join([f'{k}="{v}"' for k, v in child.attrib.items()])
                    result += f'\t\t<driver {attrs_str}/>\n'
            
            result += '\t</game>\n'
            return result
        
        return ""
    
    def get_game_data(self, game_name: str) -> dict:
        """Ottiene i dati per un gioco, prima dall'XML2 poi dal file TXT"""
        # Prima controlla nell'XML di riferimento
        if game_name in self.xml2_games_data:
            xml2_data = self.xml2_games_data[game_name].copy()
            
            # Se c'è anche nel file TXT, integra i dati mancanti
            if game_name in self.games_data:
                txt_data = self.games_data[game_name]
                for key, value in txt_data.items():
                    if key not in xml2_data or not xml2_data[key]:
                        xml2_data[key] = value
            
            return xml2_data
        
        # Altrimenti usa i dati dal file TXT
        elif game_name in self.games_data:
            return self.games_data[game_name]
        
        return {}
    
    def process_xml(self, xml_file_path: str) -> bool:
        """Elabora il file XML MAME"""
        try:
            self.log_message(f"Elaborazione file: {xml_file_path}")
            
            # Legge il file XML preservando la struttura
            with open(xml_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Trova l'header (tutto prima del primo <game>)
            game_start = content.find('<game')
            if game_start == -1:
                self.log_message("Errore: Nessun tag <game> trovato nel file XML")
                return False
            
            header = content[:game_start]
            
            # Parsa l'XML
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            modified_games = 0
            total_games = len(root.findall('game'))
            
            self.log_message(f"Trovati {total_games} giochi nel file XML")
            self.log_message(f"Attributi selezionati per la modifica: {[k for k, v in self.selected_attributes.items() if v]}")
            
            # Elabora ogni gioco
            for game in root.findall('game'):
                game_name = game.attrib.get('name', '')
                
                # Ottiene i dati (prima da XML2, poi da TXT)
                data = self.get_game_data(game_name)
                
                if data:
                    # Modifica solo gli attributi selezionati
                    
                    # Sourcefile (attributo del tag game)
                    if self.selected_attributes.get('sourcefile', False) and 'sourcefile' in data:
                        game.set('sourcefile', data['sourcefile'])
                    
                    # Info elements - rimuove solo quelli che verranno sostituiti
                    info_names_to_process = []
                    if self.selected_attributes.get('mameID', False) and 'mameID' in data:
                        info_names_to_process.append('mameID')
                    if self.selected_attributes.get('machine_type', False) and 'machine_type' in data:
                        info_names_to_process.append('machine_type')
                    if self.selected_attributes.get('add_by', False) and 'add_by' in data:
                        info_names_to_process.append('add_by')
                    if self.selected_attributes.get('add_in', False) and 'add_in' in data:
                        info_names_to_process.append('add_in')
                    
                    # Rimuove solo gli info che verranno sostituiti
                    for info_elem in game.findall('info'):
                        if info_elem.get('name') in info_names_to_process:
                            game.remove(info_elem)
                    
                    # Sound, Video, Input - rimuove solo se verranno sostituiti
                    if (self.selected_attributes.get('sound_channels', False) and 'sound_channels' in data):
                        for elem in game.findall('sound'):
                            game.remove(elem)
                    
                    if (self.selected_attributes.get('video_screen', False) or self.selected_attributes.get('orientation', False)) and ('video_screen' in data or 'orientation' in data):
                        for elem in game.findall('video'):
                            game.remove(elem)
                    
                    if self.selected_attributes.get('input_players', False) and 'input_players' in data:
                        for elem in game.findall('input'):
                            game.remove(elem)
                    
                    # Trova la posizione dopo manufacturer per inserire i nuovi elementi info
                    manufacturer_elem = game.find('manufacturer')
                    if manufacturer_elem is not None:
                        insert_pos = list(game).index(manufacturer_elem) + 1
                    else:
                        insert_pos = len(list(game))
                    
                    # Aggiunge i nuovi elementi info selezionati
                    info_count = 0
                    for info_name in info_names_to_process:
                        if info_name in data:
                            info_elem = ET.Element('info')
                            info_elem.set('name', info_name)
                            info_elem.set('value', data[info_name])
                            game.insert(insert_pos + info_count, info_elem)
                            info_count += 1
                    
                    # Trova la posizione dopo le ROM per aggiungere sound, video, input
                    rom_elements = game.findall('rom')
                    if rom_elements:
                        last_rom_pos = max([list(game).index(rom) for rom in rom_elements]) + 1
                    else:
                        last_rom_pos = len(list(game))
                    
                    # Aggiunge sound se selezionato
                    if self.selected_attributes.get('sound_channels', False) and 'sound_channels' in data:
                        sound_elem = ET.Element('sound')
                        sound_elem.set('channels', data['sound_channels'])
                        game.insert(last_rom_pos, sound_elem)
                        last_rom_pos += 1
                    
                    # Aggiunge video se selezionato
                    if (self.selected_attributes.get('video_screen', False) or self.selected_attributes.get('orientation', False)) and ('video_screen' in data or 'orientation' in data):
                        video_elem = ET.Element('video')
                        if 'video_screen' in data and self.selected_attributes.get('video_screen', False):
                            video_elem.set('screen', data['video_screen'])
                        if 'orientation' in data and self.selected_attributes.get('orientation', False):
                            video_elem.set('orientation', data['orientation'])
                        game.insert(last_rom_pos, video_elem)
                        last_rom_pos += 1
                    
                    # Aggiunge input se selezionato
                    if self.selected_attributes.get('input_players', False) and 'input_players' in data:
                        input_elem = ET.Element('input')
                        input_elem.set('players', data['input_players'])
                        game.insert(last_rom_pos, input_elem)
                    
                    # Gestisce driver: rimuove e ricrea solo se richiesto E se gli attributi driver sono selezionati
                    driver_attrs_selected = any([
                        self.selected_attributes.get('driver_status', False),
                        self.selected_attributes.get('driver_emulation', False),
                        self.selected_attributes.get('driver_color', False),
                        self.selected_attributes.get('driver_sound', False),
                        self.selected_attributes.get('driver_graphic', False),
                        self.selected_attributes.get('driver_savestate', False)
                    ])
                    
                    if self.modify_driver and driver_attrs_selected:
                        # Rimuove eventuali driver esistenti
                        for elem in game.findall('driver'):
                            game.remove(elem)
                        
                        # Crea nuovo driver con solo gli attributi selezionati
                        driver_elem = ET.Element('driver')
                        if self.selected_attributes.get('driver_status', False) and 'status' in data:
                            driver_elem.set('status', data['status'])
                        if self.selected_attributes.get('driver_emulation', False) and 'emulation' in data:
                            driver_elem.set('emulation', data['emulation'])
                        if self.selected_attributes.get('driver_color', False) and 'color' in data:
                            driver_elem.set('color', data['color'])
                        if self.selected_attributes.get('driver_sound', False) and 'sound' in data:
                            driver_elem.set('sound', data['sound'])
                        if self.selected_attributes.get('driver_graphic', False) and 'graphic' in data:
                            driver_elem.set('graphic', data['graphic'])
                        if self.selected_attributes.get('driver_savestate', False) and 'savestate' in data:
                            driver_elem.set('savestate', data['savestate'])
                        
                        # Aggiunge il driver solo se ha almeno un attributo
                        if driver_elem.attrib:
                            game.append(driver_elem)
                    
                    modified_games += 1
                else:
                    self.not_modified_games.append(game_name)
            
            # Salva il file modificato
            base_name = os.path.splitext(xml_file_path)[0]
            output_file = f"{base_name}_upd.xml"
            
            # Ricostruisce l'XML mantenendo la formattazione
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(header)
                for game in root.findall('game'):
                    f.write(self.preserve_formatting(game))
                f.write('</datafile>\n')
            
            self.log_message(f"Giochi modificati: {modified_games}/{total_games}")
            self.log_message(f"File salvato come: {output_file}")
            
            return True
            
        except Exception as e:
            self.log_message(f"Errore durante l'elaborazione dell'XML: {e}")
            return False
    
    def save_log(self, xml_file_path: str):
        """Salva il log dei giochi non modificati"""
        if not self.not_modified_games:
            self.log_message("Tutti i giochi sono stati modificati, nessun log necessario.")
            return
        
        base_name = os.path.splitext(xml_file_path)[0]
        log_file = f"{base_name}_not_modified.log"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("Giochi non modificati:\n")
                f.write("=" * 50 + "\n")
                for game_name in self.not_modified_games:
                    f.write(f"{game_name}\n")
            
            self.log_message(f"Log salvato come: {log_file}")
            self.log_message(f"Giochi non modificati: {len(self.not_modified_games)}")
            
        except Exception as e:
            self.log_message(f"Errore durante il salvataggio del log: {e}")
    
    def run(self):
        """Avvia l'applicazione"""
        self.root.mainloop()


def main():
    app = MAMEXMLProcessorGUI()
    app.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        input("Premi Invio per uscire...")