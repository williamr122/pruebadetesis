import sqlite3
import json

def run_migration():
    conn = sqlite3.connect("yelia.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("Starting database migration...")

    # 1. Update metrics_events: copy conversation_id to conv_id if conv_id is NULL
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics_events';")
    if cur.fetchone():
        cur.execute("UPDATE metrics_events SET conv_id = conversation_id WHERE conv_id IS NULL AND conversation_id IS NOT NULL;")
        print(f"Updated conv_id in metrics_events: {cur.rowcount} rows affected.")

    # 2. Update progreso using student_profiles
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles';")
    has_profiles = cur.fetchone()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='progreso';")
    has_progreso = cur.fetchone()

    if has_profiles and has_progreso:
        cur.execute("SELECT student_id, profile_json FROM student_profiles;")
        profiles = cur.fetchall()
        
        updated_progreso_count = 0
        for p in profiles:
            student_id = p["student_id"]
            try:
                prof = json.loads(p["profile_json"])
            except Exception:
                continue
            
            ciclo = prof.get("ciclo") or prof.get("course")
            estado = prof.get("estado")
            if not estado and prof.get("tags"):
                t = prof.get("tags")
                if isinstance(t, list):
                    estado = ", ".join(t) if t else None
                else:
                    estado = str(t)
            nivel = prof.get("level_current")
            
            # Check if this student exists in progreso
            cur.execute("SELECT id FROM progreso WHERE usuario = ?;", (student_id,))
            row = cur.fetchone()
            
            if row:
                cur.execute(
                    """
                    UPDATE progreso 
                    SET ciclo_academico = COALESCE(?, ciclo_academico),
                        estado_materia = COALESCE(?, estado_materia),
                        nivel_materia = COALESCE(nivel_materia, ?)
                    WHERE usuario = ?;
                    """,
                    (ciclo, estado, nivel, student_id)
                )
                updated_progreso_count += cur.rowcount
            else:
                # If they have a profile but no progreso row, create a default progreso row
                cur.execute(
                    """
                    INSERT INTO progreso (usuario, puntos, temas_aprendidos, ciclo_academico, estado_materia, nivel_materia)
                    VALUES (?, 0, '[]', ?, ?, ?);
                    """,
                    (student_id, ciclo, estado, nivel)
                )
                updated_progreso_count += 1
                
        print(f"Updated/Synchronized progreso rows: {updated_progreso_count}.")

    conn.commit()
    conn.close()
    print("Migration finished successfully.")

if __name__ == "__main__":
    run_migration()
