from mt16.core.logging import get_logger
from mt16.core.types import ContentPacket
from mt16.core.policy import allow_publish

log = get_logger("mt16.runtime")

def run_packet(packet: ContentPacket, human_approved: bool):
    log.info(f"Running packet: {packet.topic}")
    if not allow_publish(packet.risk, human_approved):
        log.warning("Blocked by policy")
        return False

    log.info("Packet approved and executed")
    return True
