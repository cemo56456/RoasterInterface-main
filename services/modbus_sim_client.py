import random
import time

from services.modbus_base import ModbusClientBase


class ModbusSimClient(ModbusClientBase):
    """
    PLC yerine geçen sahte Modbus istemcisi (ağ yok, anında cevap verir).
    ModbusTCPClient ile aynı arayüze sahip: connect/close/read_holding_n/
    read_coils/write_single_register/write_single_coil.

    Register haritası ekranların okuduğu adreslerle uyumludur:
      MW2020..2025  canlı değerler (SET, BEAN, EXH temp, exhaust raw, burner, airflow)
      MW2026..2046  zaman/faz/ROR/banner/mod bilgileri
      MW3000..3016  manuel kontrol durum bloğu
    Coil 500 = kavurma başlat/durdur (MW2038'e yansır), coil 501 -> MW2040.
    Yazılan register'lar saklanır, böylece set/yüzde değişiklikleri ekrana döner.
    """

    DROP_SEC = 840          # kavurma bu süreden sonra otomatik biter (drop out)
    CHARGE_TEMP = 170.0     # bean sıcaklığı başlangıcı (°C)
    TURNING_TEMP = 85.0     # turning point sıcaklığı (°C)
    TURNING_SEC = 60
    TARGET_TEMP = 215.0
    TAU = 240.0
    FIRST_CRACK = 196.0
    DRY_END = 150.0

    def __init__(self, unit_id=1, timeout=1.5, **_ignored):
        super().__init__(unit_id=unit_id, timeout=timeout)
        self.regs = {}
        self.coils = {}
        self._connected = False

        self._running = False
        self._t0 = 0.0
        self._elapsed = 0.0
        self._last_bt = 25.0
        self._fc_sec = None
        self._dry_sec = None
        self._drop = False

        # varsayılan ayarlar
        self.regs[240] = 2150   # SET x10
        self.regs[20] = 250     # exhaust raw (0..500) -> %50
        self.regs[30] = 60      # burner %
        self.regs[200] = 500    # drum raw (x10) -> %50
        self.regs[615] = 0
        self.regs[2260] = 60
        self.regs[2261] = 10
        self.regs[2262] = 5

    # ------------------------------------------------------------
    # Transport (sahte)
    # ------------------------------------------------------------
    def connect(self) -> bool:
        self._connected = True
        return True

    def close(self):
        self._connected = False

    def _ensure(self) -> bool:
        self._connected = True
        return True

    def _transact(self, pdu: bytes):
        raise NotImplementedError("simulation does not use PDU framing")

    # ------------------------------------------------------------
    # Public API (ModbusClientBase'i atlar, belleğe okur/yazar)
    # ------------------------------------------------------------
    def read_holding_n(self, start_reg: int, qty: int):
        if qty <= 0 or qty > 125:
            return None, "qty out of range"
        with self.lock:
            self._tick()
            return [self._get(start_reg + i) for i in range(qty)], None

    def read_coils(self, start_coil: int, qty: int):
        if qty <= 0 or qty > 2000:
            return None, "qty out of range"
        with self.lock:
            return [1 if self.coils.get(start_coil + i) else 0 for i in range(qty)], None

    def write_single_register(self, reg: int, value: int):
        with self.lock:
            self.regs[int(reg)] = int(value) & 0xFFFF
            return True, None

    def write_single_coil(self, coil_addr: int, value: bool):
        with self.lock:
            addr = int(coil_addr)
            self.coils[addr] = bool(value)
            if addr == 500:
                if value:
                    self._start_roast()
                else:
                    self._stop_roast(reset=True)
            return True, None

    # ------------------------------------------------------------
    # Simülasyon
    # ------------------------------------------------------------
    def _start_roast(self):
        self._running = True
        self._drop = False
        self._t0 = time.time()
        self._elapsed = 0.0
        self._fc_sec = None
        self._dry_sec = None

    def _stop_roast(self, reset=False):
        self._running = False
        if reset:
            self._elapsed = 0.0
            self._fc_sec = None
            self._dry_sec = None
            self._drop = False

    def _bean_temp(self, t: float) -> float:
        if not self._running and not self._drop:
            return 25.0
        if t < self.TURNING_SEC:
            k = t / self.TURNING_SEC
            return self.CHARGE_TEMP - (self.CHARGE_TEMP - self.TURNING_TEMP) * k
        return self.TARGET_TEMP - (self.TARGET_TEMP - self.TURNING_TEMP) * \
            pow(2.718281828, -(t - self.TURNING_SEC) / self.TAU)

    def _tick(self):
        if self._running:
            self._elapsed = time.time() - self._t0
            if self._elapsed >= self.DROP_SEC:
                self._running = False
                self._drop = True
                self.coils[500] = False

        bt = self._bean_temp(self._elapsed)
        self._last_bt = bt

        if self._running or self._drop:
            if self._dry_sec is None and bt >= self.DRY_END:
                self._dry_sec = self._elapsed
            if self._fc_sec is None and bt >= self.FIRST_CRACK:
                self._fc_sec = self._elapsed

    def _banner(self) -> int:
        if self._drop:
            return 9
        if not self._running:
            return 0
        t = self._elapsed
        if t < self.TURNING_SEC:
            return 2 if t < 10 else 3
        if t < self.TURNING_SEC + 10:
            return 4
        if self._fc_sec is not None:
            return 5 if (t - self._fc_sec) < 20 else 6
        return 1

    @staticmethod
    def _mmss(sec: float):
        sec = max(0, int(sec))
        return sec // 60, sec % 60

    def _get(self, reg: int) -> int:
        # Canlı blok
        if 2020 <= reg <= 2046:
            return self._live_reg(reg)
        # Manuel kontrol blok
        if 3000 <= reg <= 3016:
            return self._manual_reg(reg)
        return self.regs.get(reg, 0)

    def _live_reg(self, reg: int) -> int:
        bt = self._last_bt
        active = self._running or self._drop
        t = self._elapsed
        noise = random.uniform(-0.2, 0.2) if active else 0.0

        if reg == 2020:
            return self.regs.get(240, 0)
        if reg == 2021:
            return int(round((bt + noise) * 10))
        if reg == 2022:
            return int(round((bt + (35.0 if active else 0.0) + noise) * 10))
        if reg == 2023:
            return self.regs.get(20, 0)
        if reg == 2024:
            return self.regs.get(30, 0) if self._running else 0
        if reg == 2025:
            return int(60 + self.regs.get(20, 0) * 0.3) if active else 0

        if reg in (2026, 2027):
            m, s = self._mmss(t)
            return m if reg == 2026 else s

        # Faz süreleri
        dry_end = self._dry_sec if self._dry_sec is not None else t
        fc = self._fc_sec if self._fc_sec is not None else None
        mil_end = fc if fc is not None else t
        dry_t = min(t, dry_end)
        mil_t = max(0.0, mil_end - dry_end) if active else 0.0
        dev_t = max(0.0, t - fc) if fc is not None else 0.0
        total = max(1.0, dry_t + mil_t + dev_t)

        if reg in (2028, 2029):
            m, s = self._mmss(dry_t)
            return m if reg == 2028 else s
        if reg == 2030:
            return int(round(100 * dry_t / total)) if active else 0
        if reg in (2031, 2032):
            m, s = self._mmss(mil_t)
            return m if reg == 2031 else s
        if reg == 2033:
            return int(round(100 * mil_t / total)) if active else 0
        if reg in (2034, 2035):
            m, s = self._mmss(dev_t)
            return m if reg == 2034 else s
        if reg == 2036:
            return int(round(100 * dev_t / total)) if active else 0

        if reg == 2037:   # ROR x10 (°C/dk)
            if not self._running or t < self.TURNING_SEC:
                return 0
            ror = (self.TARGET_TEMP - bt) / self.TAU * 60.0
            return int(round(ror * 10))
        if reg == 2038:
            return 1 if self.coils.get(500) else 0
        if reg == 2039:
            return self._banner()
        if reg == 2040:
            return 1 if self.coils.get(501) else 0
        if reg == 2041:   # ROR MAX x10
            return int(round((self.TARGET_TEMP - self.TURNING_TEMP) / self.TAU * 60.0 * 10))
        if reg == 2042:   # C/sn x10, 999 = yok
            if not self._running or t < self.TURNING_SEC:
                return 999
            return int(round((self.TARGET_TEMP - bt) / self.TAU * 10))
        if reg == 2043:
            return self.regs.get(615, 0)
        if reg == 2044:
            return self.regs.get(2044, 0)
        if reg == 2045:
            return self.regs.get(2045, 0)
        if reg == 2046:
            return self.regs.get(2046, 0)
        return 0

    def _manual_reg(self, reg: int) -> int:
        bt = self._last_bt
        active = self._running or self._drop
        r = reg - 3000
        if r == 0:   # drum
            return 1 if self._running else 0
        if r == 1:   # burner
            return 1 if self._running else 0
        if r == 2:   # mixer
            return 1 if self.coils.get(502) else 0
        if r == 3:   # cooler
            return 1 if self._drop else 0
        if r == 4:   # cooling
            return self.regs.get(2201, 0)
        if r == 5:
            return self.regs.get(20, 0)
        if r == 6:
            return self.regs.get(30, 0)
        if r == 7:
            return self.regs.get(200, 0)
        if r == 8:
            return self.regs.get(240, 0)
        if r == 9:
            return int(round(bt * 10))
        if r == 10:
            return int(round((bt + (35.0 if active else 0.0)) * 10))
        if r == 11:
            return self.regs.get(2260, 0)
        if r == 12:
            return self.regs.get(2261, 0)
        if r == 13:
            return self.regs.get(2262, 0)
        if r == 14:
            return self.regs.get(2263, 0)
        return 0
