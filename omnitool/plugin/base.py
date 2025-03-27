from typing import Dict

from omnitool.plugin.configuration import PluginConfigurationService, ContextConfiguration, ContextResourceConfiguration
from omnitool.plugin.finder import PluginLocation
from omnitool_plugin_base.plugin.base import PluginDefinition


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
        return self._configuration_service.get_contexts()

    def add_resource(self, context_id: str, resource: ContextResourceConfiguration):
        self._configuration_service.add_resource(context_id, resource)
