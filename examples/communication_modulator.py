# communication_modulator.py
import asyncio
import logging
import os
import sys
import tcdicn
import random

async def main():
    # 读取配置和密钥
    file = open("constants.txt", "r")
    id = file.readline().strip()
    key = open("key", "rb").read()

    # 设置连接参数
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

    # 配置日志
    logging.basicConfig(
        format="%(asctime)s.%(msecs)04d [%(levelname)s] %(message)s",
        level=logging.INFO, datefmt="%H:%M:%S:%m")

    # 启动客户端
    logging.info("Starting client...")
    client = tcdicn.Client(
        id + "_MOD", port, [],
        server_host, server_port,
        net_ttl, net_tpf, net_ttp)

    # 根据电磁场值调整通信模式
    async def adjust_communication_mode(emf_value):
        logging.info(f"Adjusting communication mode for EMF value: {emf_value}")  # 新增日志
        if emf_value > 50.0:
            logging.info("High EMF detected, switching to high interference mode.")
            mode = "High Interference Mode"
        else:
            logging.info("Normal EMF levels, maintaining standard mode.")
            mode = "Standard Mode"

        encrypted_mode = tcdicn.encrypt(mode, key)
        try:
            client.set("communication_status", encrypted_mode)  # 移除 await
            logging.info(f"Published communication mode: {mode}")  # 新增日志
        except OSError as exc:
            logging.error(f"Failed to publish communication mode: {exc}")

    # 订阅电磁场数据
    async def run_actuator():
        tasks = {}

        def subscribe(tag):
            if tag not in tasks or tasks[tag].done():
                logging.info(f"Subscribing to {tag}...")
                getter = client.get(tag, get_ttl, get_tpf, get_ttp)
                task = asyncio.create_task(getter, name=tag)
                tasks[tag] = task

        subscribe(id + "_emf_data")

        while True:
            done, _ = await asyncio.wait(
                tasks.values(), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                tag = task.get_name()
                value = float(tcdicn.decrypt(task.result(), key))
                logging.info(f"Received {tag} = {value}")
                if tag == "emf_data":
                    await adjust_communication_mode(value)
                await asyncio.sleep(3)
                subscribe(tag)  # 重新订阅标签（如果任务完成）

    # 运行执行器任务
    actuator_task = asyncio.create_task(run_actuator())

    logging.info("Starting communication modulator...")
    await asyncio.wait([client.task, actuator_task], return_when=asyncio.FIRST_COMPLETED)
    logging.info("Communication modulator done.")

if __name__ == "__main__":
    asyncio.run(main())
