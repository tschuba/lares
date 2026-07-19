import asyncio
import json
import logging
import os
from datetime import datetime, timezone

import aiohttp
import aiomqtt
from myskoda import MySkoda
from myskoda.auth.authorization import (
    AuthorizationError,
    AuthorizationFailedError,
    CSRFError,
    MarketingConsentError,
    TermsAndConditionsError,
    TokenExpiredError,
)

_LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(level=_LOG_LEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("skoda2mqtt")

USERNAME = os.getenv("MYSKODA_USERNAME")
PASSWORD = os.getenv("MYSKODA_PASSWORD")
VIN = os.getenv("MYSKODA_VIN")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))
MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASS = os.getenv("MQTT_PASSWORD")
TOPIC_STATE = "ev/skoda/state"
TOPIC_COMMAND = "ev/skoda/command"
TOPIC_STATUS = "ev/skoda/status"

AUTH_MAX_RETRIES = int(os.getenv("AUTH_MAX_RETRIES", 3))
AUTH_BACKOFF_BASE = int(os.getenv("AUTH_BACKOFF_BASE", 10))
BACKOFF_CAP = 300
AUTH_COOLDOWN_BASE = int(os.getenv("AUTH_COOLDOWN_BASE", 1800))
AUTH_COOLDOWN_MAX = int(os.getenv("AUTH_COOLDOWN_MAX", 86400))
AUTH_COOLDOWN_MAX_RETRIES = int(os.getenv("AUTH_COOLDOWN_MAX_RETRIES", 0))

AUTH_EXCEPTIONS = (
    AuthorizationError,
    AuthorizationFailedError,
    CSRFError,
    MarketingConsentError,
    TermsAndConditionsError,
    TokenExpiredError,
)


async def fetch_state(myskoda: MySkoda, vin: str) -> dict:
    charging = await myskoda.get_charging(vin)
    status = charging.status
    settings = charging.settings
    battery = status.battery if status else None

    data = {
        "charging_state": status.state.value if status and status.state else None,
        "charge_power_kw": status.charge_power_in_kw if status else None,
        "charge_type": status.charge_type.value if status and status.charge_type else None,
        "charging_rate_km_per_h": status.charging_rate_in_kilometers_per_hour if status else None,
        "remaining_charge_min": status.remaining_time_to_fully_charged_in_minutes if status else None,
        "battery_soc_pct": battery.state_of_charge_in_percent if battery else None,
        "remaining_range_km": (
            round(battery.remaining_cruising_range_in_meters / 1000)
            if battery and battery.remaining_cruising_range_in_meters
            else None
        ),
        "target_soc_pct": settings.target_state_of_charge_in_percent if settings else None,
        "max_charge_current": (
            settings.max_charge_current_ac.value
            if settings and settings.max_charge_current_ac
            else None
        ),
        "preferred_charge_mode": (
            settings.preferred_charge_mode.value
            if settings and settings.preferred_charge_mode
            else None
        ),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return {k: v for k, v in data.items() if v is not None}


async def handle_command(myskoda: MySkoda, vin: str, payload: str) -> None:
    try:
        cmd = json.loads(payload)
    except json.JSONDecodeError:
        logger.warning("Invalid command JSON: %s", payload)
        return

    action = cmd.get("action")
    if action == "start_charging":
        await myskoda.start_charging(vin)
        logger.info("Started charging")
    elif action == "stop_charging":
        await myskoda.stop_charging(vin)
        logger.info("Stopped charging")
    elif action == "set_charge_limit":
        limit = cmd.get("value")
        if isinstance(limit, int) and 50 <= limit <= 100:
            await myskoda.set_charge_limit(vin, limit)
            logger.info("Set charge limit to %d%%", limit)
        else:
            logger.warning("Invalid charge limit: %s (must be int 50–100)", limit)
    else:
        logger.warning("Unknown command action: %s", action)


async def publish_status(mqtt: aiomqtt.Client, state: str, **fields) -> None:
    payload = {"state": state, "last_updated": datetime.now(timezone.utc).isoformat(), **fields}
    await mqtt.publish(TOPIC_STATUS, json.dumps(payload), retain=True)


async def polling_loop(myskoda: MySkoda, mqtt: aiomqtt.Client) -> None:
    while True:
        try:
            state = await fetch_state(myskoda, VIN)
            await mqtt.publish(TOPIC_STATE, json.dumps(state), retain=True)
            logger.info(
                "Published: soc=%s%% state=%s power=%skW",
                state.get("battery_soc_pct"),
                state.get("charging_state"),
                state.get("charge_power_kw"),
            )
        except AUTH_EXCEPTIONS:
            raise
        except Exception:
            logger.exception("Error in polling loop")
        await asyncio.sleep(POLL_INTERVAL)


async def command_loop(myskoda: MySkoda, mqtt: aiomqtt.Client) -> None:
    await mqtt.subscribe(TOPIC_COMMAND)
    async for message in mqtt.messages:
        payload = message.payload.decode()
        logger.info("Received command: %s", payload)
        try:
            await handle_command(myskoda, VIN, payload)
        except AUTH_EXCEPTIONS:
            raise
        except Exception:
            logger.exception("Error handling command")


async def run() -> None:
    if not all([USERNAME, PASSWORD, VIN]):
        logger.error("MYSKODA_USERNAME, MYSKODA_PASSWORD and MYSKODA_VIN are required")
        return

    mqtt_kwargs: dict = {"hostname": MQTT_HOST, "port": MQTT_PORT}
    if MQTT_USER:
        mqtt_kwargs["username"] = MQTT_USER
    if MQTT_PASS:
        mqtt_kwargs["password"] = MQTT_PASS

    async with aiomqtt.Client(**mqtt_kwargs) as mqtt:
        logger.info("Connected to MQTT at %s:%d", MQTT_HOST, MQTT_PORT)
        auth_failures = 0
        cooldown_failures = 0

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    myskoda = MySkoda(session)
                    logger.info("Authenticating with mySkoda API...")
                    await myskoda.connect(USERNAME, PASSWORD)
                    logger.info("Authenticated. VIN: %s", VIN)
                    auth_failures = 0
                    cooldown_failures = 0
                    await publish_status(mqtt, "ok")
                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(polling_loop(myskoda, mqtt))
                        tg.create_task(command_loop(myskoda, mqtt))
            except* AUTH_EXCEPTIONS as eg:
                for exc in eg.exceptions:
                    logger.error("Auth failure (%s): %s", type(exc).__name__, exc)

                if auth_failures < AUTH_MAX_RETRIES:
                    auth_failures += 1
                    delay = min(AUTH_BACKOFF_BASE * 2 ** (auth_failures - 1), BACKOFF_CAP)
                    logger.warning(
                        "Fast-tier auth retry %d/%d in %ds",
                        auth_failures,
                        AUTH_MAX_RETRIES,
                        delay,
                    )
                    await publish_status(mqtt, "auth_retry", attempt=auth_failures, next_retry_in_s=delay)
                    await asyncio.sleep(delay)
                else:
                    cooldown_failures += 1
                    if AUTH_COOLDOWN_MAX_RETRIES > 0 and cooldown_failures >= AUTH_COOLDOWN_MAX_RETRIES:
                        logger.error(
                            "Permanent auth stop after %d cooldown failures — manual restart required",
                            cooldown_failures,
                        )
                        await publish_status(mqtt, "auth_error", cooldown_attempt=cooldown_failures, final=True)
                        await asyncio.Event().wait()  # block forever; never exit (avoids Docker restart resetting counters)
                    delay = min(AUTH_COOLDOWN_BASE * 2 ** (cooldown_failures - 1), AUTH_COOLDOWN_MAX)
                    logger.warning(
                        "Cooldown-tier auth retry %d in %ds",
                        cooldown_failures,
                        delay,
                    )
                    await publish_status(
                        mqtt, "auth_error", cooldown_attempt=cooldown_failures, next_retry_in_s=delay
                    )
                    await asyncio.sleep(delay)


async def main() -> None:
    backoff = 10
    while True:
        try:
            await run()
        except* Exception as eg:
            for exc in eg.exceptions:
                logger.error("Fatal error (%s), restarting in %ds", exc, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_CAP)
        else:
            backoff = 10


if __name__ == "__main__":
    asyncio.run(main())
