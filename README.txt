# VLC Playlist Creator 🚀

Ein radikal effizientes Python-Tool zur automatischen Erstellung und Verwaltung von **VLC-kompatiblen Playlists (.xspf)** aus tief verschachtelten Medienordnern – mit intelligenter natürlicher Sortierung und zero footprint.

## ✨ Hauptfunktionen

- **Komplette Bereinigung**: Löscht vorab **alle** alten `.xspf` und `.m3u` im gesamten Verzeichnisbaum  
  → Kein Playlist-Chaos mehr, immer aktuelle Listen
- **Intelligente natürliche Sortierung**  
  Erkennt automatisch: `S01E01`, `01 - Titel`, `Folge 12`, `Titel Teil II (2023)`, `Movie 3`, römische Zahlen, etc.
- **Storyline-Playlists** aus `Storyline.txt`  
  Perfekt für Hörspiele, Marvel-Chronologie, Director’s Cut-Reihenfolgen, etc.
- **Kombinierte Playlists** (optional)  
  Fasst alle Unterordner-Playlists + lokale Dateien zu einer einzigen zusammen – **ohne Duplikate und ohne „(Kombiniert)“ im Namen**
- **Playlists im Elternordner speichern** (optional)  
  Hält deine Medienordner sauber
- **Live-Fortschrittsfenster** mit detailliertem Log
- **100 % portabel** – keine Konfiguration, keine Logs, keine Spuren

## 📁 Unterstützte Medienformate

`.mp4` · `.mkv` · `.avi` · `.mp3` · `.m4a` · `.flac` · `.wav`

## 🛠 Technologie

- **Python 3** (nur Standardbibliothek!)
- **GUI**: tkinter
- **Playlist-Format**: XSPF (`file:///`-URLs, Unicode-sicher, VLC-liebt-es)

## 🚀 Nutzung

1. Python 3 installiert? → Ja/Nein → Egal, es gibt auch eine **fertige .exe**  
2. Skript starten → `VLCPlaylistCreator.py` oder die EXE aus den Releases
3. Ordner auswählen → Optionen anpassen → **„Playlists erstellen“**
4. Fertig. In Sekunden bis Minuten ist deine gesamte Mediathek perfekt organisiert.

**Download der portablen EXE (keine Installation nötig):**  
➡️ https://github.com/blobb999/VLCPlaylistCreator/releases/tag/1.0

## 🎯 Philosophie

Dieses Tool ist **absichtlich kompromisslos** gebaut:

- Wer startet, will einen sauberen Neuanfang → alte Playlists werden komplett entfernt  
- Keine Konfigurationsdateien, keine Logs → wirklich portabel und spurlos  
- Kein „Abbrechen“ → Wer das alte Haus abreißt, baut das neue auch fertig  
- Kein Schnickschnack → Nur das, was wirklich gebraucht wird

Perfekt für DataHoarder, Anime-Sammler, Hörspiel-Fans und alle, die ihre Medienbibliothek **ernst nehmen**.

---

### 👨‍💻 Über dieses Projekt

Alle meine Repositories entstehen mit KI-Unterstützung. Ich bin der Produktmanager meiner eigenen lang gehegten Ideen:  
Ich sage, **was** ich will – die KI hilft beim **wie**.  
Der Fokus liegt auf Pragmatismus, Automatisierung und persönlicher Effizienz – nicht auf Perfektion nach Lehrbuch.

**Du darfst:**
- Den Code klonen, ändern, weiterentwickeln, commercial nutzen  
- Ihn in deine eigenen Projekte einbauen  
- Ihn als Basis für etwas Größeres verwenden

**Ich würde mich freuen über:**
- Einen ⭐ Star auf GitHub  
- Ein kurzes „Hey, ich hab’s weiterentwickelt!“  
- Oder einfach ein stilles Lächeln, weil es dir Zeit und Nerven spart 😄

> **Made with frustration and love – for people who hate playlist chaos.**

---