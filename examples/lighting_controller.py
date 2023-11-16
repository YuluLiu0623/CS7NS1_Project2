# lighting_controller.py
import asyncio
import logging
import os
import sys
import tcdicn

async def main():
    name = os.getenv("TCDICN_ID", "lighting_controller")
    port = int(os.getenv("TCDICN_PORT", 33350))
    dport = int(os.getenv("TCDICN_DPORT", port))
    ttl = float(os.getenv("TCDICN_TTL", 30))
    tpf = int(os.getenv("TCDICN_TPF", 3))
    ttp = float(os.getenv("TCDICN_TTP", 5))
    get_ttl = float(os.getenv("TCDICN_GET_TTL", 90))
    get_tpf = int(os.getenv("TCDICN_GET_TPF", 2))
    get_ttp = float(os.getenv("TCDICN_GET_TTP", 0.5))
    verb = os.getenv("TCDICN_VERBOSITY", "info")

    if name is None:
        sys.exit("Please give your actuator a unique ID by setting TCDICN_ID")

    # Logging verbosity
    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        level=verbs[verb], datefmt="%H:%M:%S")

    # 初始化 ICN 节点客户端，不发布任何标签
    client = {"name": name, "ttp": ttp, "labels": []}
    node = tcdicn.Node()
    node_task = asyncio.create_task(node.start(port, dport, ttl, tpf, client))

    # 假设初始亮度为 50%
    current_brightness = 50

    async def run_actuator():
        nonlocal current_brightness
        label = ["water_temperature"]
        tasks = set()

        def subscribe(label):
            logging.info(f"Subscribing to {label}...")
            getter = node.get(label, get_ttl, get_tpf, get_ttp)
            task = asyncio.create_task(getter, name=label)
            tasks.add(task)


        while True:
            done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                label = task.get_name()
                temperature = await task.result()
                logging.info(f"Received {label} = {temperature}")
                current_brightness = adjust_lighting(float(temperature), current_brightness)
                # 发布当前亮度数据
                await node.set("lighting_brightness", str(current_brightness))
                subscribe(label)

    def adjust_lighting(temperature, brightness):
        if temperature < 10:
            logging.info("Low temperature detected, increasing lighting brightness.")
            return min(brightness + 10, 100)  # 增加亮度，但不超过 100%
        else:
            logging.info("Normal temperature, maintaining current lighting.")
            return max(brightness - 5, 0)  # 降低亮度，但不低于 0%

    actuator_task = asyncio.create_task(run_actuator())

    logging.info("Starting lighting controller...")
    await asyncio.wait([node_task, actuator_task], return_when=asyncio.FIRST_COMPLETED)
    logging.info("Lighting controller done.")

if __name__ == "__main__":
    asyncio.run(main())
