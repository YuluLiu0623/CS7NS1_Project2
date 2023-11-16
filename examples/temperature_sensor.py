# temperature_sensor.py
import asyncio
import logging
import os
import random
import sys
import tcdicn

async def main():
    name = os.getenv("TCDICN_ID", "temperature_sensor")
    port = int(os.getenv("TCDICN_PORT", 33350))  # 设置为不同于默认的端口
    dport = int(os.getenv("TCDICN_DPORT", port))  # 使用与监听端口相同的端口
    ttl = float(os.getenv("TCDICN_TTL", 30))  # 生存时间 30s
    tpf = int(os.getenv("TCDICN_TPF", 3))  # 提醒频率
    ttp = float(os.getenv("TCDICN_TTP", 5))  # 重复广告的时间阈值

    if name is None:
        sys.exit("Please give your sensor a unique ID by setting TCDICN_ID")

    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        level=verbs["info"], datefmt="%H:%M:%S")

    label = "water_temperature"  # 用于发布温度数据的标签
    node = tcdicn.Node()
    node_task = asyncio.create_task(node.start(port, dport, ttl, tpf, {"name": name, "ttp": ttp, "labels": [label]}))

    async def run_sensor():
        while True:
            await asyncio.sleep(random.uniform(10, 30))
            temperature = random.uniform(0, 25)  # 模拟水温数据
            logging.info(f"Publishing {label} = {temperature}...")
            try:
                await node.set(label, str(temperature))
            except OSError as exc:
                logging.error(f"Failed to publish: {exc}")

    sensor_task = asyncio.create_task(run_sensor())

    logging.info("Starting temperature sensor...")
    await asyncio.wait([node_task, sensor_task], return_when=asyncio.FIRST_COMPLETED)
    logging.info("Temperature sensor done.")

if __name__ == "__main__":
    asyncio.run(main())
