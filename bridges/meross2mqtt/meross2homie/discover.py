"""
meross_discover: Einmalige Erkennung der Meross-Geraete via Cloud-API.

Authentifiziert sich einmalig gegen die Meross Cloud, ermittelt UUID und
den globalen User-Key aller Geraete und schreibt das Ergebnis in config.yml.

Wird automatisch von entrypoint.sh aufgerufen wenn die 'devices:'-Sektion
in config.yml leer ist. Kann auch manuell ausgefuehrt werden:

    meross_discover [config-datei]
    docker compose run --rm meross2mqtt meross_discover
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger

CONFIG_PATH = Path("/config/config.yml")
API_BASE_URL = "https://iotx-eu.meross.com"


async def _discover(email: str, password: str) -> tuple[str, dict]:
    from meross_iot.http_api import MerossHttpClient

    logger.info(f"Verbinde mit Meross Cloud API ({API_BASE_URL})...")

    try:
        client = await MerossHttpClient.async_from_user_password(
            api_base_url=API_BASE_URL,
            email=email,
            password=password,
        )
    except Exception as e:
        logger.error(f"Cloud-Authentifizierung fehlgeschlagen: {e}")
        logger.error("Bitte MEROSS_EMAIL und MEROSS_PASSWORD in .env pruefen.")
        sys.exit(1)

    # Globalen User-Key aus den Cloud-Credentials lesen
    user_key = ""
    try:
        creds = client.cloud_credentials
        user_key = getattr(creds, "key", "") or getattr(creds, "user_key", "") or ""
        if user_key:
            logger.info("User-Key erfolgreich ermittelt.")
        else:
            logger.warning("User-Key konnte nicht ermittelt werden – meross_key bleibt leer.")
    except Exception as e:
        logger.warning(f"Konnte User-Key nicht lesen: {e}")

    # Geraete abrufen
    try:
        device_list = await client.async_list_devices()
    except Exception as e:
        logger.error(f"Geraete konnten nicht abgerufen werden: {e}")
        await client.async_logout()
        sys.exit(1)

    devices = {}
    logger.info(f"{len(device_list)} Geraet(e) gefunden:")
    for dev in device_list:
        uuid = getattr(dev, "uuid", None)
        if not uuid:
            continue
        name = getattr(dev, "dev_name", None) or uuid
        dtype = getattr(dev, "device_type", "unbekannt")
        localip = getattr(dev, "localip", "")
        location = f" @ {localip}" if localip else ""
        logger.info(f"  {uuid}: {name} ({dtype}){location}")
        devices[uuid] = {"pretty_name": name}

    try:
        await client.async_logout()
        logger.info("Von Meross Cloud abgemeldet.")
    except Exception:
        pass

    return user_key, devices


def main(argv: Optional[list] = None):
    """Einstiegspunkt fuer 'meross_discover' CLI-Befehl."""
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    if argv is None:
        argv = sys.argv[1:]

    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0

    # Config-Pfad aus Argument oder Standard
    config_path = Path(argv[0]) if argv else CONFIG_PATH

    email = os.environ.get("MEROSS_EMAIL", "").strip()
    password = os.environ.get("MEROSS_PASSWORD", "").strip()

    if not email or not password:
        logger.error(
            "MEROSS_EMAIL und MEROSS_PASSWORD muessen in .env gesetzt sein.\n"
            "Beispiel:\n"
            "  MEROSS_EMAIL=deine@email.de\n"
            "  MEROSS_PASSWORD=deinPasswort"
        )
        sys.exit(1)

    user_key, devices = asyncio.run(_discover(email, password))

    if not devices:
        logger.warning("Keine Geraete gefunden. Meross-Account und Credentials pruefen.")

    # Bestehende config.yml laden oder neu erstellen
    config: dict = {}
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

    # Globalen meross_key und Geraete setzen
    if user_key:
        config["meross_key"] = user_key
    config["devices"] = devices

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    logger.success(f"{len(devices)} Geraet(e) in {config_path} geschrieben.")
    logger.info("Discovery abgeschlossen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
