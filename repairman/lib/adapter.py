
import abc
import docker
import time
import tornado.log
from .entity import Container, ApplicationGlobalPolicy
from .notify import Notify


class Adapter(metaclass=abc.ABCMeta):
    """ Adapter """

    @abc.abstractmethod
    def find_all_containers(self) -> list:
        pass

    @abc.abstractmethod
    def find_all_containers_in_namespace(self) -> list:
        pass

    @abc.abstractmethod
    def find_all_unhealthy_containers_in_namespace(self) -> list:
        pass

    @abc.abstractmethod
    def restart_container(self, container_id: str):
        pass

    @abc.abstractmethod
    def get_log(self, container_id: str, max_lines: int = 10):
        pass

    @abc.abstractmethod
    def remove_container(self, container_id: str):
        pass


class DockerAdapter(Adapter):
    api: docker.DockerClient
    policy: ApplicationGlobalPolicy
    notify: Notify
    _invalid_containers = {}

    def __init__(self, app_policy: ApplicationGlobalPolicy):
        self.policy = app_policy
        self.api = docker.from_env()
        self.notify = Notify(app_policy)

    def remove_container(self, container_id: str):
        container = self.api.containers.get(container_id)
        container.stop()
        container.remove()

    def restart_container(self, container_id: str):
        container = self.api.containers.get(container_id)
        t = time.time()
        container.restart()
        tornado.log.app_log.info('Container was restarted in ' + str(time.time() - t) + 's')

    def get_log(self, container_id: str, max_lines: int = 10):
        container = self.api.containers.get(container_id)
        return container.logs(tail=max_lines).decode('utf-8')

    def find_all_containers(self) -> list:
        return self._map_containers(self.api.containers.list())

    def find_all_containers_in_namespace(self) -> list:
        return self._map_containers(self._filter_by_prefix(self.api.containers.list()))

    def find_all_unhealthy_containers_in_namespace(self) -> list:
        unhealthy = list(
            filter(
                lambda container:
                    # WHEN is unhealthy (health)
                    (
                            "Health" in container.attrs['State']
                            and container.attrs['State']['Health']['Status'] == "unhealthy"
                    ) or (  # WHEN is exited by failure
                            container.status == "exited"
                            and (
                                    0 < container.attrs['State']['ExitCode'] < 130
                                    or container.attrs['State']['ExitCode'] > 200
                            )
                            # 130 > exit codes are keyboard interruption, sigkill, sigterm etc.
                            # lower exit codes are typically failures
                            # 200+ ex. 255 are generic errors
                    ),
                self.api.containers.list())
        )

        return self._map_containers(
            self._filter_by_prefix(unhealthy)
        )

    def _map_containers(self, containers: list):
        """ From internal docker container  """

        return list(filter(lambda x: x is not None, map(self._map_container, containers)))

    def _map_container(self, docker_container):
        container = None

        try:
            container = Container(
                docker_container.name,
                docker_container.status,
                docker_container.attrs['State']['ExitCode'],
                docker_container.attrs['Created'],
                self.policy.create_service_policy(
                    self.create_policy_params_from_docker_container_tags(
                        labels=docker_container.attrs['Config']['Labels']
                    )
                )
            )
            container.policy.validate()

        except Exception as e:
            # do not repeat the same notification twice or more too often
            if str(docker_container.name) in self._invalid_containers \
                    and self._invalid_containers[str(docker_container.name)] > time.time():
                return None

            self._invalid_containers[str(docker_container.name)] = time.time() + 600

            tornado.log.app_log.error(str(docker_container.name) + ': ' + str(e))
            tornado.log.app_log.error(str(docker_container.name) + ': Cannot monitor container due to ' +
                                      'configuration error. Please check container labels')

            if container:
                self.notify.container_configuration_invalid(container, str(e))
            else:
                self.notify.any_container_configuration_invalid(str(e))

            return None

        return container

    def _filter_by_prefix(self, containers: list):
        return list(filter(
            lambda docker_container: docker_container.name.startswith(self.policy.namespace),
            containers
        ))

    def create_policy_params_from_docker_container_tags(self, labels: dict):
        prefix = 'org.riotkit.repairman.'
        params = {}

        for key, value_type in self.policy._get_types().items():
            label_to_search_for = prefix + key.replace('-', '_')

            if label_to_search_for in labels:
                params[key] = labels[label_to_search_for]

        return params

