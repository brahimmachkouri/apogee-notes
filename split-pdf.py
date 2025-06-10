#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extrait chaque page d'un PDF et les enregistre 
individuellement dans un dossier dédié.
"""

import os
import argparse
from PyPDF2 import PdfReader, PdfWriter

def extract_pages(pdf_path: str):
    """
    Extrait chaque page du PDF situé à pdf_path
    et enregistre chaque page nom_fichier_numéro.pdf
    (avec zéro-padding) dans un dossier nommé nom_fichier_pages.
    """
    # Charger le PDF
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    # Calcul de la largeur du padding (ex. 3 pour 100 pages, 2 pour 12 pages)
    pad_width = len(str(total_pages))

    # Base name sans extension
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    # Dossier de sortie : <base_name>_pages
    output_dir = f"{base_name}_pages"
    os.makedirs(output_dir, exist_ok=True)

    for idx, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        # Nom de sortie : nomFichier_001.pdf, nomFichier_002.pdf, …
        output_filename = f"{base_name}_{idx:0{pad_width}d}.pdf"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, "wb") as out_file:
            writer.write(out_file)
        print(f"Enregistré : {output_path}")

    print(f"\nExtraction terminée : {total_pages} pages créées dans '{output_dir}'.")

def main():
    parser = argparse.ArgumentParser(
        description="Extrait chaque page d'un PDF et les enregistre individuellement avec zéro-padding."
    )
    parser.add_argument(
        "pdf_path",
        help="Fichier PDF à splitter."
    )
    args = parser.parse_args()
    extract_pages(args.pdf_path)

if __name__ == "__main__":
    main()
