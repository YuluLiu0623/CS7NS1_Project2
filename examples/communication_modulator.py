# communication_modulator.py
import asyncio
import logging
import os
import sys
import tcdicn
import random

async def main():
    file = open("constants.txt", "r")
    id = file.readline().strip()
    key = open("key", "rb").read()

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

    logging.basicConfig(
        format="%(asctime)s.%(msecs)04d [%(levelname)s] %(message)s",
        level=logging.INFO, datefmt="%H:%M:%S:%m")

    logging.info("Starting client...")
    client = tcdicn.Client(
        id + "_MOD", port, [],
        server_host, server_port,
        net_ttl, net_tpf, net_ttp)

    async def adjust_communication_mode(emf_value):
        if emf_value > 50.0:
            logging.info("High EMF detected, switching to high interference mode.")
            mode = "High Interference Mode"
        else:
            logging.info("Normal EMF levels, maintaining standard mode.")
            mode = "Standard Mode"
        encrypted_mode = tcdicn.encrypt(mode, key)
        try:
            await client.set("communication_status", encrypted_mode)
        except OSError as exc:
            logging.error(f"Failed to publish communication mode: {exc}")



    async def run_actuator():
        tasks = set()

        def subscribe(tag):
            getter = client.get(tag, get_ttl, get_tpf, get_ttp)
            task = asyncio.create_task(getter, name=tag)
            tasks.add(task)

        logging.info("Subscribing to emf_data...")
        subscribe(id + "_emf_data")

        while True:
            done, _ = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                tag = task.get_name()
                value = float(tcdicn.decrypt(task.result(), key))
                logging.info(f"Received {tag} = {value}")
                if tag == "emf_data":
                    await adjust_communication_mode(value)
                logging.info(f"Resubscribing to {tag}...")
                subscribe(tag)
            await asyncio.sleep(5)

    actuator_task = asyncio.create_task(run_actuator())

    logging.info("Starting communication modulator...")
    await asyncio.wait([client.task, actuator_task], return_when=asyncio.FIRST_COMPLETED)
    logging.info("Communication modulator done.")

if __name__ == "__main__":
    asyncio.run(main())
