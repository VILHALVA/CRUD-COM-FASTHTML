from fasthtml.common import *
from datetime import datetime
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_db():
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='users' OR name='entries')")
        existing_tables = cursor.fetchall()

        if len(existing_tables) < 2:  
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    occupation TEXT,
                    week_details TEXT,
                    hobbies TEXT,
                    hometown TEXT,
                    weekend_plans TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            conn.commit()
            logging.info("Configuração do banco de dados bem-sucedida - tabelas criadas!")
        else:
            logging.info("O banco de dados já existe - nenhuma configuração necessária!")

    except sqlite3.Error as e:
        logging.error(f"Falha na configuração do banco de dados: {e}")
    finally:
        conn.close()

setup_db()

def create_user(username):
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        user_id = cursor.lastrowid
        logging.info(f"Usuário criado com sucesso: {username}")
        return user_id
    except sqlite3.IntegrityError:
        logging.warning(f"Usuário já existe: {username}")
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        return cursor.fetchone()[0]
    except sqlite3.Error as e:
        logging.error(f"Erro ao criar usuário: {e}")
        return None
    finally:
        conn.close()

def get_user_id(username):
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Erro ao obter ID do usuário: {e}")
        return None
    finally:
        conn.close()

def create_entry(user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans):
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO entries (user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans))
        conn.commit()
        entry_id = cursor.lastrowid
        logging.info(f"Entrada criada com sucesso para o usuário: {user_id}")
        return entry_id
    except sqlite3.Error as e:
        logging.error(f"Erro ao criar entrada: {e}")
        return None
    finally:
        conn.close()

def get_entries(user_id):
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, content, occupation, week_details, hobbies, hometown, weekend_plans, timestamp
            FROM entries WHERE user_id = ? ORDER BY timestamp DESC
        """, (user_id,))
        entries = cursor.fetchall()
        logging.info(f"Recuperado {len(entries)} entradas para usuário {user_id}")
        return entries
    except sqlite3.Error as e:
        logging.error(f"Erro ao recuperar entradas: {e}")
        return []
    finally:
        conn.close()

def get_entry(entry_id):
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans, timestamp
            FROM entries WHERE id = ?
        """, (entry_id,))
        entry = cursor.fetchone()
        if entry:
            logging.info(f"Entrada recuperada: {entry_id}")
            return entry
        else:
            logging.warning(f"Nenhuma entrada encontrada com id: {entry_id}")
            return None
    except sqlite3.Error as e:
        logging.error(f"Erro ao recuperar entrada: {e}")
        return None
    finally:
        conn.close()

def get_all_entries():
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.title, u.username
            FROM entries e
            JOIN users u ON e.user_id = u.id
            ORDER BY e.timestamp DESC
        """)
        entries = cursor.fetchall()
        logging.info(f"Recuperado {len(entries)} entradas totais")
        return entries
    except sqlite3.Error as e:
        logging.error(f"Erro ao recuperar todas as entradas: {e}")
        return []
    finally:
        conn.close()

def update_entry(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans):
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE entries 
            SET title = ?, content = ?, occupation = ?, week_details = ?, hobbies = ?, hometown = ?, weekend_plans = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, content, occupation, week_details, hobbies, hometown, weekend_plans, entry_id))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Entrada {entry_id} atualizado com sucesso")
            return True
        else:
            logging.warning(f"Nenhuma entrada encontrada com id: {entry_id}")
            return False
    except sqlite3.Error as e:
        logging.error(f"Erro ao atualizar a entrada: {e}")
        return False
    finally:
        conn.close()

app, rt = fast_app()

@rt('/')
def get():
    return Titled("PÁGINA INICIAL",
        Form(
            Input(id='username', placeholder='DIGITE SEU USUÁRIO!'),
            Button("ENTRAR", hx_post='/journal', hx_target='#content'),
            id='login-form',
        ),
        A("ENTRADAS", href='/all_entries', style='display: inline-block; padding: 10px 20px; margin-top: 10px; margin-bottom: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'),
        Div(id='content')
    )

@rt('/journal')
def post(username: str):
    user_id = create_user(username)
    if user_id:
        return journal_page(user_id, username)
    else:
        return "Erro ao criar usuário. Tente novamente!"

def journal_page(user_id, username):
    current_date = datetime.now().strftime("%Y%m%d")
    title = f"ENTROU EM {current_date}"

    return Div(
        H2(f"SEJA BEM-VINDO, {username.upper()}!"),

        Form(
            Div("TÍTULO:", Input(id='entry-title', name='title', value=title)),
            Div("HISTÓRIA:", Textarea(id='entry-content', name='content', placeholder='Escreva sua história aqui...')),
            Div("OCUPAÇÃO:", Input(id='occupation', name='occupation', placeholder='Sua ocupação')),
            Div("DETALHES DA SEMANA:", Textarea(id='week-details', name='week_details', placeholder='Detalhes sobre sua semana')),
            Div("HÁBITOS:", Textarea(id='hobbies', name='hobbies', placeholder='Seus hobbies')),
            Div("CIDADE NATAL:", Input(id='hometown', name='hometown', placeholder='Sua cidade natal')),
            Div("PLANOS DE FIM DE SEMANA:", Textarea(id='weekend-plans', name='weekend_plans', placeholder='Seus planos para o próximo fim de semana')),
            Button("SALVAR", hx_post=f'/submit/{user_id}', hx_target='#entries'),
            id='entry-form'
        ),

        A(
            "INICIO",
            href='/view_entries/',
            style='display: inline-block; padding: 10px 20px; margin-top: 10px; background-color: #007bff; margin-bottom: 10px; color: white; text-align: center; text-decoration: none; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'
        ),

        Div(id='entries')
    )
    
@rt('/submit/{user_id}')
def post(user_id: int, title: str, content: str, occupation: str, week_details: str, hobbies: str, hometown: str, weekend_plans: str):
    entry_id = create_entry(user_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans)
    if entry_id:
        return entry_div(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans, datetime.now())
    else:
        return "Erro ao enviar a entrada. Tente novamente!"

@rt('/view_entries/{user_id}')
def get(user_id: int):
    entries = list_entries(user_id)
    return Titled("VER ENTRADAS:",
        A("HOME", href='/', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'),
        Div(*entries)
    )

@rt('/all_entries')
def get():
    entries = get_all_entries()

    entry_links = [
        Div(
            A(
                f"{entry[1]} COM USUÁRIO: {entry[2]}", 
                href=f'/view_entry/{entry[0]}',
                style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: red; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'
            )
        ) for entry in entries
    ]
    
    return Titled("TODAS AS ENTRADAS:",
        A(
            "HOME", 
            href='/', 
            style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'
        ),
        Div(*entry_links)  
    )

@rt('/view_entry/{entry_id}')
def get(entry_id: int):
    entry = get_entry(entry_id)
    if entry:
        fields = [
            ("TÍTULO", entry[2]),
            ("HISTÓRIA", entry[3]),
            ("OCUPAÇÃO", entry[4]),
            ("PLANOS DE FIM DE SEMANA", entry[5]),
            ("HÁBITOS", entry[6]),
            ("CIDADE NATAL", entry[7]),
            ("PLANOS DE FIM DE SEMANA", entry[8]),
            ("ÚLTIMA ATUALIZAÇÃO", entry[9])
        ]
        entry_details = [Div(
            Div(field[0], style="font-weight: bold; display: inline-block; width: 150px;"),
            " -> ",
            field[1],
            style="margin-bottom: 10px;"
        ) for field in fields]
        return Titled(f"VER ENTRADA {entry_id}",
            A("INÍCIO", href='/', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'),
            Div(*entry_details),
            A("EDITAR", href=f'/edit/{entry_id}', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'),
            A("APAGAR", href=f'/del/{entry_id}', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;')
        )
    else:
        return Titled("ENTRADA NÃO ENCONTRADA",
            A("INÍCIO", href='/'),
            P(f"Entrada {entry_id} não encontrada.")
        )

def list_entries(user_id):
    entries = get_entries(user_id)
    return [entry_div(entry[0], entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], entry[7], entry[8]) for entry in entries]

def entry_div(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans, timestamp):
    return Div(
        H3(title),
        P(f"ESTÓRIA: {content}"),
        P(f"OCUPAÇÃO: {occupation}"),
        P(f"DETALHES DA SEMANA: {week_details}"),
        P(f"HÁBITOS: {hobbies}"),
        P(f"CIDADE NATAL: {hometown}"),
        P(f"PLANOS DE FIM DE SEMANA: {weekend_plans}"),
        P(f"POSTADO EM: {timestamp}"),
        Div(
            A("EDITAR", href=f'/edit/{entry_id}', 
              style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'),
            A("APAGAR", href=f'/del/{entry_id}', 
              style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #dc3545; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'),
            style="display: flex; justify-content: start; gap: 10px; margin-top: 10px;"
        ),
        id=f'entry-{entry_id}'
    )

@rt('/update/{entry_id}')
def post(entry_id: int, title: str, content: str, occupation: str, week_details: str, hobbies: str, hometown: str, weekend_plans: str):
    if update_entry(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return Div(
            P(f"ALTERAÇÕES SALVAS COM SUCESSO EM {current_time}"),
            Script("setTimeout(function() { window.location.href = '/view_entry/" + str(entry_id) + "'; }, 2000);")
        )
    else:
        return "ERRO AO ATUALIZAR A PUBLICAÇÃO. TENTE NOVAMENTE."

@rt('/edit/{entry_id}')
def get(entry_id: int):
    entry = get_entry(entry_id)
    if entry:
        return Titled(f"EDITAR PUBLICAÇÃO {entry_id}",
            Form(
                Div("TÍTULO:", Input(id=f'edit-title-{entry_id}', name='title', value=entry[2])),
                Div("HISTÓRIA:", Textarea(id=f'edit-content-{entry_id}', name='content', placeholder='Escreva sua história aqui...')(entry[3])),
                Div("OCUPAÇÃO:", Input(id=f'edit-occupation-{entry_id}', name='occupation', placeholder='Sua ocupação', value=entry[4])),
                Div("DETALHES DA SEMANA:", Textarea(id=f'edit-week-details-{entry_id}', name='week_details', placeholder='Detalhes sobre sua semana')(entry[5])),
                Div("HÁBITOS:", Textarea(id=f'edit-hobbies-{entry_id}', name='hobbies', placeholder='Seus hobbies')(entry[6])),
                Div("CIDADE NATAL:", Input(id=f'edit-hometown-{entry_id}', name='hometown', placeholder='Sua cidade natal', value=entry[7])),
                Div("PLANOS DE FIM DE SEMANA:", Textarea(id=f'edit-weekend-plans-{entry_id}', name='weekend_plans', placeholder='Seus planos para o próximo fim de semana')(entry[8])),
                Button("SALVAR", hx_post=f'/update/{entry_id}', hx_target='#notification'),
                id=f'edit-form-{entry_id}'
            ),
            Div(id='notification')
        )
    else:
        return Titled("PUBLICAÇÃO NÃO ENCONTRADA",
            A("Início", href='/'),
            P(f"Publicação {entry_id} não encontrada.")
        )

@rt('/del/{entry_id}')
def delete_entry(entry_id: int):
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()

        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()

        if cursor.rowcount > 0:
            logging.info(f"Entrada {entry_id} excluído com sucesso!")
            return Titled(
                "ENTRADA APAGADA",
                P(f"A entrada com ID {entry_id} foi apagada com sucesso."),
                A("HOME", href='/', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'),
                A("ENTRADAS", href='/all_entries', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;')
            )
        else:
            logging.warning(f"Nenhuma entrada encontrada com ID: {entry_id}")
            return Titled(
                "ERRO AO APAGAR",
                P(f"Nenhuma entrada foi encontrada com ID {entry_id}."),
                A("HOME", href='/', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'),
                A("ENTRADAS", href='/all_entries', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;')
            )
    except sqlite3.Error as e:
        logging.error(f"Erro de banco de dados ao excluir entrada: {entry_id}: {e}")
        return Titled(
            "ERRO INTERNO",
            P("Houve um erro ao tentar apagar a entrada. Por favor, tente novamente mais tarde."),
            A("HOME", href='/', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;'),
            A("ENTRADAS", href='/all_entries', style='display: inline-block; padding: 10px 20px; margin: 10px; background-color: #007bff; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s ease;')
        )
    finally:
        conn.close()

def update_entry(entry_id, title, content, occupation, week_details, hobbies, hometown, weekend_plans):
    try:
        conn = sqlite3.connect('DATABASE.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE entries 
            SET title = ?, content = ?, occupation = ?, week_details = ?, hobbies = ?, hometown = ?, weekend_plans = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, content, occupation, week_details, hobbies, hometown, weekend_plans, entry_id))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Publicação {entry_id} atualizada com sucesso")
            return True
        else:
            logging.warning(f"Nenhuma publicação encontrada com o id {entry_id}")
            return False
    except sqlite3.Error as e:
        logging.error(f"Erro ao atualizar a publicação: {e}")
        return False
    finally:
        conn.close()

serve()