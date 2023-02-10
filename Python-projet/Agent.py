import platform
import socket
import time
import datetime
import psutil
import json
import os


# Liste les services en cours d'exécution sur la machine
def list_running_services():
    """
     Cette fonction liste les services par status et les ajoute à un tableau.
     """
    cmd = os.popen(
        '''for /f "tokens=2" %s in ('sc query state^= all ^| find "SERVICE_NAME"') do @(for /f "tokens=4" %t in ('sc query %s ^| find "STATE     "') do @echo %s is %t)''')
    running_services = []
    for line in cmd:
        running = line.split()
        if running[-1] == 'RUNNING':
            running_services.append(running[0])
    return running_services


# Vérifie si les services listés dans le fichier de configuration sont en cours d'exécution
def check_configured_services(configured_services):
    """
    Cette fonction permet de vérifier si un service est 'RUNNING' ou non suivant le fichier de config.
    """
    try:
        # Ouvre le fichier de configuration des services
        with open(configured_services, 'r') as services_file:
            # Lit le fichier ligne par ligne
            services = services_file.readlines()
            # Enlève les sauts de ligne
            services = [service.strip() for service in services]
            # Liste les services en cours d'exécution
            running_services = list_running_services()
            # Vérifie si les services listés dans le fichier de configuration sont en cours d'exécution
            for service in services:
                if service in running_services:
                    print(f'Le service "{service}" est en cours d\'exécution.')
                else:
                    print('--')
                    print(f'Le service "{service}" n\'est pas en cours d\'exécution.')
                    print('--')
    except FileNotFoundError:
        print(f'Le fichier "{configured_services}" n\'a pas été trouvé.')
    except Exception as e:
        print(f'Une erreur est survenue : {e}')


def get_hardware_info():
    """
    Cette fonction retourne les informations matérielles de l'ordinateur.
    Returns :
        dict : Un dictionnaire contenant les informations matérielles.
    """
    system_info = {}
    # Récupération du nom d'hôte
    system_info['hostname'] = socket.gethostname()
    # Récupération de la plateforme OS
    system_info['os'] = platform.platform()
    # Récupération de uptime en secondes
    boot_time = int(time.time()) - psutil.boot_time()
    # Conversion en objet datetime
    dt = datetime.datetime.fromtimestamp(boot_time)
    # Formatage en chaîne de caractères
    formatted_time = dt.strftime('%H:%M:%S')
    system_info['uptime'] = formatted_time

    # Récupération des informations CPU
    system_info['cpu'] = {
        "type": platform.processor(),
        "count": psutil.cpu_count(),
        "frequency": psutil.cpu_freq().current / 1000,
        "percent": psutil.cpu_percent(interval=None)
    }

    # Récupération de la version du noyau
    system_info['kernel'] = platform.uname().release

    disk_info = {}
    # Récupération des informations sur les partitions disques
    partitions = psutil.disk_partitions()
    for partition in partitions:
        usage = psutil.disk_usage(partition.mountpoint)
        disk_info[partition.mountpoint] = {
            "total": round(usage.total / (1024.0 ** 3), 2),
            "used": round(usage.used / (1024.0 ** 3), 2),
            "free": round(usage.free / (1024.0 ** 3), 2),
            "percent_used": usage.percent
        }
    system_info['disk'] = disk_info

    # Récupération de l'utilisation CPU
    system_info['cpu_percent'] = psutil.cpu_percent()

    # Récupération de la mémoire vive
    memory = psutil.virtual_memory()
    memory_info = {}
    memory_info['total'] = round(memory.total / (1024.0 ** 3), 2)
    memory_info['available'] = round(memory.available / (1024.0 ** 3), 2)
    memory_info['used'] = round(memory.used / (1024.0 ** 3), 2)
    system_info['memory'] = memory_info

    # Récupération des statistiques réseau
    network_io_counters = psutil.net_io_counters()
    system_info['network'] = {
        "bytes_sent": network_io_counters.bytes_sent,
        "bytes_recv": network_io_counters.bytes_recv
    }

    # Récupération des statistiques disque
    disk_io_counters = psutil.disk_io_counters()
    system_info['disk_io'] = {
        "read_count": disk_io_counters.read_count,
        "write_count": disk_io_counters.write_count
    }
    return system_info


try:
    try:
        print('Vérification de vos services avant toutes connection au serveur...')
        # Appelle la fonction check_configured_services avec le nom du fichier de configuration
        check_configured_services('services.conf')
        print('--> services OK')
    except:
        print('Impossible de vérifier l\'intégralité de vos services !')
    # Création d'un socket client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Connexion au serveur à l'adresse IP "127.0.0.1" sur le port 4444
    client_socket.connect(("127.0.0.1", 4444))
    # Obtention des informations système
    hardware_info = get_hardware_info()
    # Conversion des informations système en chaîne JSON
    hardware_info_json = json.dumps(hardware_info)
    # Envoi des informations système au serveur
    client_socket.send(hardware_info_json.encode())
    print('Données envoyé au serveur...')
    # Fermeture de la connexion d'écriture
    client_socket.shutdown(socket.SHUT_WR)
    # Fermeture du socket client
    client_socket.close()
    print('Fermeture de la connexion.')

except ConnectionRefusedError:
    print("Le serveur n'a pas répondu. Vérifiez que le serveur est en cours d'exécution et que l'adresse IP et le port sont corrects.")
except socket.gaierror:
    print("Impossible de résoudre l'adresse IP. Vérifiez que l'adresse IP est correcte.")
except Exception as e:
    print(f"Une erreur s'est produite: {e}")
