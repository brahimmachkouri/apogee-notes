# apogee-notes
Extraction des notes d'un PDF d'Apogee

```bash
./split-pdf.py -h
usage: split-pdf.py [-h] pdf_path

Extrait chaque page d'un PDF et les enregistre individuellement avec zéro-padding.

positional arguments:
  pdf_path    Chemin vers le fichier PDF à splitter.

options:
  -h, --help  show this help message and exit
```

```bash
/notes2csv.py -h
usage: notes2csv.py [-h] [-o OUTPUT_DIR] [-l LOG_FILE] pdf_file

Extrait les notes d'un PDF issu d'Apogée et génère un CSV.

positional arguments:
  pdf_file              Fichier PDF ou répertoire à traiter

options:
  -h, --help            show this help message and exit
  -o, --output-dir OUTPUT_DIR
                        Répertoire de sortie des CSV
  -l, --log-file LOG_FILE
                        Chemin vers le fichier de log
```
