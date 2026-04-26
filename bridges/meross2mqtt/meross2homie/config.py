from dataclasses import dataclass, field
from typing import Optional, Dict

from dataclasses_json import DataClassJsonMixin, config
from yamldataclassconfig import YamlDataClassConfig

from meross2homie.homie import validate_homie_identifier


def _validate_topic(topic: Optional[str]) -> Optional[str]:
    if topic is None:
        return None
    return validate_homie_identifier(topic)


@dataclass
class DeviceConfig(DataClassJsonMixin):
    pretty_name: Optional[str] = None
    pretty_topic: Optional[str] = field(metadata=config(decoder=_validate_topic, encoder=str), default=None)


@dataclass
class Config(YamlDataClassConfig):
    log_level: str = "INFO"

    # MQTT broker (local Mosquitto on NAS)
    mqtt_host: str = None  # type: ignore
    mqtt_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    mqtt_clean_session: bool = False

    # Meross Cloud credentials
    meross_email: str = None  # type: ignore
    meross_password: str = None  # type: ignore

    # Homie MQTT protocol
    homie_prefix: str = field(metadata=config(decoder=_validate_topic, encoder=str), default="homie")
    """MQTT prefix of Homie devices in the configured MQTT broker. Default is the standard 'homie'."""

    # Bridge behaviour
    devices: Dict[str, DeviceConfig] = field(default_factory=dict)
    """Mapping from device UUIDs to {pretty_name: "Homie Device Name", pretty_topic: "homie-device-id"}"""

    polling_interval: Optional[int] = 30
    """Interval in seconds between each polling of the devices, or None to disable polling. Default: 30 seconds."""


CONFIG = Config()
