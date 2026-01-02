from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml

from app.core.config import get_settings
from app.core.plugins.manifest import PluginManifest


@dataclass
class SpecialtyPlugin:
    name: str
    version: str
    display_name: str | None
    manifest: dict


class PluginRegistry:
    """Discovers, loads, and manages specialty plugins."""

    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self._plugins: dict[str, SpecialtyPlugin] = {}
        self._loaded = False

    def discover_plugins(self) -> list[str]:
        plugins: list[str] = []
        if not self.plugins_dir.exists():
            return plugins
        for path in self.plugins_dir.iterdir():
            if path.is_dir() and (path / "manifest.yaml").exists():
                plugins.append(path.name)
        return plugins

    def load_plugin(self, name: str) -> SpecialtyPlugin:
        plugin_path = self.plugins_dir / name
        manifest_path = plugin_path / "manifest.yaml"

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_dict = yaml.safe_load(f)

        manifest = PluginManifest.model_validate(manifest_dict)

        plugin = SpecialtyPlugin(
            name=manifest.metadata.name,
            version=manifest.metadata.version,
            display_name=manifest.metadata.displayName,
            manifest=manifest_dict,
        )

        self._plugins[plugin.name] = plugin
        return plugin

    def load_all(self) -> None:
        for name in self.discover_plugins():
            self.load_plugin(name)
        self._loaded = True

    def get_plugin(self, name: str) -> Optional[SpecialtyPlugin]:
        return self._plugins.get(name)

    def get_all_plugins(self) -> list[SpecialtyPlugin]:
        return list(self._plugins.values())

    def get_ui_config(self, specialty: str) -> dict:
        plugin = self._plugins.get(specialty)
        if not plugin:
            return {}
        return plugin.manifest.get("spec", {}).get("ui", {})


settings = get_settings()
_base = Path(__file__).resolve().parents[3]
plugins_dir = Path(settings.plugins_dir)
if not plugins_dir.is_absolute():
    plugins_dir = _base / plugins_dir

plugin_registry = PluginRegistry(plugins_dir=plugins_dir)
