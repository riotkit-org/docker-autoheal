

class ProcessingException(Exception):
    pass


class ContainerIsLocked(ProcessingException):
    pass


class ConfigurationException(Exception):
    pass

