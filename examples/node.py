import asyncio
import logging
import os
import tcdicn

async def main():
    # 获取环境变量或默认值
    port = int(os.getenv("TCDICN_PORT", 33350))  # 更新监听端口为 :33350
    dport = int(os.getenv("TCDICN_DPORT", port))  # 通信端口与监听端口相同
    ttl = int(os.getenv("TCDICN_TTL", 30))  # 生存时间 30s
    tpf = int(os.getenv("TCDICN_TPF", 3))  # 提醒频率
    verb = os.getenv("TCDICN_VERBOSITY", "info")  # 日志详细程度

    # 配置日志详细程度
    verbs = {"dbug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN}
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        level=verbs[verb], datefmt="%H:%M:%S")

    # 启动 ICN 节点直到关闭
    logging.info("Starting node...")
    await tcdicn.Node().start(port, dport, ttl, tpf)
    logging.info("Done.")

if __name__ == "__main__":
    asyncio.run(main())