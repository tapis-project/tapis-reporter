from abc import ABC, abstractmethod

from ..helpers.ApiCalls import query_splunk


class BaseSource(ABC):
    """ """

    @abstractmethod
    def connect(self):
        """
        Class responsible for handling connection to source. Sub classes must implement

        Raises
        ------
        NotImplementedError:
            Error is raised if function is not implemented in subclass
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_data(self):
        """
        Class responsible for handling data fetching from source. Sub classes must implement

        Raises
        ------
        NotImplementedError:
            Error is raised if function is not implemented in subclass
        """
        raise NotImplementedError


class SplunkSource(BaseSource):
    """
    SplunkSource handles connections and data retrieval from Splunk

    Args:
        host (str): Where the Splunk instance lives
        port (int): The port of the Splunk instance
        username (str): Username to authenticate with
        password (str): Password to authenticate with
        scheme (str): http or https of Splunk instance
        search (str): Base 64 encoded string of search query
    """

    def __init__(self, **kwargs):
        try:
            self.validate_kwargs(kwargs)
        except TypeError as e:
            print(e)
            return e

        self.host = kwargs["host"]
        self.port = kwargs["port"]
        self.username = kwargs["username"]
        self.password = kwargs["password"]
        self.scheme = kwargs["scheme"]
        self.search = kwargs["search"]

    def validate_kwargs(self, kwargs):
        """
        This function is used to filter out any unwanted kwarg arguments and to check the type of each kwarg

        Raises
        ------
        TypeError:
            Error raised if keyword doesn't exist or type does not match expected type
        """
        allowed_kwargs = {
            "host": str,
            "port": int,
            "username": str,
            "password": str,
            "scheme": str,
            "search": str,
        }

        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Got unexpected keyword argument: {key}")
            value = kwargs[key]
            exp_type = allowed_kwargs[key]

            if value is not None and not isinstance(value, exp_type):
                raise TypeError(
                    f"Expected {key} to be {exp_type.__name__}, got {type(kwargs[key]).__name__}"
                )

    def test_connection(self) -> dict:
        """
        This function is used to test the connection to the Splunk instance

        Returns
        -------
        dict
            Result count and sample result, or error
        """
        try:
            result = query_splunk(
                self.host,
                self.port,
                self.username,
                self.password,
                self.scheme,
                self.search,
                True,
            )

            return {
                "result_count": result["result_count"],
                "sample_result": result["sample_result"],
            }
        except Exception as e:
            print(e)
            return {"error": e}

    def connect(self):
        pass

    def fetch_data(self):
        pass
