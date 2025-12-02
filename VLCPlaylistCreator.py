import os
import re
import threading
import queue
from tkinter import filedialog, messagebox, Tk, Button, Label, Entry, StringVar, BooleanVar, Checkbutton, Frame, LabelFrame, Toplevel, Text, Scrollbar
from urllib.parse import quote, unquote
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


class PlaylistCreator:
    def __init__(self, progress_callback=None):
        # Verwende normale Python-Booleans statt BooleanVar
        self.create_combined_playlists = True
        self.create_storyline_playlists = True
        self.save_in_parent_dir = True
        self.progress_callback = progress_callback  # Callback für Fortschrittsanzeige
        
    def update_progress(self, message, current=None, total=None):
        """Aktualisiert die Fortschrittsanzeige, wenn Callback vorhanden."""
        if self.progress_callback:
            self.progress_callback(message, current, total)
    
    def robust_natural_sort_key(self, s):
        """
        Robuste natürliche Sortierung für alle Dateinamen-Formate.
        """
        # Wenn es eine URL ist, extrahiere den Dateinamen
        if isinstance(s, str) and s.startswith('file:///'):
            path = s.replace('file:///', '')
            path = unquote(path)
            filename = os.path.basename(path)
        else:
            filename = str(s)
        
        # Entferne Dateierweiterung
        name_without_ext = os.path.splitext(filename)[0]
        
        # 1. Erkennung von Episodenformat: "1 - Titel" oder "01. Titel" oder "S01E01"
        # Muster: Zahl am Anfang, gefolgt von Trennzeichen und Titel
        episode_pattern = r'^(?:S(\d+)[Ee](\d+)|(\d+)[\.\s-]+)(.*)'
        episode_match = re.match(episode_pattern, name_without_ext)
        
        if episode_match:
            # Fall: S01E01 Format
            if episode_match.group(1):
                season = int(episode_match.group(1))
                episode = int(episode_match.group(2))
                title = episode_match.group(4).strip()
                return (0, season, episode, title.lower())
            # Fall: Nummer am Anfang Format
            else:
                number = int(episode_match.group(3) or 0)
                title = episode_match.group(4).strip()
                return (1, number, title.lower())
        
        # 2. Erkennung von Filmreihen: "Titel 2 (Jahr)" oder "Titel: Teil II (Jahr)"
        # Extrahiere Jahr
        year_match = re.search(r'\((\d{4})\)', name_without_ext)
        year = int(year_match.group(1)) if year_match else 9999  # 9999 für Filme ohne Jahr
        
        # Entferne Jahr aus dem Namen
        name_without_year = re.sub(r'\s*\(\d{4}\)', '', name_without_ext)
        
        # Suche nach Teilnummer (arabisch oder römisch)
        # Arabische Zahlen am Ende oder nach Leerzeichen
        arabic_match = re.search(r'(\d+)$', name_without_year.strip())
        
        # Römische Zahlen
        roman_numerals = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
            'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15
        }
        
        # Suche nach römischen Zahlen (mit oder ohne "Teil", "Part", etc.)
        roman_match = None
        for roman in roman_numerals:
            if re.search(fr'\s*(?:Teil|Part|Teil\s+)?{roman}\s*$', name_without_year, re.IGNORECASE):
                roman_match = roman
                break
        
        if arabic_match:
            part_num = int(arabic_match.group(1))
            base_name = re.sub(r'\s*\d+$', '', name_without_year).strip()
        elif roman_match:
            part_num = roman_numerals[roman_match]
            base_name = re.sub(fr'\s*(?:Teil|Part|Teil\s+)?{roman_match}\s*$', '', name_without_year, flags=re.IGNORECASE).strip()
        else:
            # Keine explizite Teilnummer -> Teil 1
            part_num = 1
            base_name = name_without_year.strip()
        
        # Entferne Doppelpunkte und andere Trennzeichen vom Anfang des Basisnamens
        base_name = re.sub(r'^[:\-\s]+', '', base_name)
        
        return (2, base_name.lower(), part_num, year)
    
    def extract_sort_key_from_path(self, filepath):
        """
        Extrahiert Sortierschlüssel aus einem Dateipfad.
        """
        if filepath.startswith('file:///'):
            path = filepath.replace('file:///', '')
            path = unquote(path)
            filename = os.path.basename(path)
            full_path = path
        else:
            filename = os.path.basename(filepath)
            full_path = filepath
        
        # Get sort key from filename
        sort_key = self.robust_natural_sort_key(filename)
        
        # Für bessere Gruppierung: füge Verzeichnispfad hinzu (ohne Dateiname)
        dir_path = os.path.dirname(full_path) if 'full_path' in locals() else os.path.dirname(filepath)
        
        # Rückgabe: Sortierschlüssel + Verzeichnispfad für stabile Sortierung
        return (*sort_key, dir_path.lower())
    
    def delete_old_playlists(self, directory):
        """
        Löscht alte Playlist-Dateien.
        """
        deleted_count = 0
        self.update_progress(f"Lösche alte Playlists in: {directory}")
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.xspf') or file.endswith('.m3u'):
                    try:
                        os.remove(os.path.join(root, file))
                        deleted_count += 1
                    except:
                        pass
        
        self.update_progress(f"{deleted_count} alte Playlists gelöscht")
        return deleted_count
    
    def create_playlist_for_directory(self, directory, playlist_name=None):
        """
        Erstellt eine Playlist für ein spezifisches Verzeichnis.
        """
        media_files = []
        
        # Sammle alle Medien-Dateien im Verzeichnis
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path) and item.lower().endswith(('.mp4', '.mp3', '.mkv', '.avi', '.flac', '.wav', '.m4a')):
                media_files.append(item)
        
        if not media_files:
            return 0
        
        # Sortiere Dateien
        media_files.sort(key=self.robust_natural_sort_key)
        
        # Erstelle Playlist
        playlist = Element('playlist', {'version': '1', 'xmlns': 'http://xspf.org/ns/0/'})
        title = SubElement(playlist, 'title')
        
        if playlist_name:
            title.text = playlist_name
        else:
            title.text = os.path.basename(directory) if directory != '.' else 'Playlist'
        
        track_list = SubElement(playlist, 'trackList')
        
        for media_file in media_files:
            track = SubElement(track_list, 'track')
            location = SubElement(track, 'location')
            file_path = os.path.join(directory, media_file).replace('\\', '/')
            encoded_path = quote(file_path, safe=":/")
            location.text = f'file:///{encoded_path}'
        
        xml_string = tostring(playlist, 'utf-8')
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent='  ')
        
        # Bestimme, wo die Playlist gespeichert werden soll
        if self.save_in_parent_dir:
            # Speichere im übergeordneten Ordner
            parent_directory = os.path.dirname(directory)
            if playlist_name:
                playlist_filename = os.path.join(parent_directory, f'{playlist_name}.xspf')
            else:
                folder_name = os.path.basename(directory)
                playlist_filename = os.path.join(parent_directory, f'{folder_name}.xspf')
        else:
            # Speichere im aktuellen Verzeichnis
            if playlist_name:
                playlist_filename = os.path.join(directory, f'{playlist_name}.xspf')
            else:
                playlist_filename = os.path.join(directory, f'{os.path.basename(directory) if directory != "." else "Playlist"}.xspf')
        
        with open(playlist_filename, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        self.update_progress(f"Playlist erstellt: {os.path.basename(playlist_filename)} ({len(media_files)} Dateien)")
        return len(media_files)
    
    def create_combined_playlist(self, directory, subdirs_with_playlists):
        """
        Erstellt eine kombinierte Playlist aus mehreren Unterordner-Playlists.
        OHNE "(Kombiniert)" im Namen, wenn die Option aktiv ist.
        BEHÄLT die Reihenfolge der Original-Playlists bei (keine Neu-Sortierung).
        INKLUDIERT auch Mediendateien die direkt im Genre-Ordner liegen.
        """
        self.update_progress(f"Erstelle kombinierte Playlist für: {os.path.basename(directory)}")
        
        all_tracks = []
        
        # SCHRITT 1: Prüfe ob es eine eigene Playlist für dieses Verzeichnis gibt
        # (für Mediendateien die direkt im Genre-Ordner liegen)
        if self.save_in_parent_dir:
            parent_of_directory = os.path.dirname(directory)
            directory_playlist_path = os.path.join(parent_of_directory, f'{os.path.basename(directory)}.xspf')
        else:
            directory_playlist_path = os.path.join(directory, f'{os.path.basename(directory)}.xspf')
        
        # Wenn es eine Playlist für dieses Verzeichnis selbst gibt, füge deren Tracks ZUERST hinzu
        if os.path.exists(directory_playlist_path):
            try:
                with open(directory_playlist_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    xml_tree = minidom.parseString(content)
                    track_list = xml_tree.getElementsByTagName('trackList')[0]
                    tracks = track_list.getElementsByTagName('track')
                    
                    for track in tracks:
                        location = track.getElementsByTagName('location')[0]
                        all_tracks.append(location.firstChild.data)
            except:
                pass
        
        # SCHRITT 2: Sortiere die Unterverzeichnisse nach Namen (für konsistente Reihenfolge)
        if subdirs_with_playlists:
            subdirs_with_playlists_sorted = sorted(subdirs_with_playlists, key=lambda x: os.path.basename(x).lower())
        else:
            subdirs_with_playlists_sorted = []
        
        # SCHRITT 3: Sammle alle Tracks aus allen Unterordner-Playlists IN DER REIHENFOLGE
        for subdir in subdirs_with_playlists_sorted:
            if self.save_in_parent_dir:
                # Wenn im übergeordneten Ordner gespeichert wird, suche Playlist im übergeordneten Ordner des Unterordners
                parent_of_subdir = os.path.dirname(subdir)
                playlist_name = os.path.basename(subdir)
                playlist_path = os.path.join(parent_of_subdir, f'{playlist_name}.xspf')
            else:
                # Wenn im aktuellen Ordner gespeichert wird, suche Playlist im Unterordner
                playlist_path = os.path.join(subdir, f'{os.path.basename(subdir)}.xspf')
            
            if os.path.exists(playlist_path):
                try:
                    with open(playlist_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        xml_tree = minidom.parseString(content)
                        track_list = xml_tree.getElementsByTagName('trackList')[0]
                        tracks = track_list.getElementsByTagName('track')
                        
                        # Füge alle Tracks DIESER Playlist in der Original-Reihenfolge hinzu
                        for track in tracks:
                            location = track.getElementsByTagName('location')[0]
                            all_tracks.append(location.firstChild.data)
                except:
                    continue
        
        if not all_tracks:
            return 0
        
        # WICHTIG: Entferne nur Duplikate, aber KEINE Neu-Sortierung!
        # dict.fromkeys() behält die Einfüge-Reihenfolge bei (Python 3.7+)
        unique_tracks = list(dict.fromkeys(all_tracks))
        
        # ENTFERNT: unique_tracks.sort(key=self.extract_sort_key_from_path)
        # Die Reihenfolge bleibt so wie sie aus den Playlists kommt!
        
        # Erstelle kombinierte Playlist
        playlist = Element('playlist', {'version': '1', 'xmlns': 'http://xspf.org/ns/0/'})
        title = SubElement(playlist, 'title')
        # Wenn kombinierte Playlists aktiv sind, KEIN "(Kombiniert)" im Namen
        if self.create_combined_playlists:
            title.text = f'{os.path.basename(directory)}'
        else:
            title.text = f'{os.path.basename(directory)} (Kombiniert)'
        
        track_list = SubElement(playlist, 'trackList')
        
        for track_path in unique_tracks:
            track = SubElement(track_list, 'track')
            location = SubElement(track, 'location')
            location.text = track_path
        
        xml_string = tostring(playlist, 'utf-8')
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent='  ')
        
        # Bestimme, wo die kombinierte Playlist gespeichert werden soll
        if self.save_in_parent_dir:
            # Speichere im übergeordneten Ordner
            parent_folder = os.path.dirname(directory)
            # Wenn kombinierte Playlists aktiv sind, KEIN "(Kombiniert)" im Dateinamen
            if self.create_combined_playlists:
                combined_playlist_filename = os.path.join(parent_folder, f'{os.path.basename(directory)}.xspf')
            else:
                combined_playlist_filename = os.path.join(parent_folder, f'{os.path.basename(directory)} (Kombiniert).xspf')
        else:
            # Speichere im aktuellen Ordner
            # Wenn kombinierte Playlists aktiv sind, KEIN "(Kombiniert)" im Dateinamen
            if self.create_combined_playlists:
                combined_playlist_filename = os.path.join(directory, f'{os.path.basename(directory)}.xspf')
            else:
                combined_playlist_filename = os.path.join(directory, f'{os.path.basename(directory)} (Kombiniert).xspf')
        
        with open(combined_playlist_filename, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        self.update_progress(f"Kombinierte Playlist erstellt: {os.path.basename(combined_playlist_filename)} ({len(unique_tracks)} Dateien)")
        return len(unique_tracks)
    
    def create_playlists_recursively(self, directory):
        """
        Erstellt Playlists rekursiv für die gesamte Verzeichnisstruktur.
        """
        total_playlists = 0
        total_files = 0
        
        # Zähle zuerst alle Verzeichnisse mit Mediendateien für die Fortschrittsanzeige
        dirs_to_process = []
        for root, dirs, files in os.walk(directory):
            # Überspringe Verzeichnisse, die keine Mediendateien enthalten sollten
            skip_dirs = {'extras', 'bonus', 'trailer', 'sample', 'backup'}
            dirs[:] = [d for d in dirs if d.lower() not in skip_dirs]
            
            # Prüfe, ob dieses Verzeichnis Mediendateien enthält
            media_in_current_dir = any(
                f.lower().endswith(('.mp4', '.mp3', '.mkv', '.avi', '.flac', '.wav', '.m4a'))
                for f in files
            )
            
            if media_in_current_dir:
                dirs_to_process.append(root)
        
        total_dirs = len(dirs_to_process)
        self.update_progress(f"Starte Playlist-Erstellung in {directory}", 0, total_dirs)
        
        # Phase 1: Erstelle Playlists für alle Verzeichnisse mit Mediendateien
        for i, root in enumerate(dirs_to_process):
            self.update_progress(f"Verarbeite Ordner {i+1}/{total_dirs}: {os.path.basename(root)}", i+1, total_dirs)
            
            # Prüfe, ob dieses Verzeichnis Mediendateien enthält
            files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))]
            media_in_current_dir = any(
                f.lower().endswith(('.mp4', '.mp3', '.mkv', '.avi', '.flac', '.wav', '.m4a'))
                for f in files
            )
            
            if media_in_current_dir:
                files_added = self.create_playlist_for_directory(root)
                if files_added > 0:
                    total_playlists += 1
                    total_files += files_added
            
            # Storyline Playlists (optional)
            if self.create_storyline_playlists:
                storyline_files = self.create_storyline_playlist(root)
                if storyline_files > 0:
                    total_playlists += 1
                    total_files += storyline_files
        
        # Phase 2: Kombinierte Playlists (optional)
        if self.create_combined_playlists:
            self.update_progress("Erstelle kombinierte Playlists...")
            combined_count = 0
            
            # Gehe von unten nach oben durch die Verzeichnisstruktur
            for root, dirs, files in os.walk(directory, topdown=False):
                # Finde Unterverzeichnisse, die Playlists haben
                subdirs_with_playlists = []
                for d in dirs:
                    subdir = os.path.join(root, d)
                    
                    # Prüfe, ob dieses Unterverzeichnis eine Playlist hat
                    if self.save_in_parent_dir:
                        # Wenn im übergeordneten Ordner gespeichert wird, suche Playlist im übergeordneten Ordner
                        parent_of_subdir = os.path.dirname(subdir)
                        playlist_file = os.path.join(parent_of_subdir, f'{d}.xspf')
                    else:
                        # Wenn im aktuellen Ordner gespeichert wird, suche Playlist im Unterordner
                        playlist_file = os.path.join(subdir, f'{d}.xspf')
                    
                    if os.path.exists(playlist_file):
                        subdirs_with_playlists.append(subdir)
                
                # Wenn dieses Verzeichnis Unterordner mit Playlists hat, erstelle kombinierte Playlist
                if subdirs_with_playlists:
                    combined_count += 1
                    self.update_progress(f"Erstelle kombinierte Playlist für {os.path.basename(root)}...")
                    combined_files = self.create_combined_playlist(root, subdirs_with_playlists)
                    if combined_files > 0:
                        total_playlists += 1
        
        self.update_progress("Playlist-Erstellung abgeschlossen!", total_dirs, total_dirs)
        return total_playlists, total_files
    
    def remove_brackets(self, term):
        return term.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
    
    def create_storyline_playlist(self, directory):
        """
        Erstellt eine Storyline-Playlist basierend auf einer Storyline.txt Datei.
        KORRIGIERTE VERSION: Ordnet Dateien Storyline-Einträgen zu und sortiert danach.
        """
        storyline_file = os.path.join(directory, "Storyline.txt")
        
        if not os.path.exists(storyline_file):
            return 0
        
        try:
            with open(storyline_file, "r", encoding="utf-8") as f:
                # Behalte die originale Reihenfolge und den Text bei
                original_storyline_entries = [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.update_progress(f"Fehler beim Lesen der Storyline: {e}")
            return 0
        
        if not original_storyline_entries:
            return 0
        
        self.update_progress(f"Erstelle Storyline-Playlist für {os.path.basename(directory)}")
        
        # 1. Sammle alle Medien-Dateien im Verzeichnis und allen Unterverzeichnissen
        media_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.mp4', '.mp3', '.mkv', '.avi', '.flac', '.wav', '.m4a')):
                    full_path = os.path.join(root, file)
                    media_files.append(full_path)
        
        if not media_files:
            self.update_progress("Keine Mediendateien im Verzeichnis gefunden.")
            return 0
        
        # 2. Vorbereitung der Storyline-Einträge für den Vergleich
        #    Wir erstellen eine "gesäuberte" Version jedes Eintrags für besseres Matching.
        def prepare_text_for_matching(text):
            """Entfernt Nummerierungen (wie '1.', '23.') und Jahreszahlen, konvertiert zu Kleinbuchstaben."""
            # Entferne führende Nummern mit Punkt/Dash (z.B. "1. ", "23 - ")
            text = re.sub(r'^\d+[\.\-\s]*', '', text)
            # Entferne Jahreszahlen in Klammern
            text = re.sub(r'\s*\(\d{4}\)', '', text)
            # Konvertiere zu Kleinbuchstaben und entferne überflüssige Leerzeichen
            return text.strip().lower()
        
        # Struktur: Liste von Tupeln (Original-Eintrag, bereinigter Eintrag)
        storyline_entries = []
        for entry in original_storyline_entries:
            cleaned = prepare_text_for_matching(entry)
            storyline_entries.append((entry, cleaned))
        
        # 3. JEDER Mediendatei einen Storyline-Eintrag zuordnen (oder nicht)
        #    Wir nutzen eine einfache, aber verbesserte Logik: Suche nach dem bereinigten
        #    Storyline-Text im bereinigten Dateinamen.
        matched_files = []  # Wird Tupele enthalten: (Storyline-Index, Dateipfad)
        unmatched_files = []  # Dateien, die keinem Eintrag zugeordnet werden konnten
        
        for file_path in media_files:
            filename = os.path.basename(file_path)
            # Entferne Erweiterung und bereinige den Dateinamen für den Vergleich
            name_without_ext = os.path.splitext(filename)[0]
            cleaned_filename = prepare_text_for_matching(name_without_ext)
            
            best_match_index = None
            best_match_score = 0
            
            # Durchsuche alle Storyline-Einträge, um den besten Treffer zu finden
            for idx, (original_entry, cleaned_entry) in enumerate(storyline_entries):
                # Einfacher, aber effektiver Score: Ist der bereinigte Storyline-Eintrag
                # im bereinigten Dateinamen enthalten?
                if cleaned_entry in cleaned_filename:
                    score = len(cleaned_entry)  # Länge des übereinstimmenden Textes
                    # Bonus, wenn der Eintrag am Anfang des Dateinamens steht
                    if cleaned_filename.startswith(cleaned_entry):
                        score += 5
                    if score > best_match_score:
                        best_match_score = score
                        best_match_index = idx
            
            # Nur zuordnen, wenn ein ausreichend guter Treffer gefunden wurde
            if best_match_index is not None and best_match_score >= 3:
                matched_files.append((best_match_index, file_path))
            else:
                unmatched_files.append(file_path)
        
        # 4. Sortiere die zugeordneten Dateien NACH DEM INDEX im Storyline-Eintrag
        #    Dadurch wird die exakte Reihenfolge der Storyline.txt eingehalten.
        matched_files.sort(key=lambda x: x[0])
        
        # 5. Erstelle die finale Liste der Dateien in der richtigen Reihenfolge
        final_file_list = [file_path for _, file_path in matched_files]
        
        # Optional: Nicht zugeordnete Dateien am Ende anfügen (für Debugging)
        # final_file_list.extend(unmatched_files)
        
        if not final_file_list:
            self.update_progress("Keine passenden Dateien für Storyline gefunden")
            return 0
        
        # 6. Erstelle die Playlist
        playlist = Element('playlist', {'version': '1', 'xmlns': 'http://xspf.org/ns/0/'})
        title = SubElement(playlist, 'title')
        title.text = 'Storyline Playlist'
        
        track_list = SubElement(playlist, 'trackList')
        
        for media_file in final_file_list:
            track = SubElement(track_list, 'track')
            location = SubElement(track, 'location')
            file_path = media_file.replace('\\', '/')
            encoded_path = quote(file_path, safe=":/")
            location.text = f'file:///{encoded_path}'
        
        xml_string = tostring(playlist, 'utf-8')
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent='  ')
        
        # KORREKTUR: Immer im selben Verzeichnis wie die Storyline.txt speichern
        playlist_filename = os.path.join(directory, 'Storyline.xspf')
        
        with open(playlist_filename, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        # Informative Statusmeldung
        self.update_progress(
            f"Storyline-Playlist erstellt: {len(final_file_list)} von {len(media_files)} Dateien zugeordnet. "
            f"({len(unmatched_files)} nicht zugeordnet)"
        )
        if unmatched_files:
            self.update_progress(f"Nicht zugeordnete Dateien (erste 5): {unmatched_files[:5]}")
        
        return len(final_file_list)


class ProgressGUI:
    """Separates Fenster für die Fortschrittsanzeige."""
    
    def __init__(self, parent):
        self.window = Toplevel(parent)
        self.window.title("Playlist-Erstellung läuft...")
        self.window.geometry("600x600")
        self.window.transient(parent)  # Macht das Fenster modal für das Hauptfenster
        self.window.grab_set()  # Blockiert das Hauptfenster
        
        # Frame für Status
        status_frame = Frame(self.window)
        status_frame.pack(pady=10, padx=10, fill="x")
        
        self.status_label = Label(status_frame, text="Initialisiere...", font=("Arial", 10))
        self.status_label.pack()
        
        self.progress_label = Label(status_frame, text="0/0", font=("Arial", 9), fg="gray")
        self.progress_label.pack()
        
        # Textbereich für detaillierte Ausgabe
        text_frame = Frame(self.window)
        text_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.text_widget = Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, height=15)
        self.text_widget.pack(side="left", fill="both", expand=True)
        self.text_widget.config(state="disabled")
        
        scrollbar.config(command=self.text_widget.yview)
        
        # Aktuelle Aktivität
        activity_frame = Frame(self.window)
        activity_frame.pack(pady=5, padx=10, fill="x")
        
        Label(activity_frame, text="Aktueller Schritt:", font=("Arial", 9, "bold")).pack(anchor="w")
        self.activity_label = Label(activity_frame, text="", font=("Arial", 9), fg="blue")
        self.activity_label.pack(anchor="w")
        
        # Buttons (zuerst versteckt)
        self.button_frame = Frame(self.window)
        self.button_frame.pack(pady=10)
        
        self.close_button = Button(self.button_frame, text="Schließen", command=self.close_window, state="disabled")
        self.close_button.pack()
    
    def update_progress(self, message, current=None, total=None):
        """Aktualisiert die Fortschrittsanzeige."""
        if current is not None and total is not None and total > 0:
            percent = (current / total) * 100
            self.progress_label.config(text=f"{current}/{total} ({percent:.1f}%)")
            self.status_label.config(text=f"Fortschritt: {percent:.1f}%")
        
        if message:
            self.activity_label.config(text=message[:80] + "..." if len(message) > 80 else message)
            
            # Füge Nachricht zum Textbereich hinzu
            self.text_widget.config(state="normal")
            self.text_widget.insert("end", f"{message}\n")
            self.text_widget.see("end")  # Automatisch scrollen
            self.text_widget.config(state="disabled")
        
        # GUI aktualisieren
        self.window.update_idletasks()
    
    def show_completion(self, playlists_created, files_added):
        """Zeigt Abschlussmeldung an."""
        self.text_widget.config(state="normal")
        self.text_widget.insert("end", "\n" + "="*50 + "\n")
        self.text_widget.insert("end", f"ERFOLG: {playlists_created} Playlists mit {files_added} Dateien erstellt!\n")
        self.text_widget.insert("end", "="*50 + "\n")
        self.text_widget.config(state="disabled")
        
        self.activity_label.config(text="Playlist-Erstellung abgeschlossen!", fg="green")
        self.status_label.config(text="Fertig!", fg="green")
        self.close_button.config(state="normal")
    
    def show_error(self, error_message):
        """Zeigt Fehlermeldung an."""
        self.text_widget.config(state="normal")
        self.text_widget.insert("end", "\n" + "="*50 + "\n")
        self.text_widget.insert("end", f"FEHLER: {error_message}\n")
        self.text_widget.insert("end", "="*50 + "\n")
        self.text_widget.config(state="disabled")
        
        self.activity_label.config(text="Fehler aufgetreten!", fg="red")
        self.status_label.config(text="Fehler!", fg="red")
        self.close_button.config(state="normal")
    
    def close_window(self):
        """Schließt das Fortschrittsfenster."""
        self.window.grab_release()
        self.window.destroy()


class PlaylistCreatorGUI:
    def __init__(self):
        self.creator = PlaylistCreator()
        self.root = Tk()
        self.root.title("Erweiterter VLC Playlist Creator")
        self.root.geometry("520x380")
        
        self.folder_path = StringVar()
        
        # BooleanVar-Objekte für die Checkbuttons - ALLE DEFAULT AN
        self.combined_var = BooleanVar(value=True)      # Default an
        self.storyline_var = BooleanVar(value=True)     # Default an
        self.parent_dir_var = BooleanVar(value=True)    # Default an
        
        self.setup_gui()
    
    def setup_gui(self):
        # Titel
        title_label = Label(self.root, text="VLC Playlist Creator", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Beschreibung
        desc_label = Label(self.root, text="Erstellt sortierte Playlists für Ihre Medien-Sammlung", wraplength=450)
        desc_label.pack(pady=5)
        
        # Verzeichnis-Auswahl
        frame_browse = Frame(self.root)
        frame_browse.pack(pady=10)
        
        browse_button = Button(frame_browse, text="Verzeichnis auswählen", command=self.browse_directory, width=20)
        browse_button.pack(side="left", padx=5)
        
        self.folder_entry = Entry(frame_browse, textvariable=self.folder_path, width=40)
        self.folder_entry.pack(side="left", padx=5)
        
        # Optionen-Frame
        options_frame = LabelFrame(self.root, text="Optionen:", font=("Arial", 12), padx=10, pady=10)
        options_frame.pack(pady=10, padx=20, fill="x")
        
        Checkbutton(options_frame, text="Kombinierte Playlists erstellen", 
                   variable=self.combined_var).pack(anchor="w", padx=10, pady=2)
        Checkbutton(options_frame, text="Storyline Playlists erstellen", 
                   variable=self.storyline_var).pack(anchor="w", padx=10, pady=2)
        Checkbutton(options_frame, text="Playlists im übergeordneten Ordner speichern", 
                   variable=self.parent_dir_var).pack(anchor="w", padx=10, pady=2)
        
        # Status-Anzeige
        self.status_label = Label(self.root, text="Bereit", fg="gray")
        self.status_label.pack(pady=10)
        
        # Buttons-Frame
        button_frame = Frame(self.root)
        button_frame.pack(pady=10)
        
        # Erstellen-Button
        self.create_button = Button(button_frame, text="Playlists erstellen", 
                              command=self.create_playlists, bg="#4CAF50", fg="white",
                              font=("Arial", 12, "bold"), width=20)
        self.create_button.pack(side="left", padx=10)
        
        # Beenden-Button
        exit_button = Button(button_frame, text="Beenden", command=self.root.quit, width=10)
        exit_button.pack(side="left", padx=10)
    
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.folder_path.set(directory)
            self.status_label.config(text=f"Ausgewählt: {directory}", fg="blue")
    
    def create_playlists(self):
        directory = self.folder_path.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("Fehler", "Bitte wählen Sie ein gültiges Verzeichnis aus.")
            return
        
        # Deaktiviere den Erstellen-Button während der Verarbeitung
        self.create_button.config(state="disabled", text="Wird bearbeitet...")
        self.root.update()
        
        # Öffne Fortschrittsfenster
        progress_window = ProgressGUI(self.root)
        
        # Funktion, die in einem separaten Thread läuft
        def create_playlists_thread():
            try:
                # Setze die Einstellungen basierend auf den Checkbuttons
                self.creator.create_combined_playlists = self.combined_var.get()
                self.creator.create_storyline_playlists = self.storyline_var.get()
                self.creator.save_in_parent_dir = self.parent_dir_var.get()
                
                # Setze den Progress-Callback
                self.creator.progress_callback = progress_window.update_progress
                
                # Lösche zuerst alte Playlists
                deleted = self.creator.delete_old_playlists(directory)
                progress_window.update_progress(f"{deleted} alte Playlists gelöscht")
                
                # Erstelle neue Playlists
                playlists_created, files_added = self.creator.create_playlists_recursively(directory)
                
                # Zeige Erfolgsmeldung im Fortschrittsfenster
                progress_window.show_completion(playlists_created, files_added)
                
                # Aktualisiere Hauptfenster-Status
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Fertig! {playlists_created} Playlists mit {files_added} Dateien erstellt.", 
                    fg="green"
                ))
                
            except Exception as e:
                error_msg = str(e)
                progress_window.show_error(error_msg)
                self.root.after(0, lambda: self.status_label.config(text="Fehler aufgetreten!", fg="red"))
            finally:
                # Reaktiviere den Button im Hauptfenster
                self.root.after(0, lambda: self.create_button.config(state="normal", text="Playlists erstellen"))
                # Entferne den Callback
                self.creator.progress_callback = None
        
        # Starte den Thread für die Playlist-Erstellung
        thread = threading.Thread(target=create_playlists_thread, daemon=True)
        thread.start()
        
        # Aktualisiere das Hauptfenster, während wir warten
        self.root.update()
    
    def run(self):
        self.root.mainloop()


def main():
    app = PlaylistCreatorGUI()
    app.run()


if __name__ == "__main__":
    main()
