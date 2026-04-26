import asyncio
import random
from contextlib import AsyncExitStack
from typing import Optional, Dict

import aiomqtt
from loguru import logger
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager
from meross_iot.model.enums import OnlineStatus

from meross2homie.config import CONFIG
from meross2homie.device import MerossHomieDevice
from meross2homie.homie import Homie, HomieState

MEROSS_API_URL = "https://iotx-eu.meross.com"


def _mqtt_factory(will: Optional[aiomqtt.Will] = None, client_id_prefix: Optional[str] = None) -> aiomqtt.Client:
    if not client_id_prefix:
        client_id_prefix = "meross2homie"
    client_id = f"{client_id_prefix}_{random.randint(0, 1000000)}"
    client = aiomqtt.Client(
        hostname=CONFIG.mqtt_host,
        port=CONFIG.mqtt_port,
        username=CONFIG.mqtt_username,
        password=CONFIG.mqtt_password,
        identifier=client_id,
        will=will,
        clean_session=CONFIG.mqtt_clean_session,
    )
    client.pending_calls_threshold = 200
    return client


class BridgeManager:
    def __init__(self):
        self.homie = Homie(_mqtt_factory, CONFIG.homie_prefix)
        self.homie_devices: Dict[str, MerossHomieDevice] = {}
        self._meross_manager: Optional[MerossManager] = None
        self._http_client: Optional[MerossHttpClient] = None
        self._ctx: Optional[AsyncExitStack] = None

    async def __aenter__(self):
        self._ctx = AsyncExitStack()
        await self._ctx.__aenter__()

        # Connect to Meross Cloud
        logger.info("Connecting to Meross Cloud...")
        self._http_client = await MerossHttpClient.async_from_user_password(
            api_base_url=MEROSS_API_URL,
            email=CONFIG.meross_email,
            password=CONFIG.meross_password,
        )
        self._meross_manager = MerossManager(http_client=self._http_client)
        await self._meross_manager.async_init()
        logger.info("Connected to Meross Cloud")

        # Start Homie MQTT layer
        await self._ctx.enter_async_context(self.homie)

        # Discover all devices from cloud
        await self._discover_devices()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._meross_manager:
            self._meross_manager.close()
        if self._http_client:
            await self._http_client.async_logout()
        await self._ctx.__aexit__(exc_type, exc_val, exc_tb)

    async def _discover_devices(self):
        logger.info("Discovering Meross devices from cloud...")
        await self._meross_manager.async_device_discovery()

        devices = self._meross_manager.find_devices()
        logger.info(f"Found {len(devices)} device(s)")

        for meross_device in devices:
            uuid = meross_device.uuid
            dev_info = meross_device.device_info

            # Determine Homie topic
            if (dev_cfg := CONFIG.devices.get(uuid)) and dev_cfg.pretty_topic:
                topic = dev_cfg.pretty_topic
            else:
                topic = uuid

            homie_device = MerossHomieDevice(meross_device, dev_info)

            if not homie_device.nodes:
                logger.warning(
                    f"Device {dev_info.dev_name} ({uuid}) has no supported capabilities "
                    f"(needs ElectricityMixin or ConsumptionMixin) — skipping"
                )
                continue

            await self.homie.add_device(homie_device, topic)
            self.homie_devices[uuid] = homie_device
            await homie_device.set_state(HomieState.READY)
            logger.info(f"Registered device {dev_info.dev_name} ({uuid}) as homie topic '{topic}'")

    async def _poll(self):
        while True:
            try:
                await asyncio.gather(*(d.poll() for d in self.homie_devices.values()))
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                logger.exception("Unhandled exception while polling")
            await asyncio.sleep(CONFIG.polling_interval)

    async def process_events(self):
        logger.info("Starting poll loop")
        await asyncio.gather(self._poll(), self.homie.process_messages())
