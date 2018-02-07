#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3

conn = sqlite3.connect('moai.db')

c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS indications
             (
                id INTEGER PRIMARY KEY,
                category TEXT
             )
    """)

c.execute("""
    CREATE TABLE IF NOT EXISTS websites
             (
                id INTEGER PRIMARY KEY,
                indications_id INTEGER,
                website TEXT
             )
    """)

c.execute("""
    CREATE TABLE IF NOT EXISTS websites_dates
             (
                websites_id INTEGER,
                asn TEXT,
                code TEXT,
                google_psi_desktop TEXT,
                google_psi_mobile TEXT,
                google_psi_mobile_usability TEXT,
                https TEXT,
                moz_links TEXT,
                moz_rank TEXT,
                server TEXT
             )
    """)

c.execute("""
    CREATE TABLE IF NOT EXISTS websites_drug
             (
                websites_id INTEGER,
                approval TEXT,
                company TEXT,
                generic TEXT
             )
    """)

c.execute("""
    CREATE TABLE IF NOT EXISTS websites_regex
             (
                websites_id INTEGER,
                regex TEXT
             )
    """)

conn.commit()
conn.close()
