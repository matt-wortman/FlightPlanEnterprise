from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PluginMetadata(BaseModel):
    name: str
    version: str
    displayName: str | None = None
    description: str | None = None


class PluginManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    apiVersion: str = Field(default="flightplan.io/v1")
    kind: str = Field(default="SpecialtyPlugin")
    metadata: PluginMetadata
    spec: dict[str, Any] = Field(default_factory=dict)
