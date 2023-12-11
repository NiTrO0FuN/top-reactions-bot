import sqlite3

def add_guild(guild_id: int, podium_size):
    con = sqlite3.connect("./storage.db")
    cur = con.cursor()

    cur.executemany("INSERT INTO top_reactions VALUES (?,?,?,?,?)",
                    [(None,None,guild_id,i,None) for i in range(podium_size)])
    
    cur.execute("INSERT INTO podium_location VALUES (?,?,?)", (None, None, guild_id))
    
    con.commit()
    con.close()

def remove_guild(guild_id: int):
    con = sqlite3.connect("./storage.db")
    cur = con.cursor()

    cur.execute("DELETE FROM top_reactions WHERE guild=:guild",
                {"guild": guild_id})
    
    cur.execute("DELETE FROM podium_location WHERE guild=:guild",
                {"guild": guild_id})
    
    con.commit()
    con.close()

def set_guild_podium_location(guild_id: int, channel_id: int, message_id: int):
    con = sqlite3.connect("./storage.db")
    cur = con.cursor()

    cur.execute("UPDATE podium_location SET channel=:channel, message=:message WHERE guild=:guild",
                {"guild": guild_id, "channel": channel_id, "message": message_id})

    con.commit()
    con.close()

def get_guild_podium(guild_id:int) -> list[tuple[int,int,int]|tuple[None,None,None]]:
    con = sqlite3.connect("./storage.db")
    cur = con.cursor()

    podium = cur.execute("SELECT message, channel, reactions FROM top_reactions WHERE guild=:guild ORDER BY rank" ,
                      {"guild":guild_id}).fetchall()

    con.close()

    return podium

def get_guild_podium_location(guild_id: int) -> tuple[int, int]|tuple[None, None]:
    con = sqlite3.connect("./storage.db")
    cur = con.cursor()

    podium_location = cur.execute("SELECT message, channel FROM podium_location WHERE guild=?", (guild_id,)).fetchone()

    con.close()
    return podium_location

def save_guild_podium(guild_id: int, podium: list[dict[str,int | None]]):
    con = sqlite3.connect("./storage.db")
    cur = con.cursor()

    for i in range(len(podium)):
        place = podium[i]
        cur.execute("""UPDATE top_reactions SET message=:message, channel=:channel ,reactions=:reactions
                    WHERE guild=:guild AND rank=:rank""",
                    {"message": place["message_id"], "channel": place["channel_id"], "reactions": place["reaction_nbr"], "guild": guild_id, "rank": i})

    con.commit()
    con.close()

def save_guild_podium_rank(guild_id: int, channel_id: int|None, message_id: int|None, rank: int, reaction_nbr: int|None):
    con = sqlite3.connect("./storage.db")
    cur = con.cursor()

    cur.execute("""UPDATE top_reactions SET message=:message, channel=:channel,reactions=:reactions
                WHERE guild=:guild AND rank=:rank""",
                {"message":  message_id, "channel": channel_id, "reactions": reaction_nbr, "guild": guild_id, "rank": rank})
    
    con.commit()
    con.close()