#!/usr/bin/env python3
import os
import subprocess
import shutil
import sys


def get_changed_files():
    """
    Ermittelt anhand von GITHUB_SHA die im Commit geänderten Dateien.
    Falls GITHUB_SHA nicht gesetzt ist, wird None zurückgegeben.
    """
    sha = os.environ.get("GITHUB_SHA")
    if not sha:
        print("Keine GITHUB_SHA gefunden – es werden alle data_models.py verarbeitet.",
              file=sys.stderr)
        return None
    try:
        # Ermittelt alle geänderten Dateien des Commits
        result = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            universal_newlines=True
        )
        changed_files = set(result.splitlines())
        return changed_files
    except Exception as e:
        print(f"Fehler beim Ermitteln der geänderten Dateien: {e}", file=sys.stderr)
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

    # Schritt 8: Falls Änderungen vorgenommen wurden, commiten und in den development Branch pushen
    if processed_any:
        try:
            subprocess.check_call(["git", "config", "user.name", "github-actions"])
            subprocess.check_call(
                ["git", "config", "user.email", "github-actions@github.com"])
            subprocess.check_call(["git", "add", "."])
            # Commit: Falls keine Änderungen vorhanden sind, wird commit fehlschlagen – dies ignorieren
            subprocess.call(["git", "commit", "-m",
                             "Update generated schemas and OpenAPI docs [skip ci]"])
            subprocess.check_call(["git", "push", "origin", "development"])
            print("Änderungen wurden in den development Branch gepusht.")
        except Exception as e:
            print(f"Fehler beim Commit/Pushe der Änderungen: {e}", file=sys.stderr)
    else:
        print("Keine Änderungen vorgenommen – nichts zu pushen.")


if __name__ == "__main__":
    main()