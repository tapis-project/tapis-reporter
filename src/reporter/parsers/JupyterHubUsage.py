import re
import gzip
from datetime import datetime
import logging

from ..apps.services.jupyterhub.models import FileLog, LoginLog, ParsedNginxFile
from ..helpers.jupyterhub_usage_funcions import get_home_path, get_symbolic_links

logger = logging.getLogger(__name__)


class JupyterHubUsage:

    def __init__(self):
        self.login_counts = {}
        self.login_dates = {}
        self.login_times = {}
        self.created_files = {}
        self.opened_files = {}
        self.daily_files = {}
        self.tenant = ""
        self.home_path = ""
        self.symbolic_links = {}
        self.file_entries_to_add = []
        self.login_entries_to_add = []

    def is_file_parsed(self, filename):
        logger.error(f'filename: {filename}')
        file_exists = ParsedNginxFile.objects.filter(pk=filename).exists()
        if file_exists:
            fileobj = ParsedNginxFile.objects.filter(pk=filename)[0]
            parsed_status = fileobj.status
            if parsed_status == 'Success':
                logger.error(f"{filename} exists -- skipping")
                return True
        return False

    def add_file_to_db(self, filename):
        '''
        Add NGINX file entry to ParsedNginxFile table
        '''
        file_exists = ParsedNginxFile.objects.filter(pk=filename).exists()
        if not file_exists:
            try:
                ParsedNginxFile.objects.create(
                    filename=filename,
                    status='Queued',  # Initialize parsed status to 'queued'
                    error=''
                )
                return True
            except Exception as e:
                logger.exception(f"Error creating database entry for file: {filename}")
                logger.exception(e)
                return False
        
    def parse_jhub_file(self, file, filename):
        try:
            with gzip.open(file, 'rt') as logfile:
                # Update ParsedNginxFile status to 'opened'
                ParsedNginxFile.objects.filter(pk=filename).update(status='Opened')

                for log in logfile:
                    self.set_tenant(log)
                    self.home_path = get_home_path(self.tenant)
                    self.symbolic_links = get_symbolic_links(self.tenant)

                    log_info = self.get_info_from_log(log)
                    if log_info is not None:
                        request_type = log_info['request_type']
                        path = log_info['raw_path']

                        if '/hub/api/oauth2/authorize' in log:
                            self.add_login_entry(log_info)
                        if log_info['file'] is not None:
                            # Check if user created a notebook
                            if request_type == 'GET' and 'Untitled.ipynb?kernel_name' in path:
                                self.add_created_file(log_info)
                            # Get opened notebooks and where they are
                            elif request_type == 'GET' and '/user' in path and '.ipynb' in log_info['file']:
                                self.add_opened_file(log_info)
                        
            success = True
            if len(self.file_entries_to_add) > 0:
                files_added = self.add_file_entries_to_db()
                success = False if not files_added == 'Added' else success
                error = files_added if not files_added == 'Added' else ''
            if len(self.login_entries_to_add) > 0:
                logins_added = self.add_login_entries_to_db()
                success = False if not logins_added == 'Added' else success
                error = logins_added if not logins_added == 'Added' else ''
            if success:
                logger.info(f"{filename} -- Succeeded")
                ParsedNginxFile.objects.filter(pk=filename).update(status='Succeeded')
                return True
            else:
                logger.info(f"{filename} -- Failed")
                ParsedNginxFile.objects.filter(pk=filename).update(status='Failed', error=error)
                return False
        except Exception as e:
            ParsedNginxFile.objects.filter(pk=filename).update(status='Failed', error=e)
            logger.exception(e)
            return False

    def add_file_entries_to_db(self):
        """
        Add file entries to database

        :return: String -- Added or error
        """
        try:
            FileLog.objects.bulk_create(self.file_entries_to_add)
            return 'Added'
        except Exception as e:
            logger.error(f"Unable to add file entries; error: {e}")
            return e

    def add_login_entries_to_db(self):
        """
        Add login entries to database

        :return: String -- Added or error
        """
        try:
            LoginLog.objects.bulk_create(self.login_entries_to_add)
            return 'Added'
        except Exception as e:
            logger.error(f"Unable to add login entries; error: {e}")
            return e

    def add_log_to_entries(self, info):
        """
        Add model object to entries list

        :param info: dictionary containg info from log
        :return: nothing, but update list of entries
        """
        if not isinstance(info['user'], str):
            logger.error(f"NO USER FOUND: {info} -- SKIPPING")
            return
        user = info['ip_address'] if info['user'] == '' else info['user']
        if info['action'] in ['created', 'opened']:
            self.file_entries_to_add.append(FileLog(
                    tenant=self.tenant,
                    user=user,
                    action=info['action'],
                    filepath=info['path'], 
                    filename=info['file'], 
                    date=info['date'], 
                    time=info['time'],
                    raw_filepath=info['raw_filepath']
                ))
        else:
            self.login_entries_to_add.append(LoginLog(
                    tenant=self.tenant,
                    user=user,
                    date=info['date'], 
                    time=info['time']
                ))

    def set_tenant(self, log):
        """
        Set tenant if tenant not provided

        :param log: current log in file
        :return: nothing, but update tenant
        """
        split_log = re.split(r'\s' ,log)
        if 'jupyter.tacc.cloud' in log or '/home/jovyan/' in split_log[6]:
            self.tenant = 'tacc'
        elif 'jupyter.designsafe-ci.org' in log or '/home/jupyter/' in split_log[6]:
            self.tenant = 'designsafe'

    def get_user(self, path):
        """
        Gets user from HTTP call

        :param split_log: current log split into an array
        :return: username or None if not found
        """
        split_with_user = None
        if 'client_id=' in path:
            split_client = path.split('client_id=')
            split_path = split_client[1].split('&', 1)[0]
            split_with_user = split_path.split('-')
        elif '/user/' in path:
            split_with_user = path.split('/')

        if split_with_user is not None:
            user_index = split_with_user.index('user')
            jhub_user = split_with_user[user_index+1]
            return jhub_user

    def parse_special_characters(self, str):
        """
        Replace percent encoding with represented character

        :param str: str to replace the percent encoded characters
        :return: string without any percent encoded characters
        """
        str = str.replace('%20', ' ')
        str = str.replace('%C3%B3', 'o')
        str = str.replace('%C3%A1', 'a')
        str = str.replace('%3A', ':')
        str = str.replace('%26', '&')
        return str

    def check_for_symbolic_link(self, path):
        """
        Check for symbolic path (ie. DesignSafe: /home/jupyter/projects -> /home/jupyter/MyProjects)

        :param path: path to check
        :return: updated path changed to represent symbolic link if able
        """
        for key in self.symbolic_links:
            if key in path:
                new_path = path.replace(key, self.symbolic_links[key])
                return new_path
        return path

    def get_true_path(self, user, path):
        """
        Get absolute path to file

        :param path: network path to file
        :return: absolute path
        """
        network_paths = [
            f'/user/{user}/notebooks',
            f'/user/{user}/api/contents',
            f'/user/{user}/files',
            f'/user/{user}/lab/tree',
            f'/user/{user}/nbconvert/script',
            f'/user/{user}/edit'
        ]
        for network_path in network_paths:
            if network_path in path:
                if self.home_path != "":
                    true_path = path.replace(network_path, self.home_path)
                    true_path = self.check_for_symbolic_link(true_path)
                    return true_path
        return path

    def get_path(self, split_log):
        """
        Gets path accessed in HTTP call

        :param split_log: current log split into an array
        :return: path accessed
        """
        init_path = split_log[6].rsplit('/',1)
        if '.ipynb' in init_path[0]:
            path = init_path[0].rsplit('/',1)[0]
        else:
            path = init_path[0]
        path = self.parse_special_characters(path)
        return path

    def get_file(self, path):
        """
        Gets file accessed in HTTP call

        :param split_log: current log split into an array
        :return: file accessed
        """
        file = re.search(r'[^/]*.ipynb', path)
        if file:
            file = file.group()
            file = self.parse_special_characters(file)
        return file

    def get_date(self, date):
        """
        Change date to YYYY-MM-DD format

        :param init_date: date from log
        :return: formatted date
        """
        date_obj = datetime.strptime(date, "%d/%b/%Y")
        return date_obj.strftime("%Y-%m-%d")

    def get_info_from_log(self, log):
        """
        Change date to YYYY-MM-DD format

        :param init_date: date from log
        :return: formatted date
        """
        regex = re.compile(r'(?P<jup_client_ip>\S+) - - \[(?P<jup_date>\d{2}\/\w+\/\d{4}):(?P<jup_time>\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] "(?P<jup_method>\S+) (?P<jup_path>\S+) \S+" (?P<jup_status_code>\d+) (?P<jup_bytes_sent>\d+) "(?P<jup_referer>[^"]+)" "(?P<jup_user_agent>[^"]+)" "-"')
        match = regex.match(log)

        if not match:
            return

        log_info = {name: match.group(name) for name in match.groupdict()}
        try:
            user = self.get_user(log_info['jup_path'])
            raw_path = log_info['jup_path']
            network_path = self.get_path(log_info['jup_path'])
            path = self.get_true_path(user, network_path)
            file = self.get_file(log_info['jup_path'])
            date = self.get_date(log_info['jup_date'])
            request_type = log_info['jup_method']

            time = log_info['jup_time'].split(' ')[0]
            ip_address = log_info['jup_client_ip']
            system_info = log_info['jup_user_agent']
        except Exception as e:
            print(f"Error parsing out info: {e}")

        return {'user': user, 'raw_path': raw_path, 'network_path': network_path, 'path': path, 'file': file, 'date': date, 'time': time, 'ip_address': ip_address, 'request_type': request_type, 'system_info': system_info}

    def add_login_entry(self, log_info):
        """
        Count login entry from current log

        :param log_info: current log's info
        :return: nothing
        """
        user = log_info['user']
        date = log_info['date']
        time = log_info['time']

        info = {
            'user': user,
            'date': date,
            'time': time,
            'action': 'login',
            'ip_address': log_info['ip_address'],
            'system_info': log_info['system_info']
        }

        insert = False

        if date in self.login_dates:
            if user not in self.login_dates[date]:
                self.login_dates[date].append(user)
        else:
            self.login_dates[date] = [user]

        if user in self.login_times:
            old_time = datetime.strptime(self.login_times[user], "%H:%M:%S")
            new_time = datetime.strptime(time, "%H:%M:%S")
            time_diff = new_time - old_time
            if time_diff.total_seconds() > 120:
                self.login_times[user] = time
                self.login_counts[user] += 1
                insert = True
        else:
            self.login_times[user] = time
            self.login_counts[user] = 1
            insert = True

        if insert:
            self.add_log_to_entries(info)

    def add_created_file(self, info):
        """
        Add file to created files dict

        :param split_log: current log split into an array
        :return: nothing
        """
        user = info['user']
        path = info['path']
        file = info['file']
        date = info['date']
        info['action'] = 'created'
        new_file = True
        new_date = True

        if user in self.created_files:
            if [path, file] not in self.created_files[user]:
                self.created_files[user].append([path, file])
            else:
                new_file = False
        else:
            self.created_files[user] = [[path, file]]

        if date in self.daily_files:
            if user not in self.daily_files[date]:
                self.daily_files[date][user] = {}
            else:
                new_date = False
            self.daily_files[date][user]['created'] = self.created_files[user]
        else:
            self.daily_files[date] = {}
            self.daily_files[date][user] = {}
            self.daily_files[date][user]['created'] = self.created_files[user]

        if new_file or new_date:
            self.add_log_to_entries(info)
        elif not new_file and new_date:
            self.add_log_to_entries(info)

    def add_opened_file(self, info):
        """
        Add file to opened files dict

        :param split_log: current log split into an array
        :return:  nothing
        """
        user = info['user']
        path = info['path']
        file = info['file']
        date = info['date']
        info['action'] = 'opened'
        new_file = True
        new_date = True

        if user in self.opened_files:
            if [path, file] not in self.opened_files[user]:
                self.opened_files[user].append([path, file])
            else:
                new_file = False
        else:
            self.opened_files[user] = [[path, file]]

        if date in self.daily_files:
            if user not in self.daily_files[date]:
                self.daily_files[date][user] = {}
            else:
                new_date = False
            self.daily_files[date][user]['opened'] = self.opened_files[user]
        else:
            self.daily_files[date] = {}
            self.daily_files[date][user] = {}
            self.daily_files[date][user]['opened'] = self.opened_files[user]

        if new_file or new_date:
            self.add_log_to_entries(info)
        elif not new_file and new_date:
            self.add_log_to_entries(info)
