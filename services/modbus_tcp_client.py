import socket
import struct
import time

from services.modbus_base import ModbusClientBase


class ModbusTCPClient(ModbusClientBase):
    """
    Modbus TCP (port 502) transport. All FC01/03/05/06 request/response
    logic lives in ModbusClientBase - this class only knows how to open
    a socket and frame a PDU inside an MBAP header.
    """

    def __init__(self, host="192.168.1.50", port=502, unit_id=1, timeout=1.5):
        super().__init__(unit_id=unit_id, timeout=timeout)
        self.host = host
        self.port = port

        self.sock = None
        self._tx_id = 1

    def connect(self) -> bool:
        try:
            self.close()

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            return True

        except Exception:
            self.sock = None
            return False

    def close(self):
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
        self.sock = None

    def _ensure(self) -> bool:
        return self.sock is not None or self.connect()

    def _next_tid(self) -> int:
        self._tx_id = (self._tx_id + 1) & 0xFFFF
        if self._tx_id == 0:
            self._tx_id = 1
        return self._tx_id

    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray()
        t0 = time.time()
        while len(buf) < n and (time.time() - t0) < self.timeout:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                break
            buf += chunk
        return bytes(buf)

    def _transact(self, pdu: bytes):
        """
        MBAP: TID(2) PID(2)=0 LEN(2)=unit_id+pdu LEN UID(1), then the PDU.
        """
        tid = self._next_tid()
        length = 1 + len(pdu)
        mbap = struct.pack(">HHHB", tid, 0, length, self.unit_id)

        self.sock.sendall(mbap + pdu)

        # Response MBAP header is 7 bytes
        hdr = self._recv_exact(7)
        if len(hdr) != 7:
            return None, "short mbap"

        r_tid, r_pid, r_len, r_uid = struct.unpack(">HHHB", hdr)
        if r_tid != tid:
            return None, "tid mismatch"
        if r_pid != 0:
            return None, "pid mismatch"
        if r_uid != self.unit_id:
            return None, "unit mismatch"

        # Remaining bytes in ADU = r_len - 1 (unit already consumed)
        rest_len = r_len - 1
        rest = self._recv_exact(rest_len)
        if len(rest) != rest_len:
            return None, f"short pdu {len(rest)}/{rest_len}"

        return rest, None
