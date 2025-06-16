import omnitool.settings as settings
import omnitool.plugin.loading.loader as loader
from omnitool.main import main


def test_main(mocker):
    """
    Tests the main function of the omnitool package.
    Expects the settings and plugins to be loaded correctly.
    """
    mock_load_settings = mocker.patch.object(settings, "load_settings")
    mock_load_plugins = mocker.patch.object(loader, "load_plugins")
    main([])
    mock_load_settings.assert_called_once()
    mock_load_plugins.assert_called_once()
