#!/usr/bin/env python3
"""Assemble a static GitHub Pages site from generated schemas and Swagger UI.

The script turns the generated ``<folder>/deploy`` content into a browsable
site with navigation pages and copies it into a staging directory that can be
published as-is:

    _site/index.html
    _site/<folder>/index.html
    _site/<folder>/deploy/schemas/index.html
    _site/<folder>/deploy/swagger-ui/index.html
    _site/.nojekyll
"""
import argparse
import html
import json
import shutil
from pathlib import Path

STYLE = """      body {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: #fafafa;
        color: #212529;
      }
      header {
        background: #17324d;
        color: #fff;
        padding: 2rem 2.5rem;
      }
      header h1 {
        margin: 0;
        font-size: 1.8rem;
      }
      header p {
        margin: 0.5rem 0 0;
        opacity: 0.85;
      }
      nav {
        margin-top: 0.75rem;
      }
      nav a {
        color: #9ecbff;
        text-decoration: none;
        font-size: 0.9rem;
      }
      nav a:hover {
        text-decoration: underline;
      }
      main {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 2.5rem;
      }
      ul {
        list-style: none;
        padding: 0;
      }
      li {
        margin-bottom: 0.75rem;
      }
      a.card {
        display: block;
        padding: 1rem 1.25rem;
        background: #fff;
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        color: #0366d6;
        text-decoration: none;
        font-weight: 500;
      }
      a.card:hover {
        border-color: #0366d6;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
      }
      a.card .desc {
        display: block;
        color: #6a737d;
        font-weight: 400;
        font-size: 0.9rem;
        margin-top: 0.25rem;
      }"""

# Root page uses plain links (no navigation, no card class).
ROOT_STYLE = """      body {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: #fafafa;
        color: #212529;
      }
      header {
        background: #17324d;
        color: #fff;
        padding: 2rem 2.5rem;
      }
      header h1 {
        margin: 0;
        font-size: 1.8rem;
      }
      header p {
        margin: 0.5rem 0 0;
        opacity: 0.85;
      }
      main {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 2.5rem;
      }
      ul {
        list-style: none;
        padding: 0;
      }
      li {
        margin-bottom: 0.75rem;
      }
      a {
        display: block;
        padding: 1rem 1.25rem;
        background: #fff;
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        color: #0366d6;
        text-decoration: none;
        font-weight: 500;
      }
      a:hover {
        border-color: #0366d6;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
      }
      a .desc {
        display: block;
        color: #6a737d;
        font-weight: 400;
        font-size: 0.9rem;
        margin-top: 0.25rem;
      }"""

PAGE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{style}
    </style>
  </head>
  <body>
{body}
  </body>
</html>
"""


def title_from_folder(folder: str) -> str:
    """Turn a folder name such as ``example_building_automation`` into a title."""
    return folder.replace("_", " ").replace("-", " ").title()


def render_page(title: str, body: str, style: str = STYLE) -> str:
    return PAGE.format(title=html.escape(title), style=style, body=body)


def render_list_body(header_title, subtitle, nav_href, nav_label, items):
    nav = ""
    if nav_href:
        nav = f'\n      <nav><a href="{nav_href}">&larr; {html.escape(nav_label)}</a></nav>'
    body = (
        f"    <header>\n"
        f"      <h1>{html.escape(header_title)}</h1>\n"
        f"      <p>{html.escape(subtitle)}</p>{nav}\n"
        f"    </header>\n"
        f"    <main>\n"
        f"      <ul>\n"
        f"{items}\n"
        f"      </ul>\n"
        f"    </main>"
    )
    return body


def card_item(name: str, description: str, href: str) -> str:
    return (
        f'        <li><a class="card" href="{href}">{html.escape(name)}'
        f'<span class="desc">{html.escape(description)}</span></a></li>'
    )


def card_block(name: str, description: str, href: str) -> str:
    return (
        f'        <li>\n'
        f'          <a class="card" href="{href}">\n'
        f'            {html.escape(name)}\n'
        f'            <span class="desc">{html.escape(description)}</span>\n'
        f'          </a>\n'
        f'        </li>'
    )


def read_schema_entries(schema_dir: Path):
    """Return sorted ``(name, description)`` pairs for every JSON schema."""
    entries = []
    for schema_file in sorted(schema_dir.glob("*.json")):
        description = ""
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                description = json.load(f).get("description", "")
        except (json.JSONDecodeError, OSError):
            pass
        entries.append((schema_file.stem, description))
    return entries


def discover_model_folders(repo_root: Path):
    """Find top-level folders that contain a ``data_models.py``."""
    folders = []
    for entry in sorted(repo_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith(".") or entry.name == "utils":
            continue
        if (entry / "data_models.py").exists():
            folders.append(entry.name)
    return folders


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_model_pages(folder: str, site_dir: Path) -> None:
    """Generate the folder landing page and its schemas/swagger listing pages."""
    title = title_from_folder(folder)
    folder_site = site_dir / folder

    # Folder landing page.
    cards = "\n".join([
        card_block("Schemas", "JSON schemas for each Fiware data model.",
                   "deploy/schemas/index.html"),
        card_block("Swagger UI", "Interactive API documentation for each data model.",
                   "deploy/swagger-ui/index.html"),
    ])
    body = render_list_body(title, f"Data models for {title.lower()}.",
                            "../index.html", "N5GEH Data Models", cards)
    write_file(folder_site / "index.html", render_page(title, body))

    # Schemas listing page.
    schemas_dir = folder_site / "deploy" / "schemas"
    entries = read_schema_entries(schemas_dir)
    items = "\n".join(
        card_item(name, description, f"{name}.json")
        for name, description in entries
    )
    body = render_list_body("Schemas", "JSON schemas for each Fiware data model.",
                            "../../index.html", title, items)
    write_file(schemas_dir / "index.html", render_page("Schemas", body))

    # Swagger UI listing page.
    swagger_dir = folder_site / "deploy" / "swagger-ui"
    items = "\n".join(
        card_item(name, description, f"{name}/index.html")
        for name, description in entries
    )
    body = render_list_body("Swagger UI",
                            "Interactive API documentation for each data model.",
                            "../../index.html", title, items)
    write_file(swagger_dir / "index.html", render_page("Swagger UI", body))


def build_root_page(folders, site_dir: Path) -> None:
    title = "N5GEH Data Models"
    items = []
    for folder in folders:
        folder_title = title_from_folder(folder)
        items.append(
            f'        <li>\n'
            f'          <a href="{folder}/index.html">\n'
            f'            {html.escape(folder_title)}\n'
            f'            <span class="desc">JSON schemas and Swagger UI for '
            f'{html.escape(folder_title.lower())} data models.</span>\n'
            f'          </a>\n'
            f'        </li>'
        )
    items_html = "\n".join(items)
    body = (
        f"    <header>\n"
        f"      <h1>{title}</h1>\n"
        f"      <p>Browse the data models published in this repository.</p>\n"
        f"    </header>\n"
        f"    <main>\n"
        f"      <ul>\n"
        f"{items_html}\n"
        f"      </ul>\n"
        f"    </main>"
    )
    write_file(site_dir / "index.html", render_page(title, body, style=ROOT_STYLE))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_root",
        help="Folder holding generated schemas/ and swagger-ui/ "
             "(e.g. example_building_automation/deploy)")
    parser.add_argument("--site-root", default="_site",
                        help="Staging directory that is published (default: _site)")
    parser.add_argument("--repo-root", default=".",
                        help="Repository root used to discover data model folders")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_root = Path(args.output_root)
    if not output_root.is_dir():
        raise NotADirectoryError(f"Output root not found: {output_root}")

    folder = output_root.parent.name
    site_dir = Path(args.site_root)
    model_dir = site_dir / folder

    # Copy the generated deploy tree into the staging directory.
    if model_dir.exists():
        shutil.rmtree(model_dir)
    model_dir.mkdir(parents=True)
    shutil.copytree(output_root, model_dir / "deploy")

    # Make sure schemas and swagger-ui directories exist even when empty.
    (model_dir / "deploy" / "schemas").mkdir(parents=True, exist_ok=True)
    (model_dir / "deploy" / "swagger-ui").mkdir(parents=True, exist_ok=True)

    build_model_pages(folder, site_dir)
    build_root_page(discover_model_folders(repo_root), site_dir)

    # GitHub Pages should serve the site verbatim.
    write_file(site_dir / ".nojekyll", "")

    print(f"Generated site in {site_dir} for folder '{folder}'.")


if __name__ == "__main__":
    main()
