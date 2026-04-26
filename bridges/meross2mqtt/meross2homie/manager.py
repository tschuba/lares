import asyncio
import json
import random
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Optional, Dict

import aiomqtt
from loguru import logger
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager
from meross_iot.model.credentials import MerossCloudCreds
from meross_iot.model.http.exception import TooManyTokensException, UnauthorizedException

from meross2homie.config import CONFIG
from meross2homie.device import MerossHomieDevice
from meross2homie.homie import Homie, HomieState

MEROSS_API_URL = "https://iotx-eu.meross.com"
CREDS_FILE = Path("/config/meross_creds.json")


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


def _load_cached_creds() -> Optional[MerossCloudCreds]:
    if not CREDS_FILE.exists():
        return None
    try:
        creds = MerossCloudCreds.from_json(CREDS_FILE.read_text())
        logger.info(f"Loaded cached Meross credentials from {CREDS_FILE}")
        return creds
    except Exception:
        logger.warning(f"Failed to load cached credentials from {CREDS_FILE}, will re-login")
        return None


def _save_creds(creds: MerossCloudCreds):
    try:
        CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        CREDS_FILE.write_text(creds.to_json())
        logger.debug(f"Saved Meross credentials to {CREDS_FILE}")
    except Exception:
        logger.warning(f"Failed to save credentials to {CREDS_FILE}")


def _delete_cached_creds():
    try:
        if CREDS_FILE.exists():
            CREDS_FILE.unlink()
            logger.info(f"Deleted cached credentials {CREDS_FILE}")
    except Exception:
        logger.warning(f"Failed to delete cached credentials {CREDS_FILE}")


async def _login() -> MerossHttpClient:
    """Login with email/password, save token, return http client."""
    logger.info("Logging in to Meross Cloud with email/password...")
    http_client = await MerossHttpClient.async_from_user_password(
        api_base_url=MEROSS_API_URL,
        email=CONFIG.meross_email,
        password=CONFIG.meross_password,
    )
    _save_creds(http_client.cloud_credentials)
    return http_client


async def _get_http_client() -> MerossHttpClient:
    """Return an authenticated MerossHttpClient, using cached token if available."""
    creds = _load_cached_creds()
    if creds is not None:
        try:
            http_client = await MerossHttpClient.async_from_cloud_creds(creds)
            logger.info("Connected to Meross Cloud using cached token")
            return http_client
        except (UnauthorizedException, TooManyTokensException):
            logger.warning("Cached token is invalid or expired, re-logging in...")
            _delete_cached_creds()

    return await _login()


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

        # Connect to Meross Cloud (reuse cached token if available)
        logger.info("Connecting to Meross Cloud...")
        self._http_client = await _get_http_client()
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
        # Do NOT logout — that would invalidate the cached token.
        # The token will be reused on next start.
        await self._ctx.__aexit__(exc_type, exc_val, exc_tb)

    async def _discover_devices(self):
        logger.info("Discovering Meross devices from cloud...")
        await self._meross_manager.async_device_discovery()

        devices = self._meross_manager.find_devices()
        logger.info(f"Found {len(devices)} device(s)")

        for meross_device in devices:
            uuid = meross_device.uuid
            dev_info = meross_device.cached_http_info

            # Determine Homie topic
            if (dev_cfg := CONFIG.devices.get(uuid)) and dev_cfg.pretty_topic:
                topic = dev_cfg.pretty_topic
            else:
                topic = uuid

            homie_device = MerossHomieDevice(meross_device, dev_info)

            if not homie_device.children:
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
