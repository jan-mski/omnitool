import omnitool.main
from omnitool.main import main


def test_main(mocker):
    mock_load_settings = mocker.patch.object(omnitool.main.settings, "load_settings")
    mock_load_plugins = mocker.patch.object(omnitool.main.loader, "load_plugins")
    main([])
    mock_load_settings.assert_called_once()
    mock_load_plugins.assert_called_once()
