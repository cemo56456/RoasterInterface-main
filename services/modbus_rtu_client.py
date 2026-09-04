import struct
import time

import serial
from serial.serialutil import SerialException

from services.modbus_base import ModbusClientBase


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def append_crc(frame: bytes) -> bytes:
    c = crc16_modbus(frame)
    return frame + bytes([c & 0xFF, (c >> 8) & 0xFF])


class ModbusRTUClient(ModbusClientBase):
    """
    Modbus RTU (serial) transport. All FC01/03/05/06 request/response
    logic lives in ModbusClientBase - this class only knows how to talk
    to the serial port and frame a PDU with a slave address + CRC16.
    """

    def __init__(self, port="COM5", baud=9600, unit_id=2, timeout=1.5):
        super().__init__(unit_id=unit_id, timeout=timeout)
        self.port = port
        self.baud = baud
        self.ser = None

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(
                self.port, self.baud,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=self.timeout
            )
            time.sleep(0.08)
            return True
        except SerialException:
            self.ser = None
            return False

    def close(self):
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass
        self.ser = None

    def _ensure(self) -> bool:
        return (self.ser is not None and self.ser.is_open) or self.connect()

    def _read_exact(self, n: int) -> bytes:
        """Read until n bytes or until timeout budget is consumed."""
        if not self.ser:
            return b""
        buf = bytearray()
        t0 = time.time()
        while len(buf) < n and (time.time() - t0) < self.timeout:
            chunk = self.ser.read(n - len(buf))
            if chunk:
                buf += chunk
            else:
                time.sleep(0.01)
        return bytes(buf)

    def _transact(self, pdu: bytes):
        """
        RTU has no length-prefixed header, so the expected response size
        has to be derived from the request's function code/quantity
        before reading.
        """
        frame = append_crc(bytes([self.unit_id]) + pdu)

        fc = pdu[0]
        if fc in (0x01, 0x03):
            qty = struct.unpack(">H", pdu[3:5])[0]
            if fc == 0x03:
                expected_len = 3 + 2 * qty + 2  # addr,fc,bytecount,data...,crc
            else:
                bytecount = (qty + 7) // 8
                expected_len = 3 + bytecount + 2
        else:
            expected_len = 8  # FC05/06 echo: addr,fc,addr(2),value(2),crc

        try:
            self.ser.reset_input_buffer()
            self.ser.write(frame)
            time.sleep(0.01)
            resp = self._read_exact(expected_len)
        except SerialException as e:
            self.close()
            return None, f"serial: {e}"

        if len(resp) != expected_len:
            return None, f"short read {len(resp)}/{expected_len}"

        recv_crc = resp[-2] | (resp[-1] << 8)
        calc_crc = crc16_modbus(resp[:-2])
        if recv_crc != calc_crc:
            return None, "crc error"

        if resp[0] != self.unit_id:
            return None, "slave mismatch"

        return resp[1:-2], None
