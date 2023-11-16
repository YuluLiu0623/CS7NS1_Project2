# submersible_pump_controller.py
import asyncio
import logging
import os
import sys
import tcdicn
import random

async def main():
    # Get parameters or defaults
    file = open("constants.txt", "r")
    id = file.readline().strip()
    key = open("key", "rb").read()

    name = os.getenv("TCDICN_ID", "submersible_pump_controller")
    port = int(os.environ.get("TCDICN_PORT", random.randint(33334, 65536)))
    server_host = os.environ.get("TCDICN_SERVER_HOST", "localhost")
    server_port = int(os.environ.get("TCDICN_SERVER_PORT", 33335))
    net_ttl = int(os.environ.get("TCDICN_NET_TTL", 180))
    net_tpf = int(os.environ.get("TCDICN_NET_TPF", 3))
    net_ttp = float(os.environ.get("TCDICN_NET_TTP", 0))
    get_ttl = int(os.environ.get("TCDICN_GET_TTL", 180))
    get_tpf = int(os.environ.get("TCDICN_GET_TPF", 3))
    get_ttp = float(os.environ.get("TCDICN_GET_TTP", 0))

    if name is None:
        sys.exit("Please give your actuator a unique ID by setting TCDICN_ID")

    # Logging verbosity
    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)04d [%(levelname)s] %(message)s",
        level=verbs["info"], datefmt="%H:%M:%S")

    # Start the client as a background task
    logging.info(f"Starting {id}_PUMP client...")
    client = tcdicn.Client(
        id + "_PUMP", port, [],
        server_host, server_port,
        net_ttl, net_tpf, net_ttp)

    # Define the subscription and actuator logic
    async def run_actuator():
        tasks = set()

        def subscribe(tag):
            logging.info(f"Subscribing to {tag}...")
            getter = client.get(tag, get_ttl, get_tpf, get_ttp)
            task = asyncio.create_task(getter, name=tag)
            tasks.add(task)

        subscribe(f"{id}_depth")  # Subscribe to the depth data

        while True:
            done, tasks = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                tag = task.get_name()
                value = float(tcdicn.decrypt(task.result(), key))
                logging.info(f"Received {tag} = {value}")
                # Logic to adjust pump settings based on depth
                if tag == f"{id}_depth":
                    if value > 10:
                        logging.info("Depth > 10, adjusting pump settings")
                    else:
                        logging.info("Depth within normal range")
                subscribe(tag)

    # Run the actuator logic as a coroutine
    actuator_task = run_actuator()

    # Wait for the client to shutdown while executing the actuator logic
    both_tasks = asyncio.gather(client.task, actuator_task)
    try:
        await both_tasks
    except asyncio.exceptions.CancelledError:
        logging.info("Submersible pump controller client has shutdown.")

if __name__ == "__main__":
    asyncio.run(main())
