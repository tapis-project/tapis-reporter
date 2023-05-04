import os
import django
import re
import gzip
from datetime import datetime

import logging

logger = logging.getLogger(__name__)

from .models import FileLog, LoginLog, ParsedAccessLog


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
        self.login_entries_to_add =[]

    def check_for_jhub_file(self, filename):
        logger.error(f'filename: {filename}')
        file_exists = ParsedAccessLog.objects.filter(pk = filename).exists()
        if file_exists:
            fileobj = ParsedAccessLog.objects.filter(pk=filename)[0]
            status = fileobj.status
            if status == 'Success':
                logger.error(f"{filename} exists -- skipping")
                return False
        elif not file_exists:
            try:
                ParsedAccessLog.objects.create(
                    filename = filename,
                    status = 'Queued',
                    error = ''
                )
            except Exception as e:
                logger.exception(f"Error creating entry for file: {filename}")
                logger.exception(e)
                return False
        return True

    def parse_jhub_file(self, file, filename):
        logger.error(f'parse jhub file: {file}')
        try:
            with gzip.open(file, 'rt') as logfile:
                ParsedAccessLog.objects.filter(pk=filename).update(status='Opened')
                for log in logfile:
                    self.set_tenant(log)
                    split_log = re.split(r'\s' ,log)
                    request_type = split_log[5][1:]
                    request_status = split_log[8]
                    # Check if user is authorized by TAPIS auth
                    if '/hub/api/oauth2/authorize' in log:
                        self.parse_login_info(split_log)
                    # Check if user created a notebook
                    elif request_type == 'GET' and 'Untitled.ipynb?kernel_name' in split_log[6]:
                        self.add_created_file(split_log)
                    # Get opened notebooks and where they are
                    elif request_type == 'GET' and '/user/' in split_log[6] and '.ipynb' in split_log[6]:
                        self.add_opened_file(split_log)
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
                logger.info(f"{filename} -- Success")
                ParsedAccessLog.objects.filter(pk=filename).update(status='Success')
                return True
            else:
                logger.info(f"{filename} -- Failed")
                ParsedAccessLog.objects.filter(pk=filename).update(status='Failed', error=error)
                return False
        except Exception as e:
            ParsedAccessLog.objects.filter(pk=filename).update(status='Failed', error=e)
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

    def set_home_path(self):
        """
        Set home path based off of tenant

        :return: home path of tenant
        """
        home_paths = {
            'tacc': '/home/jovyan',
            'designsafe': '/home/jupyter'
        }
        return home_paths.get(self.tenant, "")

    def set_symbolic_links(self):
        """
        Set symbolic link based off of tenant

        :return: symbolic link(s) of tenant
        """
        symbolic_links = {
            'tacc': {
                '/home/jovyan/shared': '/home/jovyan/team_classify/shared'
            },
            'designsafe': {
                '/home/jupyter/community': '/home/jupyter/CommunityData',
                '/home/jupyter/mydata': '/home/jupyter/MyData',
                '/home/jupyter/projects': '/home/jupyter/MyProjects'
            }
        }
        return symbolic_links.get(self.tenant, {})

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

        self.home_path = self.set_home_path()
        self.symbolic_links = self.set_symbolic_links()

    def get_user(self, split_log):
        """
        Gets user from HTTP call

        :param split_log: current log split into an array
        :return: username or None if not found
        """
        hub_call = split_log[6]
        if 'client_id=' in hub_call:
            hub_call = hub_call.split('client_id=')
            jhub_user = hub_call[1].split('&', 1)[0]
            return jhub_user.split('-')[2]
        elif '/user/' in hub_call:
            split_call = hub_call.split('/')
            user_index = split_call.index('user')
            jhub_user = split_call[user_index+1]
            return jhub_user
        else:
            return None

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

    def get_file(self, split_log):
        """
        Gets file accessed in HTTP call

        :param split_log: current log split into an array
        :return: file accessed
        """
        file = re.search(r'[^/]*.ipynb', split_log[6]).group()
        file = self.parse_special_characters(file)
        return file

    def get_date_time(self, split_log):
        """
        Change date to YYYY-MM-DD format

        :param init_date: date from log
        :return: formatted date
        """
        timestamp = split_log[3][1:].split(':', 1)

        time = timestamp[1]
        dateobj = datetime.strptime(timestamp[0], "%d/%b/%Y").date()
        date = dateobj.strftime('%Y-%m-%d')
        return {'date': date, 'time': time}

    def get_info_from_log(self, split_log):
        """
        Change date to YYYY-MM-DD format

        :param init_date: date from log
        :return: formatted date
        """
        user = self.get_user(split_log)
        raw_filepath = self.get_path(split_log)
        path = self.get_true_path(user, raw_filepath)
        file = self.get_file(split_log)
        datetime_dict = self.get_date_time(split_log)
        date = datetime_dict['date']
        time = datetime_dict['time']
        ip_address = split_log[0]

        return {'user': user, 'raw_filepath': raw_filepath, 'path': path, 'file': file, 'date': date, 'time': time, 'ip_address': ip_address}

    def parse_login_info(self, split_log):
        """
        Get info from Tapis authorization call and log users

        :param split_log: current log split into an array
        :return: nothing
        """
        user = self.get_user(split_log)
        datetime_dict = self.get_date_time(split_log)
        date = datetime_dict['date']
        time = datetime_dict['time']
        info = {
            'user': user,
            'date': date,
            'time': time,
            'action': 'login',
            'ip_address': split_log[0]
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
        
        if insert: self.add_log_to_entries(info)

    def add_created_file(self, split_log):
        """
        Add file to created files dict

        :param split_log: current log split into an array
        :return: nothing
        """
        info = self.get_info_from_log(split_log)
        user = info['user']
        path = info['path']
        file = info['file']
        date = info['date']
        info['action'] = 'created'
        new_file = True
        new_date = True

        if user in self.created_files:
            if [path,file] not in self.created_files[user]:
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
        elif new_file == False and new_date:
            self.add_log_to_entries(info)


    def add_opened_file(self, split_log):
        """
        Add file to opened files dict

        :param split_log: current log split into an array
        :return:  nothing
        """
        info = self.get_info_from_log(split_log)
        user = info['user']
        path = info['path']
        file = info['file']
        date = info['date']
        info['action'] = 'opened'
        new_file = True
        new_date = True

        if user in self.opened_files:
            if [path,file] not in self.opened_files[user]:
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
        elif new_file == False and new_date:
            self.add_log_to_entries(info)