import os
import django
import logging
from typing import List

os.environ["DJANGO_SETTINGS_MODULE"] = "reporter.settings"
django.setup()

from ..parsers.JupyterHubUsage import JupyterHubUsage
from ..parsers.TapisUsage import TapisUsage

logger = logging.getLogger(__name__)


class LogParser:
    """
    Handles parsing the NGINX log files from the service's network activity

    """
    def __init__(self, service):
        self.service = service
        self.file_dir = self.get_file_dir(service)

    @classmethod
    def get_file_dir(self, service):
        return f'/app/reporter/filelogs/{service}'

    def parse_logs(self) -> None:
        """
        Reads file line by line and call appropriate function

        :param file: file to be parsed
        :param files_successfully_parsed: array to be appended to
        :param files_failed_to_parse: array to be appended to
        :return: nothing
        """

        match self.service:
            case 'jupyterhub':
                files_to_parse = self.get_files_to_parse()
                self.parse_files(files_to_parse)
            case 'tapis':
                self.parse_splunk()
            case _:
                return
    
    def get_files_to_parse(self) -> List[str]:
        """
        First function called.
        > go through the service's directory
        > make list of files to parse
        > call function to parse files

        :return: list of files to parse
        """

        # Reformat the file path to match 'ex.'
        files_to_parse = os.listdir(self.file_dir) if self.file_dir != "" else []
        if self.file_dir != "": 
            if self.file_dir[-1] == '/':
                self.file_dir = self.file_dir[:-1]
            for i in range(len(files_to_parse)):
                files_to_parse[i] = self.file_dir + "/" + files_to_parse[i]

        return files_to_parse

    def parse_files(self, files: List[str]):
        """
        Go through list of files and call function to parse each file

        :return: nothing
        """
        logger.debug(f'Files to parse: {files}')
        files_successfully_parsed = []
        files_failed_to_parse = []
        for file in files:
            self.parse_file(file,
                            files_successfully_parsed,
                            files_failed_to_parse)

        logger.debug(f"Files successfully parsed: {files_successfully_parsed}")
        logger.debug(f"Files failed to parse: {files_failed_to_parse}")

    def parse_file(self, file, files_successfully_parsed, files_failed_to_parse):
        filename = os.path.basename(file)

        match self.service:
            case 'jupyterhub':
                parser = JupyterHubUsage()
                has_been_parsed = parser.is_file_parsed(filename)

                if not has_been_parsed:
                    # add file entry to ParsedNginxFile db
                    parser.add_file_to_db(filename)

                    # parse the file
                    file_parsed = parser.parse_jhub_file(file, filename)

                    if file_parsed: files_successfully_parsed.append(filename)
                    else: files_failed_to_parse.append(filename)
            case _:
                return

    def parse_splunk(self):
        match self.service:
            case 'tapis':
                parser = TapisUsage()
                parser.query_splunk()
            case _:
                return
