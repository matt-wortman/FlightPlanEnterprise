from pathlib import Path

from app.core.plugins.registry import PluginRegistry


def test_plugin_registry_loads_manifest():
    plugins_dir = Path(__file__).resolve().parents[1] / "plugins"
    registry = PluginRegistry(plugins_dir=plugins_dir)
    registry.load_all()

    plugin = registry.get_plugin("cardiac")
    assert plugin is not None
    assert plugin.display_name == "Cardiac Surgery"


def test_plugin_registry_missing_plugin_returns_none():
    plugins_dir = Path(__file__).resolve().parents[1] / "plugins"
    registry = PluginRegistry(plugins_dir=plugins_dir)
    registry.load_all()
    assert registry.get_plugin("does-not-exist") is None
