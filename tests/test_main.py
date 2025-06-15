import omnitool.settings as settings
import omnitool.plugin.loading.loader as loader
from omnitool.main import main


def test_main(mocker):
    mock_load_settings = mocker.patch.object(settings, "load_settings")
    mock_load_plugins = mocker.patch.object(loader, "load_plugins")
    main([])
    mock_load_settings.assert_called_once()
    mock_load_plugins.assert_called_once()
