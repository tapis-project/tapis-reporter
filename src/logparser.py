import os
import django
import argparse
import re
from datetime import datetime
import json
import logging
from collections import defaultdict
import sys
import gzip

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from reporter.apps.jupyterhub.functions import JupyterHubUsage
from reporter.apps.tapis.service_config import TapisServiceConfig


logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Process arguments')
parser.add_argument('service')
args = parser.parse_args()

#services = Services.objects.all().values('tenant')
valid_services = ['jupyterhub', 'tapis']
# for service in list(services):
#     valid_services.append(service['service'])

service = args.service
if service not in valid_services:
    logger.error(f'{service} not a valid service, expecting one of: {valid_services}')
    sys.exit()

class LogParser:
    """
    Handles parsing the log files pertaining to JupyterHub's NGINX network activity

    """
    def __init__(self, service):
        self.service = service
        #self.service_handler = self.get_service_handler(service)
        self.file_dir = self.get_file_dir(service)
    
    @classmethod
    def get_service_handler(self, service):
        match service:
            case 'jupyterhub':
                return JupyterHubUsage()
            case 'tapis':
                return
    
    @classmethod
    def get_file_dir(self, service):
        filelogs_path = '/app/reporter/filelogs/'
        match service:
            case 'jupyterhub':
                return filelogs_path + 'jupyter/'
            case 'tapis':
                return


    def parse(self):
        """
        Go through list of files and parse the logs

        :return: nothing, but will print which files succeeded or failed
        """
        files_to_parse = os.listdir(self.file_dir) if self.file_dir != "" else []
        if self.file_dir != "": 
            if self.file_dir[-1] == '/': self.file_dir = self.file_dir[:-1]
            for i in range(len(files_to_parse)):
                files_to_parse[i] = self.file_dir + "/" + files_to_parse[i]
        
        logger.error(f'Parse: {files_to_parse}')
        files_successfully_parsed = []
        files_failed_to_parse = []
        for file in files_to_parse:
            self.parse_file(file, files_successfully_parsed, files_failed_to_parse)
            self.file_entries_to_add = []
            self.login_entries_to_add = []

        logger.debug(f"Files unable to parse: {files_failed_to_parse}")
        logger.debug(f"Files successfully parsed: {files_successfully_parsed}")

    def parse_file(self, file, files_successfully_parsed, files_failed_to_parse):
        """
        Read a file line by line and call appropriate function

        :param file: file to be parsed
        :return: nothing
        """
        filename = os.path.basename(file)

        match service:
            case 'jupyterhub':
                logger.error('Case: jupyterhub')
                parser = JupyterHubUsage()
                status = parser.check_for_jhub_file(filename)
                if not status:
                    files_failed_to_parse.append(filename)
                    return
                parsed = parser.parse_jhub_file(file, filename)
                if parsed: files_successfully_parsed.append(filename)
                else: files_failed_to_parse.append(filename)
            case 'tapis':
                return

if __name__ == '__main__':
    logParser = LogParser(service)
    logParser.parse()
