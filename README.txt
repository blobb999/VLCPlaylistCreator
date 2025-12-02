# VLC Playlist Creator

Ein Python-Skript zur automatischen Erstellung und Verwaltung von VLC-Playlists (.xspf) aus Mediendateien in Verzeichnisstrukturen.

## Funktionen

Das Skript führt folgende Hauptaufgaben durch:
1.  **Verzeichnisauswahl**: Ermöglicht die Auswahl eines Stammverzeichnisses über eine tkinter-Oberfläche.
2.  **Bereinigung**: Entfernt vorab alte Playlist-Dateien (`.xspf`, `.m3u`) im Zielverzeichnis und allen Unterordnern.
3.  **Playlist-Erstellung**: Erstellt für jedes Verzeichnis, das Mediendateien enthält, eine individuelle Playlist.
4.  **Intelligente Sortierung**: Sortiert Dateien mittels einer natürlichen Sortierlogik, die gängige Namenskonventionen erkennt (z.B. `S01E01`, `Folge 1`, `01. Titel`).
5.  **Storyline-Playlists**: Erkennt `Storyline.txt`-Dateien in einem Ordner und erstellt eine Playlist, in der die Medien in der dort vorgegebenen Reihenfolge erscheinen.
6.  **Kombinierte Playlists**: Fasst alle Playlists aus den Unterordnern eines Verzeichnisses zu einer einzigen kombinierten Playlist zusammen.
7.  **Fortschrittsanzeige**: Zeigt während der Verarbeitung den Fortschritt und eine Zusammenfassung der erstellten Playlists und enthaltenen Dateien an.

## Unterstützte Medienformate
*.mp4*, *.mp3*, *.mkv*, *.avi*, *.flac*, *.wav*, *.m4a*

## Technologie
*   **Sprache**: Python 3
*   **GUI**: tkinter (in der Standardbibliothek enthalten)
*   **Playlist-Format**: XSPF (XML Shareable Playlist Format)

## Nutzung
1.  Stellen Sie sicher, dass Python 3 installiert ist.
2.  Führen Sie das Skript `VLCPlaylistCreator.py` aus.
3.  Wählen Sie im geöffneten Fenster über "Verzeichnis auswählen" den Ordner Ihrer Medienbibliothek.
4.  Konfigurieren Sie die gewünschten Optionen (Storyline-, kombinierte Playlists).
5.  Klicken Sie auf "Playlists erstellen" und beobachten Sie den Fortschritt.

Hier das Binary: https://github.com/blobb999/VLCPlaylistCreator/releases/tag/1.0

---
### Persönlicher Hintergrund
*Alle Repositorys hier sind mit KI-Assistenz programmierte Projekte. Ich agiere dabei wie ein Produktmanager, der lang gehegte Ideen und Werkzeuge für den persönlichen Gebrauch umsetzt. Der Fokus liegt auf der Umsetzung von Ideen, Vereinfachung von Abläufen und Automatisierung – nicht auf industriellen Coding-Standards oder Perfektion.*

*Jeder ist eingeladen, den Code zu klonen, zu modifizieren oder anderweitig zu nutzen. Über einen Stern (Star) auf GitHub, ein Like oder eine kurze Nachricht, falls eine Idee woanders weiterentwickelt wird, würde ich mich freuen.*