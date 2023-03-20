class MissingAttributeError(Exception):
    """
    Exception raised when an attribute is missing in a file
    """

    def __init__(self, path, missing):
        self.path = path
        self.missing = missing
        super().__init__(f"Missing attribute {missing} in '{path}'")

class MissingEnvironmentError(Exception):
    """
    Exception raised when a needed environment variable is not defined
    """

    def __init__(self, missing):
        self.missing = missing
        super().__init__(f"Missing environment variable {missing}")

class StorageError(Exception):
    """
    Exception raised when an issue occured when using a storage
    """

    def __init__(self, type, issue):
        self.type = type
        self.issue = issue
        super().__init__(f"Issue occured using a {type} storage : {issue}")

class FormatError(Exception):
    """
    Exception raised when a format is expected but not respected
    """

    def __init__(self, expected_format, content, issue):
        self.expected_format = expected_format
        self.content = content
        self.issue = issue
        super().__init__(f"Expected format {expected_format} to read '{content}' : {issue}")
