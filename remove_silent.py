#! /usr/bin/env python3
import hashlib
import os
import sqlite3
import sys

import itertools
from pydub import AudioSegment

file_exts = [".rmvb", ".mp4", ".rm", ".avi"]


# Check table & update
def init_db(db):
    c = db.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS files (
      id INTEGER PRIMARY KEY,
      max_volume INTEGER,
      hash TEXT,
      file_name TEXT,
      path TEXT
    );
    ''')
    c.close()

    db.commit()


def filter_file(name):
    f_l = name.lower()
    return any(f_l.endswith(e) for e in file_exts)


class FileRecord:
    def __init__(self):
        self.id = -1
        self.max_volume = 0
        self.hash = ""
        self.file_name = ""
        self.path = ""


def iter_files(root_path):
    for (p, dirs, files) in os.walk(root_path):
        for f in filter(filter_file, files):
            file_path = os.path.join(p, f)

            m = hashlib.sha256()
            m.update(file_path.encode("utf-8"))
            file_hash = m.hexdigest()

            f_obj = FileRecord()
            f_obj.hash = file_hash
            f_obj.file_name = f
            f_obj.path = file_path

            yield f_obj


def iter_files_grouped(root_path):
    it = iter(iter_files(root_path))

    result = {}
    while True:
        try:
            f = next(it)
            result[f.hash] = f

            if len(result) >= 20:
                yield result
                result = {}

        except StopIteration:
            break

    yield result


# Check file record from database
def read_db(file_records, db):
    c = db.cursor()

    placeholders = ",".join("?" * len(file_records))
    c.execute('''
    SELECT * FROM files
    WHERE hash IN (%s)
    ''' % placeholders, [h for h in file_records])

    for record in c.fetchall():
        _id = record["id"]
        max_volume = record["max_volume"]
        h = record["hash"]
        obj = file_records[h]
        obj.id = _id
        obj.max_volume = max_volume

    c.close()


def save_db(file_records, db):
    c = db.cursor()
    c.executemany('''
    INSERT INTO files (
    max_volume,
    hash,
    file_name,
    path
    )
    VALUES (?,?,?,?)
    ''', ((f.max_volume, f.hash, f.file_name, f.path) for f in file_records))

    c.close()
    db.commit()


def get_volume(file_records):
    for f in file_records:
        try:
            audio = AudioSegment.from_file(f.path)
            f.max_volume = audio.max
        except Exception:
            f.max_volume = -1


if __name__ == '__main__':
    vl = len(sys.argv)

    if vl < 2:
        # Too few arguments
        raise Exception("Too few arguments!")

    demo = False

    for arg in sys.argv[1:-1]:
        if arg == '-d':
            demo = True
        else:
            raise Exception("Unknown argument %s!" % arg)

    path = sys.argv[-1]

    # Open database
    db_file = os.path.join(path, "remove_silent.db")
    db = sqlite3.connect(db_file)
    db.row_factory = sqlite3.Row
    init_db(db)

    for f in iter_files_grouped(path):
        read_db(f, db)

        v = itertools.groupby(f.values(), lambda _f: _f.id != -1)
        file_not_in_db = []
        file_in_db = []
        for key, group in v:
            if key:
                file_in_db = list(group)
            else:
                file_not_in_db = list(group)

        get_volume(file_not_in_db)
        save_db(file_not_in_db, db)

        # Check volume
        for single_file in f.values():
            if single_file.max_volume > 100 or single_file.max_volume == -1:
                continue

            print("File: %s, max_volume=%s." % (single_file.path, single_file.max_volume))
            if not demo:
                os.remove(single_file.path)
                print("> Deleted.")

    db.close()
