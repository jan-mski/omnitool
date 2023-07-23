from omnitool.main import main


def test_main(mocker):
    mock_load_plugins = mocker.patch("omnitool.plugin.loader.load_plugins")
    main([])
    mock_load_plugins.assert_called_once()
