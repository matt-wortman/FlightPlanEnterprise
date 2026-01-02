from fastapi import APIRouter

from app.core.plugins.registry import plugin_registry

router = APIRouter(prefix="/api/v1", tags=["plugins"])


@router.get("/specialties")
async def list_specialties() -> list[dict]:
    return [
        {
            "name": plugin.name,
            "version": plugin.version,
            "displayName": plugin.display_name,
        }
        for plugin in plugin_registry.get_all_plugins()
    ]


@router.get("/specialties/{name}/config")
async def get_specialty_config(name: str) -> dict:
    plugin = plugin_registry.get_plugin(name)
    if not plugin:
        return {"detail": "not found"}
    return plugin.manifest.get("spec", {}).get("ui", {})
