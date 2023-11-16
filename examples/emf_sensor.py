# emf_sensor.py
import asyncio
import logging
import os
import random
import sys
import tcdicn

async def main():
    name = os.getenv("TCDICN_ID", "emf_sensor")
    port = int(os.getenv("TCDICN_PORT", 33350))
    dport = int(os.getenv("TCDICN_DPORT", port))
    ttl = int(os.getenv("TCDICN_TTL", 30))
    tpf = int(os.getenv("TCDICN_TPF", 3))
    ttp = float(os.getenv("TCDICN_TTP", 5))
    verb = os.getenv("TCDICN_VERBOSITY", "info")

    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        level=verbs[verb], datefmt="%H:%M:%S")

    label = "emf_data"  # 电磁场数据的标签

    node = tcdicn.Node()
    node_task = asyncio.create_task(node.start(port, dport, ttl, tpf, {"name": name, "ttp": ttp, "labels": [label]}))

    async def run_sensor():
        while True:
            await asyncio.sleep(random.uniform(10, 30))
            emf_reading = random.uniform(0.0, 100.0)  # 模拟电磁场强度
            logging.info(f"Publishing {label} = {emf_reading}...")
            try:
                await node.set(label, str(emf_reading))
            except OSError as exc:
                logging.error(f"Failed to publish: {exc}")

    sensor_task = asyncio.create_task(run_sensor())

    logging.info("Starting EMF sensor...")
    await asyncio.wait([node_task, sensor_task], return_when=asyncio.FIRST_COMPLETED)
    logging.info("EMF sensor done.")

if __name__ == "__main__":
    asyncio.run(main())
