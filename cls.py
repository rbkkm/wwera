from dataclasses import dataclass
from hilbertcurve.hilbertcurve import HilbertCurve
from typing import Optional, ClassVar


@dataclass
class Elevation:

    a: Optional[float] = None
    o: Optional[float] = None
    f: Optional[object] = None

    def get_ele(self) -> float:

        coords = [(self.o, self.a)]

        for val in self.f.sample(coords):
            ele = None
            if -500 < val[0] < 8888:
                ele = val[0]

        return ele


@dataclass
class Location:

    FE: ClassVar[int] = 1e9  # * factor e9 1_000_000_000
    x: Optional[int] = None
    y: Optional[int] = None

    def get_hc(self) -> int:
        p = 128
        n = 2
        hilbert_curve = HilbertCurve(p, n)
        return hilbert_curve.distance_from_point([int(self.x), int(self.y)])

    def get_tt(self) -> tuple:
        p = 128
        n = 2
        hilbert_curve = HilbertCurve(p, n)
        return hilbert_curve.point_from_distance(int(self.x))

    def get_tau(self) -> tuple:

        ton = (90 - self.x) / 360

        if ton > 0.5:
            ton = 0

        tat = (self.y + 180) / 360
        if tat >= 1:
            tat = 0

        return (int(round(ton * self.FE)), int(round(tat * self.FE)))

    def get_ton(self) -> int:
        ton = (90 - self.x) / 360
        if ton > 0.5:
            ton = 0
        return int(round(ton * self.FE))

    def get_tat(self) -> int:
        tat = (self.y + 180) / 360
        if tat >= 1:
            tat = 0
        return int(round(tat * self.FE))

    def get_lat(self) -> float:
        lat = (0.25 - self.x / self.FE) * 360
        return lat

    def get_lon(self) -> float:
        lon = (self.y / self.FE - 0.5) * 360
        if lon >= 180:
            lon = -180
        return lon

    def get_dec(self) -> tuple:
        lat = (0.25 - self.x / self.FE) * 360
        lon = (self.y / self.FE - 0.5) * 360
        if lon >= 180:
            lon = -180
        return (lat, lon)
