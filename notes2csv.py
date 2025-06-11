#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extrait les notes d'un relevé de notes au format PDF
et génère un fichier CSV avec les métadonnées et le tableau de notes.
"""

import fitz  # PyMuPDF pour l'extraction textuelle
import pdfplumber # pour l'extraction des tableaux
import csv
import os
import re
import argparse
import logging
from tqdm import tqdm # pour la barre de progression


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
        if re.match(r"^N[°º]\s*Etudiant\s*[:\-]?", line.strip(), re.IGNORECASE):
            # revenir à la ligne précédente non vide
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            return lines[j].strip()

    raise ValueError("Nom de la formation introuvable dans le PDF.")


def extraire_notes_vers_csv(pdf_path: str, output_dir: str) -> None:
    """
    Extrait les notes et métadonnées d'un relevé PDF et génère un CSV dans output_dir.
    """
    if not os.path.exists(pdf_path):
        logging.error(f"Fichier introuvable : {pdf_path}")
        return

    try:
        formation = get_formation_name(pdf_path)
        logging.info(f"Formation détectée pour '{os.path.basename(pdf_path)}' : {formation}")
    except Exception as e:
        logging.error(f"Erreur extraction formation dans '{os.path.basename(pdf_path)}' : {e}")
        formation = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extraction du texte de la première page pour les métadonnées
            page0 = pdf.pages[0]
            texte_page = page0.extract_text(x_tolerance=2, y_tolerance=2)

            # Extraction des métadonnées
            nom_prenom = num_etudiant = ine = date_naissance = lieu_naissance = "Inconnu"
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
                m = re.search(r"N[ée]e?\s+le\s*[:]?(\d{1,2}\s+[^\d]+?\s+\d{4})(?:\s+à\s*[:]?(.+))?", t, re.IGNORECASE)
                if m:
                    date_naissance = m.group(1).strip()
                    if m.group(2):
                        lieu_naissance = m.group(2).strip()
                if lieu_naissance == "Inconnu":
                    m2 = re.search(r"^à\s*[:]?(.+)", t)
                    if m2:
                        lieu_naissance = m2.group(1).strip()

            logging.info(f"Métadonnées pour '{os.path.basename(pdf_path)}' : Nom={nom_prenom}, Étudiant={num_etudiant}, INE={ine}, Naissance={date_naissance}, Lieu={lieu_naissance}")

            # Extraction du tableau de notes sur toutes les pages
            entetes = ['Matière','Note/Barème','Résultat','Session','Crédits']
            lignes = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    header = [c.strip() if c else '' for c in table[0]]
                    if 'Note/Barème' in header:
                        for row in table[1:]:
                            if not row or not row[0] or not any(tag in row[0] for tag in ('UE','JR','JS','WR','WS','OPTIONS')):
                                continue
                            mat = row[0].replace('\n',' ').strip()
                            note = row[1].strip() if len(row)>1 and row[1] else 'N/A'
                            res = row[2].strip() if len(row)>2 and row[2] else ''
                            sess = row[3].strip() if len(row)>3 and row[3] else ''
                            cr = row[4].strip() if len(row)>4 and row[4] else ''
                            lignes.append([mat,note,res,sess,cr])

            if not lignes:
                logging.warning(f"Aucune table de notes trouvée dans '{os.path.basename(pdf_path)}'")
                return

            # Création du CSV
            safe = re.sub(r'[^a-zA-Z0-9]', '_', nom_prenom)
            csv_name = f"notes_{safe}_{num_etudiant}.csv"
            os.makedirs(output_dir, exist_ok=True)
            csv_path = os.path.join(output_dir, csv_name)

            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                metas_titles = ['Nom et Prénom','N° Étudiant','INE','Date de naissance','Lieu de naissance','Formation']
                metas_vals = [nom_prenom,num_etudiant,ine,date_naissance,lieu_naissance,formation]
                writer.writerow(metas_titles)
                writer.writerow(metas_vals)
                writer.writerow([])
                writer.writerow(entetes)
                writer.writerows(lignes)

            logging.info(f"CSV généré pour '{os.path.basename(pdf_path)}' : {csv_path}")
    except Exception as e:
        logging.error(f"Erreur lors de '{os.path.basename(pdf_path)}' : {e}")


def main():
    parser = argparse.ArgumentParser(description="Extrait les notes d'un PDF issu d'Apogée et génère un CSV.")
    parser.add_argument("pdf_file", help="Fichier PDF ou répertoire à traiter")
    parser.add_argument("-o", "--output-dir", default=".", help="Répertoire de sortie des CSV")
    parser.add_argument("-l", "--log-file", dest="log_file", help="Chemin vers le fichier de log")
    args = parser.parse_args()

    if args.log_file:
        logging.basicConfig(filename=args.log_file, level=logging.INFO, filemode='w',
                            format="%(asctime)s %(levelname)s: %(message)s")
    else:
        logging.disable(logging.CRITICAL)

    # Collecte des fichiers PDF
    pdf_list = []
    if os.path.isfile(args.pdf_file) and args.pdf_file.lower().endswith('.pdf'):
        pdf_list = [args.pdf_file]
    elif os.path.isdir(args.pdf_file):
        for fname in os.listdir(args.pdf_file):
            if fname.lower().endswith('.pdf'):
                pdf_list.append(os.path.join(args.pdf_file, fname))
    else:
        print(f"Erreur : '{args.pdf_file}' n'existe pas.")
        return

    if not pdf_list:
        print("Aucun fichier PDF trouvé à traiter.")
        return

    for pdf_path in tqdm(pdf_list, desc="Traitement des PDF"):
        extraire_notes_vers_csv(pdf_path, args.output_dir)

    print("Traitement terminé.")
    if args.log_file:
        print(f"Logs disponibles dans: {args.log_file}")


if __name__ == '__main__':
    main()
