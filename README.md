# Projekt: Gewächshaus-Steuerungssystem für Floristik GmbH

## Projektbeschreibung

Dieses Projekt zielt darauf ab, ein bestehendes Gewächshaus-Steuerungssystem für die **Floristik GmbH** in Betrieb zu nehmen und zu erweitern. Das ursprüngliche System bietet grundlegende Temperaturüberwachung mit einem DHT11-Sensor und zeigt die Temperatur auf einer 7-Segment-LED-Anzeige an. Allerdings ist es derzeit nicht betriebsbereit.

## Projektnutzung

1.  Zunächst klonen Sie bitte das Greenhouse-Git-Projekt über:
    git clone https://github.com/vertok/Greenhouse.git
2.  Wechseln Sie zum Projektverzeichnis mit:
    cd Greenhouse
3.  Installieren Sie das Packet via pip install -e .
4.  
5. (um alle entstehende Fragen zu klären lesen Sie die Dokumentation unter doc/build/simplepdf/greenhouse.pdf)

## Hauptaufgaben

Das Projekt umfasst folgende Hauptaufgaben:

-   **Inbetriebnahme:** Das bestehende System in einen betriebsbereiten Zustand versetzen, um grundlegende Temperatur-/Feuchtigkeitsüberwachung und -anzeige zu ermöglichen.
-   **Erweiterung:** Schrittweise Erweiterung der Systemfähigkeiten durch Integration neuer Sensoren (z.B. Luftfeuchtigkeit, Bodenfeuchtigkeit, Licht) und Aktoren (z.B. Belüftung, Bewässerung).
-   **Softwareentwicklung:** Entwicklung von Python-Skripten für:
    -   Verwaltung der Hardwarekomponenten.
    -   Implementierung der Steuerungslogik basierend auf Sensorwerten.
    -   Protokollierung von Daten in einer SQLite-Datenbank.
-   **Datenbankintegration:** Nutzung einer SQLite-Datenbank zur Speicherung von Sensorwerten für Analysen und zukünftige Verwendung in Steuerungsalgorithmen.
-   **Dokumentation:** Bereitstellung umfassender Dokumentation, einschließlich:
    -   Flussdiagramme/Strukturdiagramme (PAP)
    -   Gut kommentierter Python-Code
    -   Schaltpläne und andere relevante technische Details

## Entwicklungsansatz

Das Projekt folgt einem iterativen Entwicklungsansatz, bei dem jede Version auf der vorherigen aufbaut.

-   **Version 1.0:** Konzentration auf die Inbetriebnahme des ursprünglichen Systems und Implementierung grundlegender Temperatur-/Feuchtigkeitsprotokollierung in der Datenbank.
-   **Version 3.0:** Vollständige Funktionalität mit Datenerfassung von verschiedenen Sensoren, Anzeige verschiedener Informationen auf anderen Sensoren, Protokollierung von Daten mittels Logging und Speicherung aller Messungen in der Datenbank.

## Auftraggeber

**Floristik GmbH**
Kaditzer Straße 4-10
01139 Dresden
