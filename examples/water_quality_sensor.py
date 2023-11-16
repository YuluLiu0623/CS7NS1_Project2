# water_quality_sensor.py
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
    logging.info(f"Starting {id}_WATER_QUALITY client...")
    client = tcdicn.Client(
        id + "_WATER_QUALITY", port, [id + "_dissolved_oxygen"],
        server_host, server_port,
        net_ttl, net_tpf, net_ttp)

    label = id + "_dissolved_oxygen"  # 溶解氧水平的标签

    async def run_sensor():
        while True:
            await asyncio.sleep(random.uniform(10, 30))
            value = random.uniform(5.0, 14.0)  # 生成溶解氧水平的随机数据
            logging.info(f"Publishing {label} = {value}...")
            oxygenStr = tcdicn.encrypt(str(value), key)
            try:
                await client.set(label, oxygenStr)
            except OSError as exc:
                logging.error(f"Failed to publish: {exc}")

    sensor_task = asyncio.create_task(run_sensor())

    logging.info("Starting water quality sensor...")
    both_tasks = asyncio.gather(client.task, sensor_task)
    try:
        await both_tasks
    except asyncio.exceptions.CancelledError:
        logging.info("Water quality sensor client has shutdown.")

if __name__ == "__main__":
    asyncio.run(main())