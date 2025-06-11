#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extrait les notes d'un relevé de notes au format PDF
et génère un fichier CSV avec les métadonnées et le tableau de notes.

Il faut renseigner les tags de matière dans le code pour que l'extraction
soit correcte. Les tags sont utilisés pour identifier les matières
et les résultats dans le tableau de notes.

Pour l'instant, les tags sont :
UE, JR, JS, WR, WS, OPTIONS
"""

import fitz  # PyMuPDF pour l'extraction textuelle
import pdfplumber  # pour l'extraction des tableaux
import csv
import os
import re
import argparse
import logging
from tqdm import tqdm  # pour la barre de progression

# Définition centrale des tags de matière
TAG_LIST = ('UE', 'JR', 'JS', 'WR', 'WS', 'OPTIONS')

def get_formation_name(pdf_path: str) -> str:
    """
    Ouvre le PDF avec PyMuPDF et extrait le nom
    de la formation, situé entre le prénom-nom et la chaîne 'N° Etudiant'.
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    text = page.get_text()
    doc.close()

    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^N[°º]\s*Etudiant", line.strip(), re.IGNORECASE):
            # revenir à la ligne précédente non vide
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            return lines[j].strip()

    raise ValueError("Nom de la formation introuvable dans le PDF.")


def extraire_notes_vers_csv(pdf_path: str, output_dir: str) -> None:
    """
    Extrait les notes et métadonnées d'un relevé PDF et génère un CSV dans output_dir.
    Gère les tableaux multi-pages en mémorisant l'entête et en continuant sur les pages suivantes.
    """
    if not os.path.exists(pdf_path):
        logging.error(f"Fichier introuvable : {pdf_path}")
        return

    # Extraction du nom de formation
    try:
        formation = get_formation_name(pdf_path)
        logging.info(f"Formation détectée: {formation}")
    except Exception as e:
        logging.error(f"Erreur extraction formation: {e}")
        formation = ""

    # Extraction des métadonnées de la page 1
    nom_prenom = num_etudiant = ine = date_naissance = lieu_naissance = "Inconnu"
    with pdfplumber.open(pdf_path) as pdf:
        page0 = pdf.pages[0]
        texte_page = page0.extract_text(x_tolerance=2, y_tolerance=2)
        lines = texte_page.splitlines()
        for i, line in enumerate(lines):
            t = line.strip()
            if 'Session unique' in t:
                for j in range(i+1, len(lines)):
                    if lines[j].strip():
                        nom_prenom = lines[j].strip()
                        break
            m = re.search(r"N°\s*Etudiant\s*[:\-]?\s*(\d+)", t)
            if m:
                num_etudiant = m.group(1)
            m = re.search(r"INE\s*[:\-]?\s*([A-Z0-9]+)", t)
            if m:
                ine = m.group(1)
            m = re.search(r"N[ée]e?\s+le\s*[:]?\s*(\d{1,2}\s+[^\d]+?\s+\d{4})(?:\s+à\s*[:]?\s*(.+))?", t, re.IGNORECASE)
            if m:
                date_naissance = m.group(1).strip()
                if m.group(2):
                    lieu_naissance = m.group(2).strip()
            if lieu_naissance == "Inconnu":
                m2 = re.search(r"^à\s*[:]?(.+)", t)
                if m2:
                    lieu_naissance = m2.group(1).strip()

        logging.info(f"Métadonnées '{os.path.basename(pdf_path)}' : Nom={nom_prenom}, Étudiant={num_etudiant}, INE={ine}, Naissance={date_naissance}, Lieu={lieu_naissance}")
    
    # Préparation du parcours multi-pages
    last_header = None
    entetes = ['Matière','Note/Barème','Résultat','Session','Crédits']
    lignes = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                header = [c.strip() if c else '' for c in table[0]]
                if 'Note/Barème' in header:
                    last_header = header
                    data_rows = table[1:]
                elif last_header:
                    # suite de tableau si la première cellule ressemble à une matière
                    first_cell = table[0][0] if table and table[0] and table[0][0] else ''
                    if not any(tag in first_cell for tag in (TAG_LIST)):
                        continue
                    data_rows = table
                else:
                    continue

                for row in data_rows:
                    if not row or not row[0]:
                        continue
                    mat = row[0].replace('\n',' ').strip()
                    if not any(tag in mat for tag in (TAG_LIST)):
                        continue
                    idx_note = last_header.index('Note/Barème')
                    idx_res = last_header.index('Résultat')
                    idx_sess = last_header.index('Session')
                    idx_cr = last_header.index('Crédits')
                    note = row[idx_note].strip() if len(row)>idx_note and row[idx_note] else 'N/A'
                    res = row[idx_res].strip() if len(row)>idx_res and row[idx_res] else ''
                    sess = row[idx_sess].strip() if len(row)>idx_sess and row[idx_sess] else ''
                    cr = row[idx_cr].strip() if len(row)>idx_cr and row[idx_cr] else ''
                    lignes.append([mat, note, res, sess, cr])

    if not lignes:
        logging.warning(f"Aucune table de notes trouvée dans {pdf_path}")
        return

    # Création du CSV avec métadonnées et même nommage qu'avant
    safe = re.sub(r'[^a-zA-Z0-9]', '_', nom_prenom)
    csv_name = f"notes_{safe}_{num_etudiant}.csv"
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, csv_name)

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        metas_titles = ['Nom et Prénom','N° Étudiant','INE','Date de naissance','Lieu de naissance','Formation']
        metas_vals = [nom_prenom, num_etudiant, ine, date_naissance, lieu_naissance, formation]
        writer.writerow(metas_titles)
        writer.writerow(metas_vals)
        writer.writerow([])
        writer.writerow(entetes)
        writer.writerows(lignes)

    logging.info(f"CSV généré : {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Extrait les notes d'un PDF Apogée et génère un CSV multi-pages.")
    parser.add_argument("pdf_file", help="Fichier PDF ou répertoire à traiter")
    parser.add_argument("-o", "--output-dir", default=".", help="Répertoire de sortie des CSV")
    parser.add_argument("-l", "--log-file", dest="log_file", help="Chemin vers le fichier de log")
    args = parser.parse_args()

    if args.log_file:
        logging.basicConfig(filename=args.log_file, level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s", filemode='w')
    else:
        logging.disable(logging.CRITICAL)

    pdf_list = []
    if os.path.isfile(args.pdf_file) and args.pdf_file.lower().endswith('.pdf'):
        pdf_list = [args.pdf_file]
    elif os.path.isdir(args.pdf_file):
        pdf_list = [os.path.join(args.pdf_file, f) for f in os.listdir(args.pdf_file) if f.lower().endswith('.pdf')]
    else:
        print(f"Erreur : '{args.pdf_file}' n'existe pas.")
        return

    for pdf_path in tqdm(pdf_list, desc="Traitement des PDF"):
        extraire_notes_vers_csv(pdf_path, args.output_dir)

    print("Traitement terminé.")
    if args.log_file:
        print(f"Logs disponibles dans: {args.log_file}")


if __name__ == '__main__':
    main()
