import struct
import threading


class ModbusClientBase:
    """
    Transport-agnostic Modbus request/response logic (FC01/03/05/06).
    Subclasses implement the transport: connect(), close(), _ensure(),
    and _transact(pdu) -> (response_pdu, err), where response_pdu is
    the function-code byte plus payload, with addressing/framing/CRC
    already stripped and validated by the subclass.

    Add or fix a Modbus operation here once and every transport (TCP,
    RTU, ...) gets it for free.
    """

    def __init__(self, unit_id: int = 1, timeout: float = 1.5):
        self.unit_id = unit_id
        self.timeout = timeout
        self.lock = threading.Lock()

    # ---------------------------------------------------------
    # Transport hooks - subclasses must implement these
    # ---------------------------------------------------------
    def connect(self) -> bool:
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def _ensure(self) -> bool:
        raise NotImplementedError

    def _transact(self, pdu: bytes):
        raise NotImplementedError

    # ---------------------------------------------------------
    # Shared protocol-level operations
    # ---------------------------------------------------------
    def read_holding_n(self, start_reg: int, qty: int):
        if qty <= 0 or qty > 125:
            return None, "qty out of range"

        with self.lock:
            if not self._ensure():
                return None, "connect failed"

            pdu = struct.pack(">BHH", 0x03, start_reg, qty)
            try:
                rpdu, err = self._transact(pdu)
            except Exception as e:
                self.close()
                return None, f"transport: {e}"

            if rpdu is None:
                return None, err

            fc = rpdu[0]
            if fc & 0x80:
                ex = rpdu[1] if len(rpdu) > 1 else 0
                return None, f"exception 0x{ex:02X}"
            if fc != 0x03:
                return None, "bad response"
            if len(rpdu) < 2:
                return None, "short response"

            bytecount = rpdu[1]
            if bytecount != 2 * qty:
                return None, "bytecount mismatch"

            data = rpdu[2:2 + bytecount]
            if len(data) != bytecount:
                return None, "short data"

            return self._decode_registers(data, qty), None

    def read_coils(self, start_coil: int, qty: int):
        if qty <= 0 or qty > 2000:
            return None, "qty out of range"

        with self.lock:
            if not self._ensure():
                return None, "connect failed"

            pdu = struct.pack(">BHH", 0x01, start_coil, qty)
            try:
                rpdu, err = self._transact(pdu)
            except Exception as e:
                self.close()
                return None, f"transport: {e}"

            if rpdu is None:
                return None, err

            fc = rpdu[0]
            if fc & 0x80:
                ex = rpdu[1] if len(rpdu) > 1 else 0
                return None, f"exception 0x{ex:02X}"
            if fc != 0x01:
                return None, "bad response"
            if len(rpdu) < 2:
                return None, "short response"

            bytecount = rpdu[1]
            data = rpdu[2:2 + bytecount]
            if len(data) != bytecount:
                return None, "short data"

            return self._decode_coils(data, qty), None

    def write_single_register(self, reg: int, value: int):
        value &= 0xFFFF

        with self.lock:
            if not self._ensure():
                return False, "connect failed"

            pdu = struct.pack(">BHH", 0x06, reg, value)
            try:
                rpdu, err = self._transact(pdu)
            except Exception as e:
                self.close()
                return False, f"transport: {e}"

            if rpdu is None:
                return False, err

            fc = rpdu[0]
            if fc & 0x80:
                ex = rpdu[1] if len(rpdu) > 1 else 0
                return False, f"exception 0x{ex:02X}"
            if fc != 0x06:
                return False, "bad response"
            if len(rpdu) < 5:
                return False, "short response"

            return True, None

    def write_single_coil(self, coil_addr: int, value: bool):
        with self.lock:
            if not self._ensure():
                return False, "connect failed"

            val = 0xFF00 if bool(value) else 0x0000
            pdu = struct.pack(">BHH", 0x05, int(coil_addr) & 0xFFFF, val)
            try:
                rpdu, err = self._transact(pdu)
            except Exception as e:
                self.close()
                return False, f"transport: {e}"

            if rpdu is None:
                return False, err

            fc = rpdu[0]
            if fc & 0x80:
                ex = rpdu[1] if len(rpdu) > 1 else 0
                return False, f"exception 0x{ex:02X}"
            if fc != 0x05:
                return False, "bad response"
            if len(rpdu) < 5:
                return False, "short response"

            return True, None

    # ---------------------------------------------------------
    # Payload decoding
    # ---------------------------------------------------------
    @staticmethod
    def _decode_registers(data: bytes, qty: int):
        values = []
        for i in range(qty):
            hi = data[2 * i]
            lo = data[2 * i + 1]
            values.append((hi << 8) | lo)
        return values

    @staticmethod
    def _decode_coils(data: bytes, qty: int):
        coils = []
        for i in range(qty):
            byte_i = i // 8
            bit_i = i % 8
            coils.append((data[byte_i] >> bit_i) & 0x01)
        return coils
