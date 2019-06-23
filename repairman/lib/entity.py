
from .exception import ConfigurationException


class Policy:
    """ Defines how to treat the Container. Policy is immutable. """

    _parent_policy: None  # type: ApplicationGlobalPolicy
    _params: dict
    _types = {
        'seconds_between_restarts': int,
        'max_restarts_in_frame': int,
        'seconds_between_next_frame': int,
        'frame_size_in_seconds': int,
        'interval': int,
        'max_checks_to_give_up': int,
        'notify_url': str,
        'notify_level': str,
        'enable_cleaning_duplicated_services': bool
    }

    def __init__(self, params: dict, parent_policy=None):
        self._params = {}
        self._parent_policy = parent_policy
        types_available = self._get_types()

        for key, value in params.items():
            if key not in types_available:
                raise ConfigurationException('"' + key + '" argument is unsupported by the ' + str(self))

            self._params[key] = self.cast(value, types_available[key])

    @property
    def seconds_between_restarts(self) -> int:
        return self._params['seconds_between_restarts']

    @property
    def max_restarts_in_frame(self) -> int:
        return self._params['max_restarts_in_frame']

    @property
    def seconds_between_next_frame(self) -> int:
        return self._params['seconds_between_next_frame']

    @property
    def frame_size_in_seconds(self) -> int:
        return self._params['frame_size_in_seconds']

    @property
    def interval(self) -> int:
        return self._params['interval']

    @property
    def max_checks_to_give_up(self) -> int:
        return self._params['max_checks_to_give_up']

    @property
    def enable_cleaning_duplicated_services(self) -> bool:
        return self._params['enable_cleaning_duplicated_services']

    @property
    def notify_url(self) -> str:
        return self._params['notify_url']

    @property
    def notify_level(self) -> str:
        return self._params['notify_level']

    def to_dict(self) -> dict:
        return self._params

    def _get_types(self) -> dict:
        return self._types

    @staticmethod
    def cast(value, value_type: type):
        if value_type == bool:
            return str(value).lower() in ['true', 'yes', '1', 'y']

        elif value_type == int:
            return int(value)

        return str(value)

    def validate(self):
        if self._parent_policy:
            max_history = self._parent_policy.max_historic_entries

            if self.max_restarts_in_frame > max_history:
                raise ConfigurationException(
                    'Please increase max-historic-entries above max-restarts of each service')

            if self.max_checks_to_give_up > max_history:
                raise ConfigurationException(
                    'Please increase max-historic-entries above max-checks-to-give-up of each service')

        if self.max_checks_to_give_up and self.max_checks_to_give_up < self.max_restarts_in_frame:
            raise ConfigurationException('max-checks-to-give-up cannot be lower than max-restarts-in-frame')

        restart_operation_timeout_margin = 8  # in seconds
        proposed_min_frame_size = self.max_restarts_in_frame * restart_operation_timeout_margin * \
                                  self.seconds_between_restarts

        if self.frame_size_in_seconds < proposed_min_frame_size:
            raise ConfigurationException('Min frame size in seconds should be at' +
                                         ' least "' + str(proposed_min_frame_size) + '". ' +
                                         'Got "' + str(self.frame_size_in_seconds) + '"')


class ApplicationGlobalPolicy(Policy):
    """ Policy/Settings for whole application. Defaults for each container.  """

    _global_policy_types = {
        'debug': bool,
        'namespace': str,
        'max_historic_entries': int,
        'db_path': str
    }

    def __init__(self, params: dict):
        super().__init__(params)
        self.validate()

    @property
    def debug(self) -> bool:
        return self._params['debug']

    @property
    def namespace(self) -> str:
        return self._params['namespace']

    @property
    def max_historic_entries(self) -> int:
        return self._params['max_historic_entries']

    @property
    def clean_up_duplicated_services_after_update(self) -> bool:
        return self._params['enable_cleaning_duplicated_services']

    @property
    def db_path(self) -> str:
        return self._params['db_path']

    def create_service_policy(self, modified_params: dict) -> Policy:
        """ Create a regular Policy object for container mixing default values from ApplicationGlobalPolicy
            and applying modifications from container labels/environment or from other source
        """

        new_params = {}

        for key, value in self._params.items():
            if key in self._global_policy_types:
                continue

            new_params[key] = value

        for key, value in modified_params.items():
            if key not in self._types:
                raise ConfigurationException('Invalid setting "' + key + '" coming from container, ' +
                                             'not supported by policy')

            new_params[key] = value

        return Policy(new_params, self)

    def _get_types(self) -> dict:
        return {**self._types, **self._global_policy_types}


class Container:
    _name: str
    _status: str
    _exit_code: int
    _created_at: str
    _policy: Policy

    def __init__(self, name: str, status: str, exit_code: int, created_at: str, policy: Policy):
        self._name = name
        self._status = status
        self._exit_code = exit_code
        self._created_at = created_at
        self._policy = policy

    def get_name(self) -> str:
        return self._name

    def identify(self) -> str:
        return self.get_name()

    @property
    def policy(self):
        return self._policy


class ContainerFactory:
    pass
