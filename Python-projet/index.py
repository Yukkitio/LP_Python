import base64
import io
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from matplotlib import pyplot as plt


def cpu_usage_func(cpu_usage):
    """
    Cette fonction permet de créer le graphique gérant l'utilisation (en pourcentage) du CPU du client.
    Returns : Le graphique encodé en B64
    """
    # Créer un nouveau plot
    fig, ax = plt.subplots()
    # Définir les noms et les valeurs du graphique
    names = ["Utilisé :\n"+str(cpu_usage['percent']) + " %",
             "Disponible :\n"+str(100 - cpu_usage['percent']) + " %"]
    size = [cpu_usage['percent'], 100 - cpu_usage['percent']]
    # Ajouter un cercle blanc au fond du graphique
    my_circle = plt.Circle((0, 0), 0.7, color='white')
    plt.pie(size, labels=names, colors=['#C4EBC8', '#202A25'], wedgeprops={'linewidth': 7, 'edgecolor': 'white'})
    ax.add_artist(my_circle)
    plt.title(str(cpu_usage['type']))

    # Sauvegarder le graphique dans un buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    image_png = buffer.getvalue()
    # Ferme le tampon qui a été utilisé pour sauvegarder l'image du graphique en mémoire.
    buffer.close()
    # Ferme le graphique actuelle de Matplotlib. (évite les surcharge memoire)
    plt.close()
    # Encoder l'image en base64
    graphic = base64.b64encode(image_png).decode("ascii")
    return graphic


def memory_usage_func(memory_usage):
    """
    Cette fonction permet de créer le graphique gérant l'utilisation de l'espace memoire du client.
    Returns : Le graphique encodé en B64
    """
    # Créer un nouveau plot
    fig, ax = plt.subplots()
    # Définir les noms et les valeurs du graphique
    names = ["Libre :\n"+str(memory_usage['available']) + " Gb",
             "utilisé :\n"+str(memory_usage['used']) + " Gb"]
    size = [memory_usage['available'], memory_usage['used']]
    # Ajouter un cercle blanc au fond du graphique
    my_circle = plt.Circle((0, 0), 0.7, color='white')
    plt.pie(size, labels=names, colors=['#5998C5', '#E03616'], wedgeprops={'linewidth': 7, 'edgecolor': 'white'})
    ax.add_artist(my_circle)
    plt.title("Mémoire Totale : " + str(memory_usage['total']) + " Gb")

    # Sauvegarder le graphique dans un buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    image_png = buffer.getvalue()
    # Ferme le tampon qui a été utilisé pour sauvegarder l'image du graphique en mémoire.
    buffer.close()
    # Ferme le graphique actuelle de Matplotlib. (évite les surcharge memoire)
    plt.close()
    # Encoder l'image en base64
    graphic = base64.b64encode(image_png).decode("ascii")
    return graphic


def network_usage_func(network_usage):
    """
    Cette fonction permet de créer le graphique gérant le débit du réseau sur lequel se trouve le client.
    Returns : Le graphique encodé en B64
    """
    # Créer un nouveau plot
    fig, ax = plt.subplots()
    # Définir les noms et les valeurs du graphique
    names = ["Envoie\n"+str(round(network_usage['bytes_sent'] / (1024*1024), 2)),
             "Reception\n"+str(round(network_usage['bytes_recv'] / (1024*1024), 2))]
    size = [network_usage['bytes_sent'] / (1024*1024), network_usage['bytes_recv'] / (1024*1024)]
    plt.barh(names, size, color=['#984447', '#468C98'])
    plt.title("Utilisation du Réseau (Mb/s)")

    # Sauvegarder le graphique dans un buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    image_png = buffer.getvalue()
    # Ferme le tampon qui a été utilisé pour sauvegarder l'image du graphique en mémoire.
    buffer.close()
    # Ferme le graphique actuelle de Matplotlib. (évite les surcharge memoire)
    plt.close()
    # Encoder l'image en base64
    graphic = base64.b64encode(image_png).decode("ascii")
    return graphic


def disk_io_func(disk_io):
    """
    Cette fonction permet de créer le graphique gérant la lecture et l'écriture sur le disque du client.
    Returns : Le graphique encodé en B64
    """
    # Créer un nouveau plot
    fig, ax = plt.subplots()
    # Définir les noms et les valeurs du graphique
    names = ["Lecture :\n" + str(disk_io['read_count']) + "/s", "Ecriture :\n" + str(disk_io['write_count']) + "/s"]
    size = [disk_io['read_count'], disk_io['write_count']]
    plt.bar(names, size, color=['#05204A', '#B497D6'])
    plt.title("Nombre d'opérations du disque")

    # Sauvegarder le graphique dans un buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    image_png = buffer.getvalue()
    # Ferme le tampon qui a été utilisé pour sauvegarder l'image du graphique en mémoire.
    buffer.close()
    # Ferme le graphique actuelle de Matplotlib. (évite les surcharge memoire)
    plt.close()
    # Encoder l'image en base64
    graphic = base64.b64encode(image_png).decode("ascii")
    return graphic


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Tentative de connexion à la base de données.
            conn = sqlite3.connect('server.db')
            cursor = conn.cursor()
            # Exécution d'une requête SQL pour récupérer toutes les données nécessaires.
            cursor.execute('SELECT * from info_agent ORDER BY id DESC LIMIT 1')
            data = cursor.fetchone()
            if data is None:
                raise Exception("Aucune donnée trouvée dans la base de données")

            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                # Variable Python à injecter dans le fichier HTML
                d_os = data[4]
                d_uptime = data[5]
                d_host = data[3]
                d_kernel = data[4]

                # Création des différents graphiques (CPU et MEMOIRE)
                g_cpu_usage = cpu_usage_func(eval(data[7]))
                g_memory_usage = memory_usage_func(eval(data[10]))

                # Création d'une table HTML en y insérant les données relatives aux différents disques du client.
                d_tab_disk = '<table>'
                d_tab_disk += '<tr><th>Lecteur</th><th>Total</th><th>Utilisé</th><th>Libre</th><th>Pourcentage Utilisé</th></tr>'
                disk_usage = eval(data[8])
                for drive, usage in disk_usage.items():
                    d_tab_disk += '<tr><td>{}</td><td>{} Gb</td><td>{} Gb</td><td>{} Gb</td><td>{} %</td></tr>'.format(drive, usage['total'], usage['used'], usage['free'], usage['percent_used'])
                d_tab_disk += '</table>'

                # Création des différents graphiques (CHARGE, RESEAUX et DISQUE-IO)
                g_load_average = 'ICI GRAPH'
                g_network_use = network_usage_func(eval(data[11]))
                g_disk_io = disk_io_func(eval(data[12]))

                # Lire le fichier HTML en utilisant with pour gérer automatiquement la fermeture du fichier
                with open('index.html', 'r') as file:
                    content = file.read()

                # Remplacement des marqueurs de variable avec les valeurs de variable Python
                content = content.replace('{{ os }}', d_os)
                content = content.replace('{{ uptime }}', d_uptime)
                content = content.replace('{{ hostname }}', d_host)
                content = content.replace('{{ kernel }}', d_kernel)
                content = content.replace('{{ graph_cpu_usage }}', g_cpu_usage)
                content = content.replace('{{ graph_memory_usage }}', g_memory_usage)
                content = content.replace('{{ tab_disk_usage }}', d_tab_disk)
                content = content.replace('{{ graph_load_average }}', g_load_average)
                content = content.replace('{{ graph_network_use }}', g_network_use)
                content = content.replace('{{ graph_disk_io }}', g_disk_io)
                self.wfile.write(content.encode())

        except Exception as e:
            # Si aucune réponse alors on affiche une page d'erreur
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(
                bytes("<html><body><h1>Erreur serveur</h1><p>{}</p></body></html>".format(str(e)), 'utf-8'))
        finally:
            # Fermeture de la connection avec la BDD
            cursor.close()
            conn.close()


# Démarrez le serveur HTTP et le laisser fonctionner jusqu'à ce qu'il soit arrêté manuellement
httpd = HTTPServer(('localhost', 8080), RequestHandler)
httpd.serve_forever()
