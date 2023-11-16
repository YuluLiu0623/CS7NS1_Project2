# lighting_controller.py
import asyncio
import logging
import os
import sys
import tcdicn
import random

async def main():
    # Read ID and key from files
    file = open("constants.txt", "r")
    id = file.readline().strip()
    key = open("key", "rb").read()

    # Configuration
    port = int(os.environ.get("TCDICN_PORT", random.randint(33334, 65536)))
    server_host = os.environ.get("TCDICN_SERVER_HOST", "localhost")
    server_port = int(os.environ.get("TCDICN_SERVER_PORT", 33335))
    net_ttl = int(os.environ.get("TCDICN_NET_TTL", 180))
    net_tpf = int(os.environ.get("TCDICN_NET_TPF", 3))
    net_ttp = float(os.environ.get("TCDICN_NET_TTP", 0))
    get_ttl = int(os.environ.get("TCDICN_GET_TTL", 180))
    get_tpf = int(os.environ.get("TCDICN_GET_TPF", 3))
    get_ttp = float(os.environ.get("TCDICN_GET_TTP", 0))

    if id is None:
        sys.exit("Please give your client a unique ID by setting TCDICN_ID")

    # Logging configuration
    logging.basicConfig(
        format="%(asctime)s.%(msecs)04d [%(levelname)s] %(message)s",
        level=logging.INFO, datefmt="%H:%M:%S:%m")

    # Start the client
    logging.info(f"Starting {id}_LIGHT client...")
    client = tcdicn.Client(
        id + "_LIGHT", port, [],
        server_host, server_port,
        net_ttl, net_tpf, net_ttp)

    # Current brightness initialization
    current_brightness = 50

    # Define a function to adjust lighting
    def adjust_lighting(temperature, brightness):
        if temperature < 10:
            logging.info("Low temperature detected, increasing lighting brightness.")
            return min(brightness + 10, 100)  # Increase brightness
        else:
            logging.info("Normal temperature, maintaining current lighting.")
            return max(brightness - 5, 0)  # Decrease brightness

    # Subscribe and process temperature data
    async def run_actuator():
        nonlocal current_brightness

        while True:
            temperature_reading = await client.get(id + "_water_temperature", get_ttl, get_tpf, get_ttp)
            temperature = float(tcdicn.decrypt(temperature_reading, key))
            logging.info(f"Received water_temperature = {temperature}")
            current_brightness = adjust_lighting(temperature, current_brightness)
            encrypted_brightness = tcdicn.encrypt(str(current_brightness), key)
            await client.set(f"{id}_lighting_brightness", encrypted_brightness)

    # Run the actuator logic as a coroutine
    actuator_task = asyncio.create_task(run_actuator())

    # Execute both tasks
    both_tasks = asyncio.gather(client.task, actuator_task)
    try:
        await both_tasks
    except asyncio.exceptions.CancelledError:
        logging.info("Lighting controller client has shutdown.")

if __name__ == "__main__":
    asyncio.run(main())
