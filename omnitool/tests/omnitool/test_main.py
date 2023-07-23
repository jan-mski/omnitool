from unittest.mock import patch

from omnitool.main import main


@patch("omnitool.plugin.loader.load_plugins")
def test_main(mock_load_plugins):
    main([])
    mock_load_plugins.assert_called_once()
