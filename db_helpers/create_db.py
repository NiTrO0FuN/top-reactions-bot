import sqlite3

con = sqlite3.connect("./storage.db")

cur = con.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS top_reactions(
                    message INTEGER,
                    channel INTEGER,
                    guild INTEGER NOT NULL,
                    rank INTEGER NOT NULL,
                    reactions INTEGER
                )""")

cur.execute("""CREATE TABLE IF NOT EXISTS podium_location(
                    message INTEGER,
                    channel INTEGER,
                    guild INTEGER NOT NULL
                )""")

con.commit()
con.close()