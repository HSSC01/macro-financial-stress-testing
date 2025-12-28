"""
Defines balance-sheet schema objects and stylised constructors.
"""

import dataclasses
from typing import Dict, List
import stress_test.config as cfg

@dataclasses.dataclass
class PortfolioBucket:
    name: str
    ead: float
    rw: float
    lgd: float

    @property
    def rwa(self) -> float: # risk-weighted assets
        return self.ead * self.rw
    
    def __post_init__(self):
        if self.ead < 0.0:
            raise ValueError(f"Bucket {self.name}: EAD must be non-negative, got {self.ead}")
        if not (0.0 <= self.rw <= 2.0):
            raise ValueError(f"Bucket {self.name}: Risk weight must be in [0,2], got {self.rw}")
        if not (0.0 <= self.lgd <= 1.0):
            raise ValueError(f"Bucket {self.name}: LGD must be in [0,1], got {self.lgd}")

@dataclasses.dataclass
class Bank:
    name: str
    cet1: float
    buckets: dict[str, PortfolioBucket]
    overlays: dict[str, float]

    @property
    def total_ead(self) -> float:
        return sum(bucket.ead for bucket in self.buckets.values())
    
    @property
    def total_rwa(self) -> float:
        return self.cet1 / self.cet1_ratio
    
    @property
    def cet1_ratio(self) -> float:
        try:
            return float(cfg.REPORTED_CET1_RATIO[self.name])
        except KeyError:
            raise KeyError(f"No reported CET1 ratio configured for bank '{self.name}'")
    
    def __post_init__(self):
        if self.cet1 < 0.0:
            raise ValueError(f"Bank {self.name}: CET1 must be non-negative, got {self.cet1}")

        # Buckets must be complete and only contain the expected base portfolios
        expected = set(cfg.BASE_PORTFOLIOS)
        provided = set(self.buckets.keys())

        missing = expected - provided
        extra = provided - expected

        if missing:
            raise KeyError(
                f"Bank {self.name}: Missing base portfolio bucket(s): {sorted(missing)}"
            )
        if extra:
            raise KeyError(
                f"Bank {self.name}: Unexpected bucket key(s) (not in BASE_PORTFOLIOS): {sorted(extra)}"
            )

        # Each bucket value must be a PortfolioBucket and must match its dict key
        for key, bucket in self.buckets.items():
            if not isinstance(bucket, PortfolioBucket):
                raise TypeError(
                    f"Bank {self.name}: Bucket {key} must be a PortfolioBucket instance, got {type(bucket)}"
                )
            if bucket.name != key:
                raise ValueError(
                    f"Bank {self.name}: Bucket key '{key}' does not match bucket.name '{bucket.name}'"
                )

        # Overlay shares must be proportions in [0, 1]
        for overlay_key, share in self.overlays.items():
            if not isinstance(share, (int, float)):
                raise TypeError(
                    f"Bank {self.name}: Overlay '{overlay_key}' must be a number, got {type(share)}"
                )
            if not (0.0 <= float(share) <= 1.0):
                raise ValueError(
                    f"Bank {self.name}: Overlay '{overlay_key}' must be in [0,1], got {share}"
                )

def make_stylised_bank(name: str) -> Bank: # Construct stylised Bank object from config assumptions
    if name not in cfg.BANK_NAMES:
        raise KeyError(f"Unknown bank name '{name}'")
    
    total_ead = float(cfg.TOTAL_EAD_BN[name])
    shares = cfg.BANK_BASE_PORTFOLIO_SHARES[name]
    share_sum = sum(float(shares[p]) for p in cfg.BASE_PORTFOLIOS)
    if abs(share_sum - 1.0) > 1e-6:
        raise ValueError(f"Bank {name}: Base Portfolio shares must sum to 1.0, got {share_sum}")
    
    # Build portfolio buckets
    buckets: Dict[str, PortfolioBucket] = {}
    for portfolio in cfg.BASE_PORTFOLIOS:
        ead = total_ead * float(shares[portfolio])
        rw = float(cfg.RISK_WEIGHT[name][portfolio])
        lgd = float(cfg.BASELINE_LGD[portfolio])
        buckets[portfolio] = PortfolioBucket(name=portfolio, ead=ead, rw=rw, lgd=lgd)

    # Overlays (subset shares)
    overlays: Dict[str, float] = {
        "high_ltv_share_of_mortgages": float(cfg.HIGH_LTV_SHARE_OF_MORTGAGES[name]),
        "export_share_of_large_corp": float(cfg.EXPORT_SHARE_OF_LARGE_CORP[name]),
        "energy_intensive_share_of_corp": float(cfg.ENERGY_INTENSIVE_SHARE_OF_CORP[name])
    }

    cet1 = cfg.CET1_CAPITAL_BN[name]
    return Bank(name=name, cet1=cet1, buckets=buckets, overlays=overlays)

def make_stylised_banks() -> List[Bank]: # Construct stylised Bank objects for all banks in config
    return [make_stylised_bank(name) for name in cfg.BANK_NAMES]
