import asyncio
import logging
import os
import random
import sys
import tcdicn

async def main():
    name = os.getenv("TCDICN_ID", "water_quality_sensor")
    port = int(os.getenv("TCDICN_PORT", 33350))  # 更新端口为 :33350
    dport = int(os.getenv("TCDICN_DPORT", port))
    ttl = int(os.getenv("TCDICN_TTL", 30))
    tpf = int(os.getenv("TCDICN_TPF", 3))
    ttp = float(os.getenv("TCDICN_TTP", 5))

    if name is None:
        sys.exit("Please give your sensor a unique ID by setting TCDICN_ID")

    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        level=verbs["info"], datefmt="%H:%M:%S")

    label = "dissolved_oxygen"  # 溶解氧水平的标签

    client = {"name": name, "ttp": ttp, "labels": [label]}
    node = tcdicn.Node()
    node_task = asyncio.create_task(node.start(port, dport, ttl, tpf, client))

    async def run_sensor():
        while True:
            await asyncio.sleep(random.uniform(10, 30))
            value = random.uniform(5.0, 14.0)  # 生成溶解氧水平的随机数据
            logging.info(f"Publishing {label} = {value}...")
            try:
                await node.set(label, value)
            except OSError as exc:
                logging.error(f"Failed to publish: {exc}")

    sensor_task = asyncio.create_task(run_sensor())

    logging.info("Starting water quality sensor...")
    tasks = [node_task, sensor_task]
    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    logging.info("Water quality sensor done.")

if __name__ == "__main__":
    asyncio.run(main())
