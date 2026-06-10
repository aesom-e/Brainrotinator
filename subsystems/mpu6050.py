import struct
import time
from typing import override, Tuple, Optional
from enum import Enum, auto
from dataclasses import dataclass
import smbus2
from command import Subsystem
import cleanup

@dataclass
class GyroReading:
    x: float # Degrees per second
    y: float
    z: float
    time: float # Seconds since epoch

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __repr__(self) -> str:
        return f"GyroReading(x={self.x:.2f}, y={self.y:.2f}, z={self.z:.2f})"

class Extreme(Enum):
    LeftExtreme = auto()
    RightExtreme = auto()

class MPU6050(Subsystem):
    _DEFAULT_ADDRESS: int = 0x68

    # Register map
    _REG_PWR_MGMT_1: int  = 0x6B
    _REG_GYRO_CONFIG: int = 0x1B
    _REG_GYRO_XOUT_H: int = 0x43 # 6 bytes: X_H X_L Y_H Y_L Z_H Z_L
    _REG_WHO_AM_I: int    = 0x75

    _SCALE  = {250: 131., 500: 65.5, 1000: 32.8, 2000: 16.4}
    _FS_SEL = {250: 0b00, 500: 0b01, 1000: 0b10, 2000: 0b11}

    def __init__(self,
                 i2c_bus: int = 1,
                 address: int = _DEFAULT_ADDRESS,
                 full_scale: int = 250) -> None:
        super().__init__()

        if full_scale not in self._SCALE:
            raise ValueError(f"full_scale must be one of {list(self._SCALE)}")

        self._bus: smbus2.SMBus = smbus2.SMBus(i2c_bus)
        self._addr: int = address
        self._scale: float = self._SCALE[full_scale]

        self._extremes: Tuple[Optional[Extreme], Optional[Extreme], Optional[Extreme]] = (None, None, None)

        self._init_device(full_scale)
        cleanup.register(self._close)

    @override
    def periodic(self) -> None:
        x, y, z = self.read()
        self._extremes = (
            self._get_extreme(x),
            self._get_extreme(y),
            self._get_extreme(z)
        )

    @staticmethod
    def _get_extreme(value: float) -> Optional[Extreme]:
        if value < -160.: return Extreme.LeftExtreme
        if value > 160.: return Extreme.RightExtreme
        return None

    def _init_device(self, full_scale: int) -> None:
        # Wake the device
        self._bus.write_byte_data(self._addr, self._REG_PWR_MGMT_1, 0x00)
        time.sleep(0.1)

        # Verify the device identity (0x68 and 0x70 are acceptable return values)
        who = self._bus.read_byte_data(self._addr, self._REG_WHO_AM_I)
        if who not in (0x68, 0x70):
            raise RuntimeError(
                f"Unexpected device identity: 0x{who:02X}"
            )

        # Set the full-scale range
        fs_sel = self._FS_SEL[full_scale]
        self._bus.write_byte_data(self._addr, self._REG_GYRO_CONFIG, fs_sel << 3)

        # Read back to verify
        actual = self._bus.read_byte_data(self._addr, self._REG_GYRO_CONFIG)
        if actual != fs_sel << 3:
            raise RuntimeError(f"GYRO_CONFIG write failed")

    def read(self) -> GyroReading:
        raw = self._bus.read_i2c_block_data(self._addr, self._REG_GYRO_XOUT_H, 6)
        x, y, z = struct.unpack(">hhh", bytes(raw))
        now = time.time()
        return GyroReading(
            x=x/self._scale,
            y=y/self._scale,
            z=z/self._scale,
            time=now
        )

    @property
    def extremes(self) -> Tuple[Optional[Extreme], Optional[Extreme], Optional[Extreme]]: return self._extremes

    def _close(self) -> None: self._bus.close()