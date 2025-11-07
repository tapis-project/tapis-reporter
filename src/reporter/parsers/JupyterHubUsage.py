import gzip
import logging
import re
from datetime import datetime

from ..apps.jupyterhub.models import FileLog, LoginLog, ParsedNginxFile
from ..helpers.jupyterhub_usage_funcions import get_home_path, get_symbolic_links

logger = logging.getLogger(__name__)


class JupyterHubUsage:
    """
    A class to parse NGINX log files from JupyterHub instances,
    extracting information about user logins, created files, and opened files
    """

    def __init__(self):
        """
        Initializes the JupyterHubUsage parser with empty dictionaries and lists
        to store parsed log data
        """
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

    def is_file_parsed(self, filename: str) -> bool:
        """
        Checks if an NGINX log file has already been parsed successfully

        :param filename: The name of the NGINX log file to check
        :return: True if the file exists in ParsedNginxFile and its status is 'Succeeded', otherwise False
        """
        logger.error(f"filename: {filename}")
        file_exists = ParsedNginxFile.objects.filter(pk=filename).exists()
        if file_exists:
            fileobj = ParsedNginxFile.objects.filter(pk=filename)[0]
            parsed_status = fileobj.status
            if parsed_status == "Succeeded":
                logger.error(f"{filename} exists -- skipping")
                return True
        return False

    def add_file_to_db(self, filename: str) -> bool:
        """
        Adds an entry for a new NGINX log file to the ParsedNginxFile table

        :param filename: The name of the NGINX log file to add
        :return: True if the file entry was successfully created, otherwise False
        """
        file_exists = ParsedNginxFile.objects.filter(pk=filename).exists()
        if not file_exists:
            try:
                ParsedNginxFile.objects.create(
                    filename=filename,
                    status="Queued",  # Initialize parsed status to 'queued'
                    error="",
                )
                return True
            except Exception as e:
                logger.exception(f"Error creating database entry for file: {filename}")
                logger.exception(e)
                return False

    def parse_jhub_file(self, file, filename: str) -> bool:
        """
        Parses a gzipped JupyterHub NGINX log file, extracting login,
        created file, and opened file information. Also updates the parsing
        status in the database

        :param file: The file object of the gzipped log file
        :param filename: The name of the log file being parsed
        :return: True if parsing and database additions are successful, otherwise False
        """

        # /api/contents is the endpoint of users interacting with the file/directory system
        CREATION_POST_PATTERN = (
            r'^.*?"POST /user/[^/]+/api/contents/.*? HTTP/1\.[01]" 201 .*$'
        )
        LOADING_GET_PATTERN = r'^.*?"GET /user/[^/]+/api/contents/.*?/Untitled\.ipynb\?.*? HTTP/1\.[01]" 200 .*$'
        creation_sequences = {}

        try:
            with gzip.open(file, "rt") as logfile:
                # Update ParsedNginxFile status to 'opened'
                ParsedNginxFile.objects.filter(pk=filename).update(status="Opened")

                for log in logfile:
                    self.set_tenant(log)
                    self.home_path = get_home_path(self.tenant)
                    self.symbolic_links = get_symbolic_links(self.tenant)

                    log_info = self.get_info_from_log(log)
                    if log_info is not None:
                        request_type = log_info["request_type"]
                        path = log_info["raw_path"]

                        # Check for login events
                        if "/hub/api/oauth2/authorize" in log:
                            self.add_login_entry(log_info)

                        if request_type == "POST" and re.search(
                            CREATION_POST_PATTERN, log
                        ):
                            if "checkpoint" in path:
                                continue
                            if log_info["user"] not in creation_sequences:
                                creation_sequences[log_info["ip_address"]] = []

                            creation_sequences[log_info["ip_address"]].append(
                                {"type": "Creation", "path": path}
                            )

                        if request_type == "GET" and re.search(
                            LOADING_GET_PATTERN, log
                        ):
                            if (
                                log_info["ip_address"] in creation_sequences
                                and creation_sequences[log_info["ip_address"]]
                                and creation_sequences[log_info["ip_address"]][-1][
                                    "type"
                                ]
                                == "Creation"
                            ):
                                self.add_created_file(log_info)

                        if log_info["file"] is not None and path is not None:
                            if (
                                request_type == "GET"
                                and "/user" in path
                                and ".ipynb" in log_info["file"]
                            ):
                                self.add_opened_file(log_info)

            success = True
            error = ""

            # Attempt to add collected file entries to the database
            if len(self.file_entries_to_add) > 0:
                files_added = self.add_file_entries_to_db()
                success = False if not files_added == "Added" else success
                error = files_added if not files_added == "Added" else ""

            # Attempt to add collected login entries to the database
            if len(self.login_entries_to_add) > 0:
                logins_added = self.add_login_entries_to_db()
                success = False if not logins_added == "Added" else success
                error = logins_added if not logins_added == "Added" else ""

            # Update ParsedNginxFile status based on success/failure
            if success:
                logger.info(f"{filename} -- Succeeded")
                ParsedNginxFile.objects.filter(pk=filename).update(status="Succeeded")
                return True
            else:
                logger.info(f"{filename} -- Failed")
                ParsedNginxFile.objects.filter(pk=filename).update(
                    status="Failed", error=error
                )
                return False
        except Exception as e:
            ParsedNginxFile.objects.filter(pk=filename).update(status="Failed", error=e)
            logger.exception(e)
            return False

    def add_file_entries_to_db(self) -> str:
        """
        Performs a bulk creation of FileLog entries collected during parsing

        :return: "Added" on success, or exception object on failure
        """
        try:
            FileLog.objects.bulk_create(self.file_entries_to_add)
            self.file_entries_to_add = []
            return "Added"
        except Exception as e:
            logger.error(f"Unable to add file entries; error: {e}")
            return e

    def add_login_entries_to_db(self) -> str:
        """
        Performs a bulk creation of LoginLog entries collected during parsing

        :return: "Added" on success, or exception object on failure
        """
        try:
            LoginLog.objects.bulk_create(self.login_entries_to_add)
            self.login_entries_to_add = []
            return "Added"
        except Exception as e:
            logger.error(f"Unable to add login entries; error: {e}")
            return e

    def add_log_to_entries(self, info: dict) -> None:
        """
        Adds a parsed log entry (either FileLog or LoginLog) to the appropriate
        batch list for later bulk insertion into the database

        :param info: A dictionary containing parsed information from a log line
        :return: None. Updates lists `file_entries_to_add` or `login_entries_to_add`
        """
        # Ensure user is a string; log and skip if not valid
        if not isinstance(info["user"], str):
            logger.error(f"NO USER FOUND: {info} -- SKIPPING")
            return

        # Use IP address as user if user is empty
        user = info["ip_address"] if info["user"] == "" else info["user"]
        if info["action"] in ["created", "opened"]:
            self.file_entries_to_add.append(
                FileLog(
                    tenant=self.tenant,
                    user=user,
                    action=info["action"],
                    filepath=info["path"],
                    filename=info["file"],
                    date=info["date"],
                    time=info["time"],
                    raw_filepath=info["raw_path"],
                )
            )
        else:
            self.login_entries_to_add.append(
                LoginLog(
                    tenant=self.tenant, user=user, date=info["date"], time=info["time"]
                )
            )

    def set_tenant(self, log: str) -> None:
        """
        Identifies and sets the `tenant` based on keywords found in the log line.
        Supports 'tacc' and 'designsafe' tenants

        :param log: The raw log line
        :return: None. Updates the `self.tenant` attribute
        """
        split_log = re.split(r"\s", log)
        if "jupyter.tacc.cloud" in log or "/home/jovyan/" in split_log[6]:
            self.tenant = "tacc"
        elif "jupyter.designsafe-ci.org" in log or "/home/jupyter/" in split_log[6]:
            self.tenant = "designsafe"

    def get_user(self, path: str) -> str | None:
        """
        Extracts the username from a given URL path. Looks for patterns
        related to `client_id` or `/user/` in the path

        :param path: The URL path from the log entry
        :return: The extracted username as a string, or None if not found
        """
        split_with_user = None
        if "client_id=" in path:
            split_client = path.split("client_id=")
            split_path = split_client[1].split("&", 1)[0]
            split_with_user = split_path.split("-")
        elif "/user/" in path:
            split_with_user = path.split("/")

        if split_with_user is not None:
            try:
                user_index = split_with_user.index("user")
                jhub_user = split_with_user[user_index + 1]
                return jhub_user
            except ValueError:
                pass

        return None

    def parse_special_characters(self, s: str) -> str:
        """
        Replaces common encoded characters in a string with their
        represented characters

        :param s: The input string to decode
        :return: The string with encoded characters replaced
        """
        s = s.replace("%20", " ")
        s = s.replace("%C3%B3", "o")
        s = s.replace("%C3%A1", "a")
        s = s.replace("%3A", ":")
        s = s.replace("%26", "&")
        return s

    def check_for_symbolic_link(self, path: str) -> str:
        """
        Checks if a given path contains a known symbolic link and replaces
        it with the corresponding true path from self.symbolic_links

        :param path: The path to check
        :return: The updated path with symbolic link resolved, or the original path if no link found
        """
        for key in self.symbolic_links:
            if key in path:
                new_path = path.replace(key, self.symbolic_links[key])
                return new_path
        return path

    def get_true_path(self, user: str, path: str) -> str:
        """
        Determines the absolute file path based on the user's home path
        and known network path patterns. Also resolves symbolic links

        :param user: Username associated with the path
        :param path: Network path from the log
        :return: Absolute file path, or the original path if resolution fails
        """
        network_paths = [
            f"/user/{user}/notebooks",
            f"/user/{user}/api/contents",
            f"/user/{user}/files",
            f"/user/{user}/lab/tree",
            f"/user/{user}/nbconvert/script",
            f"/user/{user}/edit",
        ]
        for network_path in network_paths:
            if network_path in path:
                if self.home_path != "":
                    true_path = path.replace(network_path, self.home_path)
                    true_path = self.check_for_symbolic_link(true_path)
                    return true_path
        return path

    def get_path(self, path: str) -> str:
        """
        Gets path accessed in HTTP call

        :param split_log: URL path from the log
        :return: Extracted directory path
        """
        init_path = path.rsplit("/", 1)
        if ".ipynb" in init_path[0]:
            file_path = init_path[0].rsplit("/", 1)[0]
        else:
            file_path = init_path[0]
        return self.parse_special_characters(file_path)

    def get_file(self, path: str) -> str:
        """
        Extracts filename from a given URL path

        :param path: Full URL path from the log entry
        :return: Extracted filename, or None if not found
        """
        file = re.search(r"[^/]*.ipynb", path)
        if file:
            file = file.group()
            file = self.parse_special_characters(file)
        return file

    def get_date(self, date_str: str) -> str:
        """
        Converts a date string from "%d/%b/%Y" format
        to "%Y-%m-%d" format

        :param date_str: Date string from the log
        :return: Formatted date string
        """
        date_obj = datetime.strptime(date_str, "%d/%b/%Y")
        return date_obj.strftime("%Y-%m-%d")

    def get_info_from_log(self, log: str) -> dict | None:
        """
        Parses a single NGINX log line using a regular expression to extract
        date, request type, time, IP address, and system info. Also fills in
        user, different paths, and file name

        :param log: Raw NGINX log line
        :return: Dictionary containing parsed log information, or None if the log line doesn't match the regex
        """
        regex = re.compile(
            r'(?P<client_ip>\S+) - - \[(?P<date>\d{2}\/\w+\/\d{4}):(?P<time>\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status_code>\d+) (?P<bytes_sent>\d+) "(?P<referer>[^"]+)" "(?P<user_agent>[^"]*)" "-"'
        )
        match = regex.match(log)

        if not match:
            return

        log_info = {name: match.group(name) for name in match.groupdict()}
        try:
            user = self.get_user(log_info["path"])
            raw_path = log_info["path"]
            network_path = (
                self.get_path(log_info["path"]) if log_info["path"] is not None else ""
            )
            path = self.get_true_path(user, network_path)
            file = self.get_file(log_info["path"])
            date = self.get_date(log_info["date"])
            request_type = log_info["method"]

            time = log_info["time"].split(" ")[0]
            ip_address = log_info["client_ip"]
            system_info = log_info["user_agent"]
            return {
                "user": user,
                "raw_path": raw_path,
                "network_path": network_path,
                "path": path,
                "file": file,
                "date": date,
                "time": time,
                "ip_address": ip_address,
                "request_type": request_type,
                "system_info": system_info,
            }
        except Exception as e:
            logger.error(f"Error for log: {log}; error: {e}")

        return None

    def add_login_entry(self, log_info: dict) -> None:
        """
        Processes a login event, tracking user login counts and times.
        Adds the login information to the login list if it represents
        a new session (based on a 2-minute time difference)

        :param log_info: Dictionary containing parsed login information
        :return: None. Updates login_entries_to_add
        """
        user = log_info["user"]
        date = log_info["date"]
        time = log_info["time"]

        info = {
            "user": user,
            "date": date,
            "time": time,
            "action": "login",
            "ip_address": log_info["ip_address"],
            "system_info": log_info["system_info"],
            "raw_path": log_info["raw_path"],
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

    def add_created_file(self, info: dict) -> None:
        """
        Adds a created file event from a log entry if it's a new file
        or a new date for an existing file

        :param info: Dictionary containing parsed file creation information
        :return: None. Updates file_entries_to_add
        """
        user = info["user"]
        path = info["path"]
        file = info["file"]
        date = info["date"]
        info["action"] = "created"
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
            self.daily_files[date][user]["created"] = self.created_files[user]
        else:
            self.daily_files[date] = {}
            self.daily_files[date][user] = {}
            self.daily_files[date][user]["created"] = self.created_files[user]

        if new_file or new_date:
            self.add_log_to_entries(info)
        elif not new_file and new_date:
            self.add_log_to_entries(info)

    def add_opened_file(self, info: dict) -> None:
        """
        Adds an opened file event from a log entry if it's a new file
        or a new date for an existing file

        :param info: Dictionary containing parsed file creation information
        :return: None. Updates file_entries_to_add
        """
        user = info["user"]
        path = info["path"]
        file = info["file"]
        date = info["date"]
        info["action"] = "opened"
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
            self.daily_files[date][user]["opened"] = self.opened_files[user]
        else:
            self.daily_files[date] = {}
            self.daily_files[date][user] = {}
            self.daily_files[date][user]["opened"] = self.opened_files[user]

        if new_file or new_date:
            self.add_log_to_entries(info)
        elif not new_file and new_date:
            self.add_log_to_entries(info)
