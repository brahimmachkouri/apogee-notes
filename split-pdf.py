#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Découpe un PDF contenant tous les relevés de notes en fichiers regroupés par étudiant,
en utilisant l'INE pour détecter les changements d'étudiant,
et en incluant le nom et prénom dans le nom de fichier.
Ignore la première page (page de garde).
"""
import os
import re
import argparse
import logging
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber


def extract_student_info(page) -> dict:
    """
    Extrait nom/prénom, N° étudiant et INE d'une page via pdfplumber.
    Retourne {'nom_prenom', 'num_etudiant', 'ine'}.
    """
    text = page.extract_text(x_tolerance=2, y_tolerance=2)
    lines = text.splitlines() if text else []
    info = {'nom_prenom': None, 'num_etudiant': None, 'ine': None}
    for i, line in enumerate(lines):
        t = line.strip()
        if 'Session unique' in t and i+1 < len(lines):
            next_line = lines[i+1].strip()
            if next_line:
                info['nom_prenom'] = next_line
        m = re.search(r"N°\s*Etudiant\s*[:\-]?\s*(\d+)", t)
        if m:
            info['num_etudiant'] = m.group(1)
        m2 = re.search(r"INE\s*[:\-]?\s*([A-Z0-9]+)", t)
        if m2:
            info['ine'] = m2.group(1)
        if all(info.values()):
            break
    return info


def split_by_student(pdf_path: str, output_dir: str):
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    # Pad pour le nom de fichier si besoin
    pad = len(str(total_pages))

    base = os.path.splitext(os.path.basename(pdf_path))[0]
    outdir = os.path.join(output_dir, f"{base}_per_student")
    os.makedirs(outdir, exist_ok=True)

    current_ine = None
    current_writer = None
    current_info = {}
    page_count = []

    with pdfplumber.open(pdf_path) as pdf:
        # Parcours en ignorant la première page (page de garde)
        for idx, page in enumerate(pdf.pages[1:], start=2):
            info = extract_student_info(page)
            ine = info.get('ine')
            # Si nouveau relevé (INE change ou premier étudiant)
            if current_writer is None or ine != current_ine:
                # Sauvegarde du relevé précédent
                if current_writer:
                    safe_nom = re.sub(r'[^A-Za-z0-9]', '_', current_info.get('nom_prenom', ''))
                    filename = f"{base}_{safe_nom}_{current_ine}_{current_info.get('num_etudiant','')}.pdf"
                    path = os.path.join(outdir, filename)
                    with open(path, 'wb') as f:
                        current_writer.write(f)
                    print(f"Écrit : {path} ({len(page_count)} pages)")
                # Démarrage nouveau relevé
                current_writer = PdfWriter()
                current_ine = ine
                current_info = info
                page_count = []
            # Ajout de la page au writer courant
            current_writer.add_page(reader.pages[idx-1])
            page_count.append(idx)

        # Sauvegarde du dernier relevé si existant
        if current_writer:
            safe_nom = re.sub(r'[^A-Za-z0-9]', '_', current_info.get('nom_prenom', ''))
            filename = f"{base}_{safe_nom}_{current_ine}_{current_info.get('num_etudiant','')}.pdf"
            path = os.path.join(outdir, filename)
            with open(path, 'wb') as f:
                current_writer.write(f)
            print(f"Écrit : {path} ({len(page_count)} pages)")

    print(f"Terminé, {len(os.listdir(outdir))} fichiers générés dans '{outdir}'.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Split PDF en fichiers par étudiant sur INE, en ignorant la page de garde."
    )
    parser.add_argument('pdf_path', help='PDF contenant tous les relevés')
    parser.add_argument('-o', '--output-dir', default='.', help='Répertoire de sortie')
    parser.add_argument('-l', '--log-file', dest='log_file', help='Fichier de log')
    args = parser.parse_args()

    if args.log_file:
        logging.basicConfig(
            filename=args.log_file,
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s'
        )
    else:
        logging.disable(logging.CRITICAL)

    split_by_student(args.pdf_path, args.output_dir)
