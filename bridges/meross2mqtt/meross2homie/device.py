import asyncio
from typing import TypeVar

from loguru import logger
from meross_iot.controller.device import BaseDevice
from meross_iot.controller.mixins.consumption import ConsumptionMixin, ConsumptionXMixin
from meross_iot.controller.mixins.electricity import ElectricityMixin
from meross_iot.model.http.device import HttpDeviceInfo

from meross2homie.config import CONFIG
from meross2homie.homie import (
    HomieDevice,
    HomieNode,
    HomieFloatProperty,
    HomieJsonProperty,
)

MD = TypeVar("MD", bound=BaseDevice)


def _channel_topic(topic: str, channel_id: int) -> str:
    return topic if channel_id == 0 else f"{topic}-{channel_id}"


def _channel_name(name: str, channel_id: int) -> str:
    return name if channel_id == 0 else f"{name} (channel {channel_id})"


class MerossHomieDevice(HomieDevice):
    def __init__(self, meross_device: MD, dev_info: HttpDeviceInfo):
        uuid = dev_info.uuid
        if (dev_cfg := CONFIG.devices.get(uuid)) and dev_cfg.pretty_name:
            name = dev_cfg.pretty_name
        else:
            name = dev_info.dev_name
        super().__init__(name)
        self.dev_info = dev_info
        self.meross_device = meross_device
        self._populate()

    @property
    def channels(self):
        # BaseDevice.channels returns List[ChannelInfo] with .index
        return [ch.index for ch in self.meross_device.channels]

    async def poll(self):
        md = self.meross_device
        updates = []

        await self.refresh()
        await md.async_update()

        if isinstance(md, (ConsumptionMixin, ConsumptionXMixin)):
            for channel_id in self.channels:
                try:
                    stats = await md.async_get_daily_power_consumption(channel=channel_id)
                    # stats: List[{'date': datetime, 'total_consumption_kwh': float}]
                    if stats:
                        last = sorted(stats, key=lambda x: x["date"], reverse=True)[0]
                        total = sum(x["total_consumption_kwh"] for x in stats)
                        history = [
                            {"timestamp": x["date"].isoformat(), "total_consumption_kwh": x["total_consumption_kwh"]}
                            for x in stats
                        ]
                        updates.append(
                            self[_channel_topic("energy", channel_id)]["history"].update_value(history)
                        )
                        updates.append(
                            self[_channel_topic("energy", channel_id)]["daily"].update_value(
                                last["total_consumption_kwh"]
                            )
                        )
                        updates.append(
                            self[_channel_topic("energy", channel_id)]["total"].update_value(total)
                        )
                except Exception:
                    logger.exception(
                        f"Failed to poll consumption for {self.dev_info.uuid} channel {channel_id}"
                    )

        if isinstance(md, ElectricityMixin):
            for channel_id in self.channels:
                try:
                    stats = await md.async_get_instant_metrics(channel_id)
                    updates.append(
                        self[_channel_topic("electricity", channel_id)]["voltage"].update_value(stats.voltage)
                    )
                    updates.append(
                        self[_channel_topic("electricity", channel_id)]["current"].update_value(stats.current)
                    )
                    updates.append(
                        self[_channel_topic("electricity", channel_id)]["power"].update_value(stats.power)
                    )
                except Exception:
                    logger.exception(
                        f"Failed to poll electricity for {self.dev_info.uuid} channel {channel_id}"
                    )

        await asyncio.gather(*updates)

    def _populate(self):
        md = self.meross_device

        logger.info(f"Device {self.dev_info.uuid} channels: {list(self.channels)}")

        if isinstance(md, (ConsumptionMixin, ConsumptionXMixin)):
            logger.info("Device supports consumption ability")
            for channel_id in self.channels:
                node = HomieNode(
                    self,
                    topic=_channel_topic("energy", channel_id),
                    name=_channel_name("Energy", channel_id),
                    node_type="stats",
                )
                HomieJsonProperty(node, topic="history", name="History")
                HomieFloatProperty(node, topic="daily", name="Daily consumption", unit="kWh")
                HomieFloatProperty(node, topic="total", name="Total consumption", unit="kWh")

        if isinstance(md, ElectricityMixin):
            logger.info("Device supports electricity ability")
            for channel_id in self.channels:
                node = HomieNode(
                    self,
                    topic=_channel_topic("electricity", channel_id),
                    name=_channel_name("Electricity", channel_id),
                    node_type="stats",
                )
                HomieFloatProperty(node, topic="voltage", name="Voltage", unit="V")
                HomieFloatProperty(node, topic="current", name="Current", unit="A")
                HomieFloatProperty(node, topic="power", name="Power usage", unit="W")
