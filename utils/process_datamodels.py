#!/usr/bin/env python3
import os
import subprocess
import shutil
import sys
import json


def get_changed_files():
    """
    Ermittelt die im Push-Event geänderten Dateien.
    Verwendet zunächst den GitHub Event-Payload (GITHUB_EVENT_PATH) zum Vergleich
    von before und after. Falls dies fehlschlägt, wird ein Fallback auf GITHUB_SHA verwendet.
    """
    # Versuche, die Datei mit dem GitHub-Event-Payload zu laden.
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and os.path.exists(event_path):
        try:
            with open(event_path, "r") as f:
                event_data = json.load(f)
            before = event_data.get("before")
            after = event_data.get("after")
            if before and after:
                # Ermittle die Liste der geänderten Dateien zwischen before und after.
                result = subprocess.check_output(
                    ["git", "diff", "--name-only", before, after],
                    universal_newlines=True
                )
                changed_files = set(result.splitlines())
                if changed_files:
                    print(
                        f"Ermittelte geänderte Dateien aus dem Event-Payload: {changed_files}")
                    return changed_files
                else:
                    print("Kein Unterschied zwischen 'before' und 'after' gefunden.",
                          file=sys.stderr)
            else:
                print(
                    "Das Event-Payload enthält nicht die Felder 'before' und/oder 'after'.",
                    file=sys.stderr)
        except Exception as e:
            print(f"Fehler beim Laden oder Verarbeiten von {event_path}: {e}",
                  file=sys.stderr)

    # Fallback: Verwende GITHUB_SHA, falls der Event-Payload nicht verfügbar oder unvollständig ist.
    sha = os.environ.get("GITHUB_SHA")
    if not sha:
        print("Keine GITHUB_SHA gefunden – es werden alle data_models.py verarbeitet.",
              file=sys.stderr)
        return None
    try:
        result = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            universal_newlines=True
        )
        changed_files = set(result.splitlines())
        print(f"Ermittelte geänderte Dateien über GITHUB_SHA: {changed_files}")
        return changed_files
    except Exception as e:
        print(f"Fehler beim Ermitteln der geänderten Dateien mittels GITHUB_SHA: {e}",
              file=sys.stderr)
        return None


def process_folder(folder, changed_files):
    """
    Für einen Ordner prüft diese Funktion, ob eine data_models.py existiert.
    Falls ja und die data_models.py in diesem Commit neu/aktualisiert wurde,
    werden nacheinander serializer.py und openapi_generator.py (aus utils)
    in den Ordner kopiert, ausgeführt und wieder gelöscht.
    """
    data_models_path = os.path.join(folder, "data_models.py")
    if not os.path.exists(data_models_path):
        return False  # kein data_models.py -> Ordner wird übersprungen

    # Prüfe, ob data_models.py in diesem Commit geändert wurde:
    if changed_files is not None:
        rel_path = os.path.relpath(data_models_path)
        if rel_path not in changed_files:
            print(
                f"{data_models_path} wurde in diesem Commit nicht geändert. Überspringe {folder}.")
            return False
        else:
            print(f"{data_models_path} wurde geändert – bearbeite {folder}.")
    else:
        print(f"Bearbeite {data_models_path}, da keine Änderungsinfo vorliegt.")

    # Schritt 3: serializer.py kopieren und ausführen
    serializer_src = os.path.join("utils", "serializer.py")
    serializer_dest = os.path.join(folder, "serializer.py")
    try:
        shutil.copy(serializer_src, serializer_dest)
        print(f"Copied serializer.py to {folder}")
    except Exception as e:
        print(f"Fehler beim Kopieren von serializer.py in {folder}: {e}", file=sys.stderr)
        return False

    try:
        subprocess.check_call(["python", "serializer.py"], cwd=folder)
        print(f"serializer.py in {folder} ausgeführt")
    except Exception as e:
        print(f"Fehler bei der Ausführung von serializer.py in {folder}: {e}",
              file=sys.stderr)

    # Schritt 4: Kopie löschen
    try:
        os.remove(serializer_dest)
        print(f"serializer.py in {folder} gelöscht")
    except Exception as e:
        print(f"Fehler beim Löschen von serializer.py in {folder}: {e}", file=sys.stderr)

    # Schritt 5: openapi_generator.py kopieren und ausführen
    openapi_src = os.path.join("utils", "openapi_generator.py")
    openapi_dest = os.path.join(folder, "openapi_generator.py")
    try:
        shutil.copy(openapi_src, openapi_dest)
        print(f"Copied openapi_generator.py to {folder}")
    except Exception as e:
        print(f"Fehler beim Kopieren von openapi_generator.py in {folder}: {e}",
              file=sys.stderr)
        return False

    try:
        subprocess.check_call(["python", "openapi_generator.py"], cwd=folder)
        print(f"openapi_generator.py in {folder} ausgeführt")
    except Exception as e:
        print(f"Fehler bei der Ausführung von openapi_generator.py in {folder}: {e}",
              file=sys.stderr)

    # Schritt 6: Kopie löschen
    try:
        os.remove(openapi_dest)
        print(f"openapi_generator.py in {folder} gelöscht")
    except Exception as e:
        print(f"Fehler beim Löschen von openapi_generator.py in {folder}: {e}",
              file=sys.stderr)
    return True


def main():
    """
    Hauptfunktion:
      0. Annahme: Python-Umgebung ist per requirements.txt vorbereitet.
      1. Scannt alle Ordner (außer utils) im Repo.
      2. Falls data_models.py existiert, prüft, ob diese in diesem Commit geändert wurde.
      3. Ist dies der Fall, werden serializer.py und openapi_generator.py temporär in den Ordner kopiert
         und ausgeführt.
      4. Zum Schluss werden alle Änderungen in den development Branch gepusht.
    """
    cwd = os.getcwd()
    print(f"Aktueller Arbeitsordner: {cwd}")
    items = os.listdir(cwd)
    # Alle Ordner außer "utils" (und versteckte Ordner) prüfen
    folders = [item for item in items if
               os.path.isdir(item) and item != "utils" and not item.startswith(".")]
    changed_files = get_changed_files()
    print(f"Geänderte Dateien: {changed_files}")
    processed_any = False

    for folder in folders:
        data_models_path = os.path.join(folder, "data_models.py")
        if os.path.exists(data_models_path):
            print(f"Gefunden: data_models.py in Ordner '{folder}'")
            processed = process_folder(folder, changed_files)
            if processed:
                processed_any = True
        else:
            print(f"Kein data_models.py in Ordner '{folder}' gefunden – überspringe.")

    # Schritt 8: Falls Änderungen vorgenommen wurden, committen und in den aktuellen Branch pushen
    if processed_any:
        try:
            subprocess.check_call(["git", "config", "user.name", "github-actions"])
            subprocess.check_call(
                ["git", "config", "user.email", "github-actions@github.com"])
            subprocess.check_call(["git", "add", "."])
            # Commit: Falls keine Änderungen vorhanden sind, wird commit fehlschlagen – dies ignorieren
            subprocess.call(["git", "commit", "-m",
                             "Update generated schemas and OpenAPI docs [skip ci]"])

            # Ermittle den aktuellen Branch aus der Umgebungsvariable GITHUB_REF
            branch_ref = os.environ.get("GITHUB_REF", "")
            branch = "development"  # Fallback, falls GITHUB_REF nicht gesetzt ist
            if branch_ref.startswith("refs/heads/"):
                branch = branch_ref[len("refs/heads/"):]

            subprocess.check_call(["git", "push", "origin", branch])
            print(f"Änderungen wurden in den Branch '{branch}' gepusht.")
        except Exception as e:
            print(f"Fehler beim Commit/Pushe der Änderungen: {e}", file=sys.stderr)
    else:
        print("Keine Änderungen vorgenommen – nichts zu pushen.")


if __name__ == "__main__":
    main()