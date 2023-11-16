# sonar_sensor.py
import asyncio
import logging
import os
import random
import sys
import tcdicn

async def main():
    name = os.getenv("TCDICN_ID", "sonar_sensor")
    port = int(os.getenv("TCDICN_PORT", 33350))
    dport = int(os.getenv("TCDICN_DPORT", port))
    ttl = int(os.getenv("TCDICN_TTL", 30))
    tpf = int(os.getenv("TCDICN_TPF", 3))
    ttp = float(os.getenv("TCDICN_TTP", 5))
    verb = os.getenv("TCDICN_VERBOSITY", "info")

    # 设置日志详细程度
    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        level=verbs[verb], datefmt="%H:%M:%S")

    label = "sonar_data"
    # 初始化 ICN 节点
    node = tcdicn.Node()
    node_task = asyncio.create_task(node.start(port, dport, ttl, tpf, {"name": name, "ttp": ttp, "labels": [label]}))

    # 定义用于处理接收到的数据的函数
    async def process_received_data(label, value):
        if label in ["xpos", "ypos"]:
            # 处理定位数据
            logging.info(f"Received positioning data: {label} = {value}")
            # 根据定位数据调整声纳测量策略
        elif label == "depth":
            # 处理深度数据
            logging.info(f"Received depth data: {value}")
            # 根据深度数据调整声纳测量策略

    # 定义声纳测量任务
    async def run_sensor():
        while True:
            await asyncio.sleep(random.uniform(10, 30))
            sonar_reading = random.uniform(0.0, 100.0)  # 模拟声纳读数
            logging.info(f"Publishing {label} = {sonar_reading}...")
            try:
                await node.set(label, str(sonar_reading))
            except OSError as exc:
                logging.error(f"Failed to publish: {exc}")

    # 定义订阅其他传感器数据的任务
    async def subscribe_to_data():
        for label in ["xpos", "ypos", "depth"]:
            while True:
                value = await node.get(label, ttl, tpf, ttp)
                await process_received_data(label, value)

    sensor_task = asyncio.create_task(run_sensor())
    subscription_task = asyncio.create_task(subscribe_to_data())

    logging.info("Starting sonar sensor with subscriptions...")
    await asyncio.wait([node_task, sensor_task, subscription_task], return_when=asyncio.FIRST_COMPLETED)
    logging.info("Sonar sensor done.")

if __name__ == "__main__":
    asyncio.run(main())
