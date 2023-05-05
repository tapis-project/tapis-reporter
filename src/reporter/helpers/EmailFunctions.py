import datetime as date
import matplotlib.pyplot as plt
import pathlib

from itertools import chain

from apps.jupyterhub.models import FileLog, LoginLog
from apps.main.models import Service


def generate_email_data(service: str, week_begin, week_end) -> dict:
    service_config = Service.objects.get(pk=service)
    proper_name = service_config.proper_name

    match service:
        case 'jupyterub':
            accessed_files = FileLog.objects.filter(service=service, date__range=(week_begin, week_end))
            directories, counts = get_directories_and_counts(service, accessed_files.values('filepath'), service_config)
            plot_path = create_graph(directories, counts)
            stats = generate_stats(service, accessed_files, week_begin, week_end)

def get_directories_and_counts(service, accessed_files, service_config):
    match service:
        case 'jupyterhub':
            filepaths = list(accessed_files)
            dir_counts = {}
            directories = get_service_directories(service_config)

            for path in filepaths:
                dir = path['filepath']
                for d in directories:
                    if d in dir:
                        dir_counts[d] = dir_counts.get(d, 0) + 1

            directories = []
            counts = []
            for dir in dir_counts.keys():
                directories.append(dir)
                counts.append(dir_counts[dir])

            counts, directories = zip(*sorted(zip(counts, directories)))
            
            directories = list(directories)
            counts = list(counts)
            directories.reverse()
            counts.reverse()

            return directories, counts

def get_service_directories(service_config) -> list:
    temp_directories = service_config.servicedirectory_set.all().values('directory')
    service_directories = []
   
    for dir in list(temp_directories):
        service_directories.append(dir['directory'])
    
    return service_directories

def get_service_recipients(service_config) -> list:
    temp_recipients = service_config.servicerecipient_set.all().values('recipient')
    service_recipients = []

    for rec in list(temp_recipients):
        service_recipients.append(rec['recipient'])

    return service_recipients

def create_graph(directories, counts) -> str:
    plt.bar(directories, counts, color='green')
    plt.title('File Access - Notebook Data Depot Locations', fontsize=14)
    plt.xlabel('Directory', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.grid(True)

    filename = str(date.date.today()) + ".png"
    dir = pathlib.Path(__file__).parent.absolute()
    
    folder = r"/results"

    plot_path = str(dir) + folder + filename

    plt.savefig(plot_path)

    return plot_path

def generate_stats(service, accessed_files, week_begin, week_end):
    created_files = accessed_files.filter(action='created')
    opened_files = accessed_files.filter(action='opened')

    num_created_files = created_files.count()
    num_opened_files = opened_files.count()

    login_users = LoginLog.objects.filter(service=service, date__range=(week_begin, week_end))
    unique_login_count = login_users.values('user').distinct().count()
    total_login_count = login_users.count()

    try:
        combined = list(chain(accessed_files, login_users))
        users = []
        for log in combined:
            users.append(log.user)
        unique_users = set(users)
        unique_user_count = len(unique_users)
    except Exception as e:
        unique_user_count = 'Error getting unique user count'

    jupyterhub_stats = {
        'num_created_files': num_created_files,
        'num_opened_files': num_opened_files,
        'unique_login_count': unique_login_count,
        'total_login_count': total_login_count,
        'unique_user_count': unique_user_count
    }
    return jupyterhub_stats