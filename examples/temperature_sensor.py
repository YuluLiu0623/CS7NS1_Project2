# temperature_sensor.py
import asyncio
import logging
import os
import random
import sys
import tcdicn

async def main():
    # Get parameters or defaults
    file = open("constants.txt", "r")
    id = file.readline().strip()
    key = open("key", "rb").read()

    port = int(os.environ.get("TCDICN_PORT", random.randint(33334, 65536)))
    server_host = os.environ.get("TCDICN_SERVER_HOST", "localhost")
    server_port = int(os.environ.get("TCDICN_SERVER_PORT", 33335))
    net_ttl = int(os.environ.get("TCDICN_NET_TTL", 180))
    net_tpf = int(os.environ.get("TCDICN_NET_TPF", 3))
    net_ttp = float(os.environ.get("TCDICN_NET_TTP", 0))

    # Logging verbosity
    logging.basicConfig(
        format="%(asctime)s.%(msecs)04d [%(levelname)s] %(message)s",
        level=logging.INFO, datefmt="%H:%M:%S:%m")

    # Start the client as a background task
    logging.info(f"Starting {id}_TEMP client...")
    client = tcdicn.Client(
        id + "_TEMP", port, [id + "_water_temperature"],
        server_host, server_port,
        net_ttl, net_tpf, net_ttp)

    label = id + "_water_temperature"  # 水温数据的标签

    async def run_sensor():
        while True:
            await asyncio.sleep(random.uniform(10, 30))
            temperature = random.uniform(0, 25)  # 模拟水温数据
            logging.info(f"Publishing {label} = {temperature}...")
            tempStr = tcdicn.encrypt(str(temperature), key)
            try:
                await client.set(label, tempStr)
            except OSError as exc:
                logging.error(f"Failed to publish: {exc}")

    sensor_task = asyncio.create_task(run_sensor())

    logging.info("Starting temperature sensor...")
    both_tasks = asyncio.gather(client.task, sensor_task)
    try:
        await both_tasks
    except asyncio.exceptions.CancelledError:
        logging.info("Temperature sensor client has shutdown.")

if __name__ == "__main__":
    asyncio.run(main())
