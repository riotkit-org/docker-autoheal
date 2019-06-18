
from .entity import Container, ApplicationGlobalPolicy
import abc
import docker


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

    def __init__(self, app_policy: ApplicationGlobalPolicy):
        self.policy = app_policy
        self.api = docker.from_env()

    def remove_container(self, container_id: str):
        container = self.api.containers.get(container_id)
        container.stop()
        container.remove()

    def restart_container(self, container_id: str):
        container = self.api.containers.get(container_id)
        container.restart()

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

        return list(map(
            lambda docker_container: Container(
                docker_container.name,
                docker_container.status,
                docker_container.attrs['State']['ExitCode'],
                docker_container.attrs['Created'],
                self.policy.create_service_policy(
                    self.create_policy_params_from_docker_container_tags(
                        labels=docker_container.attrs['Config']['Labels']
                    )
                )
            ),
            containers
        ))

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

