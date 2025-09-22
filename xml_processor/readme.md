**README**

**IT - Italiano**

MAME XML Processor v1.0d

Questo script permette di aggiornare un file XML MAME principale con dati provenienti da un file di testo (TXT) e/o da un secondo file XML di riferimento. E' pensato per chi gestisce archivi di giochi MAME personalizzati e necessita di integrare informazioni aggiuntive come sourcefile, ID, tipo di macchina, canali audio, orientamento schermo, numero di giocatori e stato del driver.

Funzionalità principali:
- Aggiornamento selettivo degli attributi dei giochi
- Supporto per file TXT con dati strutturati (separati da punto e virgola)
- Integrazione opzionale con un secondo file XML di riferimento
- Selezione personalizzata degli attributi da modificare tramite interfaccia grafica
- Gestione automatica dei giochi duplicati nel file TXT
- Filtro per versione MAME (solo versioni <= a quella del file XML)
- Mantenimento della formattazione originale del file XML
- Log dettagliato delle operazioni eseguite
- Salvataggio dei giochi non modificati in un file di log separato

Requisiti:
- Python 3.x
- Moduli Python: tkinter, xml, configparser, threading, packaging
- Installare il modulo packaging: pip install packaging

Come utilizzare:
1. Configura il file config.ini con i percorsi predefiniti (opzionale)
2. Avvia lo script: python mame_xml_processor.py
3. Seleziona il file XML MAME principale
4. Se necessario, seleziona un file XML di riferimento
5. Seleziona il file dati TXT
6. Scegli quali attributi modificare tramite il dialogo che appare
7. Clicca "Elabora XML" per avviare il processo
8. Il risultato sara salvato come [nome_originale]_upd.xml

Formato file TXT:
Ogni riga deve contenere 16 campi separati da punto e virgola:
nome_gioco;sourcefile;mameID;machine_type;add_by;add_in;sound_channels;video_screen;orientation;input_players;status;emulation;color;sound;graphic;savestate

Note:
- Il file config.ini viene creato automaticamente se non esiste
- I giochi gia presenti nell'XML di riferimento vengono ignorati nel file TXT
- Lo script gestisce automaticamente i duplicati basandosi sulla versione MAME

---

**EN - English**

MAME XML Processor v1.0d

This script updates a main MAME XML file with data from a text file (TXT) and/or a secondary reference XML file. It is designed for users managing custom MAME game archives who need to integrate additional information such as sourcefile, ID, machine type, sound channels, screen orientation, player count, and driver status.

Main features:
- Selective update of game attributes
- Support for structured TXT data files (semicolon-separated)
- Optional integration with a secondary reference XML file
- Custom attribute selection via graphical interface
- Automatic handling of duplicate games in the TXT file
- MAME version filtering (only versions <= XML file version)
- Preservation of original XML file formatting
- Detailed operation logging
- Save unmodified games to a separate log file
- User-friendly GUI with progress indication

Requirements:
- Python 3.x
- Python modules: tkinter, xml, configparser, threading, packaging
- Install packaging module: pip install packaging

How to use:
1. Configure config.ini with default paths (optional)
2. Run the script: python mame_xml_processor.py
3. Select the main MAME XML file
4. Optionally select a reference XML file
5. Select the TXT data file
6. Choose which attributes to modify via the popup dialog
7. Click "Process XML" to start
8. Output will be saved as [original_name]_upd.xml

TXT file format:
Each line must contain 16 semicolon-separated fields:
game_name;sourcefile;mameID;machine_type;add_by;add_in;sound_channels;video_screen;orientation;input_players;status;emulation;color;sound;graphic;savestate

Notes:
- The config.ini file is created automatically if missing
- Games already present in the reference XML are ignored in the TXT file
- The script automatically handles duplicates based on MAME version