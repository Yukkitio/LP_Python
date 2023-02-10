import json
import sqlite3
import tkinter as tk
import socket
import threading


def text_data_log(self, message):
    """
    Cette fonction permet d'ajouter un message au widget de Data Logs.
    """
    self.data_log.config(state='normal')
    self.data_log.insert(tk.END, message + "\n")
    self.data_log.yview(tk.END)
    self.data_log.config(state='disabled')


def text_server_log(self, message):
    """
    Cette fonction permet d'ajouter un message au widget de Serveur Logs.
    """
    self.server_log.config(state='normal')
    self.server_log.insert(tk.END, message + "\n")
    self.server_log.yview(tk.END)
    self.server_log.config(state='disabled')


def server_database(base_name, table_name, data, client_address, self):
    """
    Cette fonction permet de créer une table dans la BDD, et d'y ajouter les données reçues.
    """
    try:
        # Tentative de connexion à la base de données.
        conn = sqlite3.connect(base_name)
        # Création d'un curseur pour exécuter des requêtes SQL.
        cursor = conn.cursor()
        text_server_log(self, f"--> CONNECTER A LA BDD {base_name}")
        try:
            # Exécution d'une requête SQL pour créer une table avec les champs nécessaires pour stocker les données.
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    IP TEXT,
                    Date DATETIME,
                    Hostname TEXT,
                    OS TEXT,
                    Uptime TEXT,
                    Kernel TEXT,
                    CPU TEXT,
                    Disk TEXT,
                    CPU_Load REAL,
                    Memory TEXT,
                    Network TEXT,
                    Disk_IO TEXT
                )
            ''')
        except sqlite3.Error as e:
            text_data_log(self, f"Error creating the table: {e}")
        try:
            # Exécution d'une requête SQL pour insérer les données dans la table.
            cursor.execute(f'''
                INSERT INTO {table_name} (IP, Date, Hostname, OS, Uptime, Kernel, CPU, Disk, CPU_Load, Memory, Network, Disk_IO)
                VALUES (?, (SELECT datetime()), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_address[0], data['hostname'], data['os'], data['uptime'], data['kernel'],
                str(data['cpu']), str(data['disk']), data['cpu_percent'], str(data['memory']),
                str(data['network']), str(data['disk_io'])
            ))
            text_server_log(self, "--> DATA INSERTED")
        except sqlite3.Error as e:
            text_server_log(self, f"Error executing the query: {e}")
        try:
            conn.commit()
        except sqlite3.Error as e:
            text_server_log(self, f"Error committing the changes: {e}")
        cursor.close()
        conn.close()
    except sqlite3.Error as e:
        text_server_log(self, f"Error connecting to the database: {e}")


def handle_client(client_socket, client_address, self):
    while True:
        try:
            # Réception des données envoyées par le client
            data = client_socket.recv(1024).decode()
            if data:
                # Décodage des données JSON et mise en forme
                data = json.loads(data)
                text_data_log(self, f"Données reçues de {client_address}\n")
                text_data_log(self, json.dumps(data, indent=2))
                text_server_log(self, "----- DEBUT BDD SQLite3 ----")
                # Enregistrement des données dans la BDD
                server_database("server.db", "info_agent", data, client_address, self)
                text_server_log(self, "------ FIN BDD SQLite3 -----")
            else:
                raise Exception("Déconnexion du client")
            text_server_log(self, "Déconnexion du client")
        except Exception as e:
            # Fermeture du socket avec le client
            client_socket.close()
            text_server_log(self, "----------------------------------------")
            break


class ServerUI:
    def __init__(self, root):
        """
        Cette fonction permet de créer UI de notre interface graphique.
        """
        # Définition du titre de la fenêtre
        root.title("Interface Serveur")
        # Largeur et hauteur de la fenêtre
        width = 600
        height = 500
        # Largeur et hauteur de l'écran
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        # Calcul des coordonnées pour centrer la fenêtre
        align_str = '%dx%d+%d+%d' % (width, height, (screen_width - width) / 2, (screen_height - height) / 2)
        # Définition de la géométrie de la fenêtre
        root.geometry(align_str)
        # Désactivation du redimensionnement de la fenêtre
        root.resizable(width=False, height=False)

        # Création d'un socket serveur
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Association du socket à l'adresse IP et au port indiqués
        self.server_socket.bind(("127.0.0.1", 4444))
        # Mise en écoute du socket avec une file d'attente de 5 connexions maximum
        self.server_socket.listen(5)

        # Ajout d'un label "Data Logs" à la fenêtre
        tk.Label(root, text="Data Logs :").place(x=200, y=0, width=94, height=30)
        # Ajout d'une zone de texte pour les logs de données
        self.data_log = tk.Text(root, borderwidth="1px")
        self.data_log.place(x=210, y=30, width=378, height=457)

        # Ajout d'un bouton "Start Serveur" pour démarrer le serveur
        self.start_button = tk.Button(root, text="Start Serveur", command=self.start_server)
        self.start_button.place(x=10, y=110, width=189, height=30)

        # Ajout d'un bouton "Stop Serveur" pour arrêter le serveur
        self.stop_button = tk.Button(root, text="Stop Serveur", command=self.stop_server)
        self.stop_button.place(x=10, y=150, width=189, height=30)

        # Ajout d'un label "Serveur Logs" à la fenêtre
        tk.Label(root, text="Serveur Logs :").place(x=10, y=200, width=114, height=30)
        # Ajout d'une zone de texte pour les logs du serveur
        self.server_log = tk.Text(root, borderwidth="1px")
        self.server_log.config(font=('Helvetica bold', 8))
        self.server_log.place(x=10, y=230, width=190, height=256)

        # Ajout d'un label "IP" à la fenêtre
        tk.Label(root, text="IP :").place(x=10, y=20, width=30, height=30)
        # Ajout d'une zone d'entrée pour l'indication de l'IP
        self.server_ip = tk.Entry(root, borderwidth="1px")
        self.server_ip.place(x=10, y=50, width=122, height=30)
        self.server_ip.insert(0, "127.0.0.1")

        # Ajout d'un label "PORT" à la fenêtre
        tk.Label(root, text="PORT :").place(x=140, y=20, width=37, height=31)
        # Ajout d'une zone d'entrée pour l'indication du PORT
        self.server_port = tk.Entry(root, borderwidth="1px")
        self.server_port.place(x=140, y=50, width=61, height=30)
        self.server_port.insert(0, "4444")

    def start_server(self):
        """
        Cette fonction permet de démarrer le serveur.
        """
        # Récupération de l'IP et du port entré par l'utilisateur
        ip = self.server_ip.get()
        port = int(self.server_port.get())
        # Fermeture du socket précédent
        self.server_socket.close()
        # Création d'un nouveau socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((ip, port))
        # Mise en écoute du socket avec une file d'attente de 5 connexions maximum
        self.server_socket.listen(5)

        try:
            # Mise à jour de l'interface graphique
            self.start_button.config(state="disable")
            self.stop_button.config(state="normal")
            # Ajout d'un message dans la zone "Serveur Logs"
            text_server_log(self, f"Le serveur écoute {ip}:{port}...")
            # Démarrage d'un thread pour exécuter le serveur
            server_thread = threading.Thread(target=self.run_server)
            server_thread.start()

        except Exception as e:
            text_server_log(self, f"Une erreur s'est produite: {e}")
            # Fermeture du socket
            self.server_socket.close()

    def run_server(self):
        """
        Démarre le serveur TCP en écoute permanante et créer un thread pour chaque client connecter.
        """
        try:
            while True:
                # Accepter les connexions de clients
                client_socket, client_address = self.server_socket.accept()
                # Ajout de messages dans la zone "Serveur Logs"
                text_server_log(self, "\n----------------------------------------")
                text_server_log(self, f"Connexion reçue de {client_address[0]}:{client_address[1]}\n")
                # Lancer un nouveau thread pour gérer chaque client séparément
                client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address, self))
                client_handler.start()
        except Exception as e:
            print(f"Une erreur s'est produite: {e}")
            # Fermer le socket du serveur
            self.server_socket.close()

    def stop_server(self):
        """
        Arrête le serveur en fermant les sockets et en activant/désactivant les boutons appropriés
        """
        # Mise à jour de l'interface graphique
        self.start_button.config(state="normal")
        self.stop_button.config(state="disable")
        # fermer la socket
        self.server_socket.close()
        # afficher un message dans le log du serveur
        text_server_log(self, "\nLe serveur a été arrêté.\n")


if __name__ == "__main__":
    # Création de la fenêtre principale de l'application
    root = tk.Tk()
    # Initialisation de l'interface graphique de l'application
    app = ServerUI(root)
    # Lancement de la boucle d'événements de la fenêtre principale (__init__)
    root.mainloop()

