# communication_modulator.py
import asyncio
import logging
import os
import sys
import tcdicn
import random

async def main():
    name = os.getenv("TCDICN_ID", "communication_modulator")
    port = int(os.getenv("TCDICN_PORT", 33350))
    dport = int(os.getenv("TCDICN_DPORT", port))
    ttl = float(os.getenv("TCDICN_TTL", 30))
    tpf = int(os.getenv("TCDICN_TPF", 3))
    ttp = float(os.getenv("TCDICN_TTP", 5))
    verb = os.getenv("TCDICN_VERBOSITY", "info")

    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        level=verbs[verb], datefmt="%H:%M:%S")

    label = "communication_status"  # 通信状态的标签

    node = tcdicn.Node()
    node_task = asyncio.create_task(node.start(port, dport, ttl, tpf, {"name": name, "ttp": ttp, "labels": [label]}))

    # 处理电磁场数据并调整通信模式
    async def adjust_communication_mode(emf_value):
        if emf_value > 50.0:
            # 调整到高干扰模式
            logging.info("High EMF detected, switching to high interference mode.")
            mode = "High Interference Mode"
        else:
            # 维持正常通信模式
            logging.info("Normal EMF levels, maintaining standard mode.")
            mode = "Standard Mode"

        # 发布通信模式状态
        try:
            await node.set(label, mode)
        except OSError as exc:
            logging.error(f"Failed to publish communication mode: {exc}")

    # 订阅电磁场数据
    async def subscribe_to_emf_data():
        while True:
            emf_reading = await node.get("emf_data", ttl, tpf, ttp)
            await adjust_communication_mode(float(emf_reading))

    subscription_task = asyncio.create_task(subscribe_to_emf_data())

    logging.info("Starting communication modulator...")
    await asyncio.wait([node_task, subscription_task], return_when=asyncio.FIRST_COMPLETED)
    logging.info("Communication modulator done.")

if __name__ == "__main__":
    asyncio.run(main())
