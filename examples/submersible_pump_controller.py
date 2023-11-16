# actuator.py
import asyncio
import logging
import os
import sys

import tcdicn

async def main():
    name = os.getenv("TCDICN_ID", "submersible_pump_controller")
    port = int(os.getenv("TCDICN_PORT", 33350))  # 更新端口为 :33350
    dport = int(os.getenv("TCDICN_DPORT", port))
    ttl = float(os.getenv("TCDICN_TTL", 30))
    tpf = int(os.getenv("TCDICN_TPF", 3))
    ttp = float(os.getenv("TCDICN_TTP", 5))
    get_ttl = float(os.getenv("TCDICN_GET_TTL", 90))
    get_tpf = int(os.getenv("TCDICN_GET_TPF", 2))
    get_ttp = float(os.getenv("TCDICN_GET_TTP", 0.5))

    if name is None:
        sys.exit("Please give your actuator a unique ID by setting TCDICN_ID")

    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        level=verbs["info"], datefmt="%H:%M:%S")

    # 订阅 Barometer 传感器发布的标签
    labels = ["pressure", "depth"]

    client = {"name": name, "ttp": ttp, "labels": labels}
    node = tcdicn.Node()
    node_task = asyncio.create_task(node.start(port, dport, ttl, tpf, client))

    async def run_actuator():
        tasks = set()

        def subscribe(label):
            logging.info("Subscribing to %s...", label)
            getter = node.get(label, get_ttl, get_tpf, get_ttp)
            task = asyncio.create_task(getter, name=label)
            tasks.add(task)

        for label in labels:
            subscribe(label)

        while True:
            done, tasks = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                label = task.get_name()
                value = await task.result()
                logging.info("Received %s=%s", label, value)
                adjust_pump_settings(label, value)
                subscribe(label)

    def adjust_pump_settings(label, value):
        # 根据接收的数据调整潜水泵设置
        if label == "depth":
            # 示例逻辑：根据深度调整潜水泵
            if value > 10:
                logging.info("Adjusting pump settings for depth > 10")
            else:
                logging.info("Depth is normal, no adjustment needed")

    actuator_task = asyncio.create_task(run_actuator())

    logging.info("Starting submersible pump controller...")
    tasks = [node_task, actuator_task]
    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    actuator_task.cancel()
    logging.info("Submersible pump controller done.")

if __name__ == "__main__":
    asyncio.run(main())
