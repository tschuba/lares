#!/usr/bin/env python3
import os
import yaml
import logging
from pymodbus.client import ModbusTcpClient
from paho.mqtt import client as mqtt_client

# Configure logging
log_file = os.getenv('LOG_FILE', '/app/logs/sungrow2mqtt.log')
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

# Try to use file logging, fall back to console if directory doesn't exist
try:
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
except (OSError, IOError):
    # Fall back to console logging if file logging fails
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger('sungrow2mqtt')

def parse_config(config_path):
    """Parse configuration file"""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Set defaults if not provided
    config.setdefault('modbus', {})
    config.setdefault('mqtt', {})
    config.setdefault('logging', {})
    
    return config

def connect_mqtt(broker, port, client_id, username, password):
    """Establish MQTT connection"""
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    
    try:
        client.connect(broker, port)
        logger.info("Connected to MQTT broker")
        return client
    except Exception as e:
        logger.error(f"MQTT connection failed: {str(e)}")
        raise

def read_modbus_registers(host, port, unit_id, slave_id, function_code, register_count):
    """Read Modbus registers from Sungrow inverter"""
    client = ModbusTcpClient(host=host, port=port, timeout=5)
    
    try:
        client.connect()
        logger.info(f"Connected to Modbus device at {host}:{port}")
        
        # Read holding registers - pymodbus 3.x syntax
        result = client.read_holding_registers(
            address=slave_id,
            count=register_count
        )
        
        if result.isError():
            logger.error(f"Modbus error: {result}")
            return None
            
        return result.registers
        
    except Exception as e:
        logger.error(f"Modbus connection failed: {str(e)}")
        return None
    finally:
        client.close()

def parse_sungrow_data(registers):
    """Parse Modbus registers into energy metrics"""
    # Example parsing logic - adjust based on actual register layout
    try:
        # Assuming register layout based on typical Sungrow inverters
        voltage = registers[0] / 10.0  # 10-bit resolution
        current = (registers[2] * 65536 + registers[3]) / 1000.0  # 32-bit combined
        power = (registers[4] * 65536 + registers[5]) / 100.0  # 32-bit combined
        
        return {
            'voltage': voltage,
            'current': current,
            'power': power,
            'energy_today': registers[6] * 65536 + registers[7],
            'energy_total': registers[8] * 65536 + registers[9]
        }
    except Exception as e:
        logger.error(f"Data parsing error: {str(e)}")
        return None

def publish_to_mqtt(mqtt_client, topic_prefix, data):
    """Publish parsed data to MQTT topics"""
    for metric, value in data.items():
        topic = f"{topic_prefix}/{metric}"
        mqtt_client.publish(topic, str(value))
        logger.info(f"Published {metric}: {value} to {topic}")

def main():
    try:
        # Load configuration
        config = parse_config('/app/config.yaml')
        logger.info("Configuration loaded successfully")
        
        # Connect to MQTT broker
        mqtt_client = connect_mqtt(
            broker=config['mqtt']['broker'],
            port=config['mqtt']['port'],
            client_id=config['mqtt']['client_id'],
            username=config['mqtt']['username'],
            password=config['mqtt']['password']
        )
        
        # Read and parse Modbus data
        registers = read_modbus_registers(
            host=config['modbus']['host'],
            port=config['modbus']['port'],
            unit_id=config['modbus']['unit_id'],
            slave_id=config['modbus']['slave_id'],
            function_code=config['modbus']['function_code'],
            register_count=config['modbus']['register_count']
        )
        
        if registers:
            data = parse_sungrow_data(registers)
            if data:
                publish_to_mqtt(mqtt_client=mqtt_client, 
                              topic_prefix=config['mqtt']['topic_prefix'],
                              data=data)
                
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        raise
    finally:
        if 'mqtt_client' in locals():
            mqtt_client.disconnect()
            logger.info("MQTT connection closed")

if __name__ == "__main__":
    main()