# water_flow_sensor.py
import asyncio
import logging
import os
import random
import sys
import tcdicn

async def main():
    name = os.getenv("TCDICN_ID", "water_flow_sensor")
    port = int(os.getenv("TCDICN_PORT", 33350))
    dport = int(os.getenv("TCDICN_DPORT", port))
    ttl = int(os.getenv("TCDICN_TTL", 30))
    tpf = int(os.getenv("TCDICN_TPF", 3))
    ttp = float(os.getenv("TCDICN_TTP", 5))
    verb = os.getenv("TCDICN_VERBOSITY", "info")

    if name is None:
        sys.exit("Please give your sensor a unique ID by setting TCDICN_ID")

    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        level=verbs[verb], datefmt="%H:%M:%S")

    label = "water_flow"  # 发布水流速度数据的标签
    node = tcdicn.Node()
    node_task = asyncio.create_task(node.start(port, dport, ttl, tpf, {"name": name, "ttp": ttp, "labels": [label]}))

    async def run_sensor():
        while True:
            await asyncio.sleep(random.uniform(10, 30))
            water_flow = random.uniform(0.0, 5.0)  # 模拟水流速度数据
            logging.info(f"Publishing {label} = {water_flow} m/s...")
            try:
                await node.set(label, str(water_flow))
            except OSError as exc:
                logging.error(f"Failed to publish: {exc}")

    sensor_task = asyncio.create_task(run_sensor())

    logging.info("Starting water flow sensor...")
    await asyncio.wait([node_task, sensor_task], return_when=asyncio.FIRST_COMPLETED)
    logging.info("Water flow sensor done.")

if __name__ == "__main__":
    asyncio.run(main())