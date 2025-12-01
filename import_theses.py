import sqlite3
import csv


def import_theses_from_csv(csv_file):
    """Import theses from a CSV file"""
    conn = sqlite3.connect('thesis_portal.db')
    cursor = conn.cursor()

    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            cursor.execute('''
                INSERT INTO thesis (title, authors, year, abstract, keywords, adviser, pdf_filename)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['title'],
                row['authors'],
                int(row['year']),
                row['abstract'],
                row.get('keywords', ''),
                row.get('adviser', ''),
                row.get('pdf_filename', '')
            ))

    conn.commit()
    conn.close()
    print(f"Successfully imported {csv_reader.line_num - 1} theses!")


if __name__ == '__main__':
    # Create your CSV file first with these columns:
    # title, authors, year, abstract, keywords, adviser, pdf_filename
    import_theses_from_csv('theses_data.csv')