# apogee-notes
Extraction des notes d'un relevé PDF d'Apogee

```bash
python3 split-pdf.py -h
usage: split-pdf.py [-h] [-o OUTPUT_DIR] [-l LOG_FILE] pdf_path

Split PDF en fichiers par étudiant sur INE, en ignorant la page de garde.

positional arguments:
  pdf_path              PDF contenant tous les relevés

options:
  -h, --help            show this help message and exit
  -o, --output-dir OUTPUT_DIR
                        Répertoire de sortie
  -l, --log-file LOG_FILE
                        Fichier de log
```

```bash
python3 notes2csv.py -h
usage: notes2csv.py [-h] [-o OUTPUT_DIR] [-l LOG_FILE] pdf_file

Extrait les notes d'un PDF Apogée et génère un CSV multi-pages.

positional arguments:
  pdf_file              Fichier PDF ou répertoire à traiter

options:
  -h, --help            show this help message and exit
  -o, --output-dir OUTPUT_DIR
                        Répertoire de sortie des CSV
  -l, --log-file LOG_FILE
                        Chemin vers le fichier de log
```

Exemple d'utilisation : 
```bash
python3 split-pdf.py releves.pdf
```
va scinder le pdf en autant de fichiers qu’il contient de pages dans le répertoire "releves_per_student".

```bash
python3 notes2csv.py ./releves_per_student
```
va extraire toutes les datas des fichiers PDF du dossier et les enregistrer dans des fichiers CSV.
