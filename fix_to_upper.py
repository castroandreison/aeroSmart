import sqlite3
c = sqlite3.connect("C:\\Users\\an053116\\Documents\\01 - Códigos python\\38 - AeroClub\\backend\\aeroclub.db")
cur = c.cursor()

# Fix to UPPERCASE (matching SQLAlchemy's enum NAME storage)
cur.execute("UPDATE agendamentos SET status = 'AGENDADO' WHERE LOWER(status) = 'agendado'")
cur.execute("UPDATE agendamentos SET status = 'CONCLUIDO' WHERE LOWER(status) = 'concluido'")
cur.execute("UPDATE agendamentos SET status = 'EM_ANDAMENTO' WHERE LOWER(status) = 'em_andamento'")
cur.execute("UPDATE agendamentos SET status = 'CANCELADO' WHERE LOWER(status) = 'cancelado'")

cur.execute("SELECT id, status FROM agendamentos ORDER BY id")
rows = cur.fetchall()
for r in rows:
    print(f"  ID {r[0]:2d}: {repr(r[1])}")
c.commit()
c.close()
