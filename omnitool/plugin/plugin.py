from typing import Dict

from omnitooldef.plugin.definition import PluginDefinition
from omnitool.plugin.configuration import PluginConfigurationService, ContextConfiguration
from omnitool.plugin.finder import PluginLocation


class Plugin:
    definition: PluginDefinition
    location: PluginLocation
    _configuration_service: PluginConfigurationService

    def __init__(self,
                 configuration_service: PluginConfigurationService,
                 definition: PluginDefinition,
                 location: PluginLocation):
        self._configuration_service = configuration_service
        self.definition = definition
        self.location = location

    @property
    def name(self) -> str:
        return self.definition.name

    def get_contexts(self) -> Dict[str, ContextConfiguration]:
        return {}
