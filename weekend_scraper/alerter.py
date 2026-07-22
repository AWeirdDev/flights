from dataclasses import dataclass
from typing import Optional, List
import statistics
from .models import PriceSample

@dataclass
class Alert:
    sample: PriceSample
    rule: str  # 'absolute', 'drop_15', 'drop_20'
    median_price: Optional[int] = None
    drop_percent: Optional[float] = None

    @property
    def dedup_key(self) -> str:
        # Price bucketed to nearest £5
        price_bucket = (self.sample.price_gbp // 500) * 5
        return f"{self.rule}:{self.sample.out_date}:{self.sample.ret_date}:{self.sample.from_airport}:{self.sample.to_airport}:{price_bucket}"

def get_alerts(sample: PriceSample, history: List[int]) -> List[Alert]:
    """
    Given a new sample and historical prices (pennies), returns a list of Alerter rules that fire.
    """
    alerts = []
    
    # Absolute alert thresholds (pennies), tiered by destination band:
    #   European weekend break destinations — £130
    #   London Heathrow / Gatwick             — £100
    #   Everything else (STN / LTN / LCY)     — £70
    european = {"CDG", "BCN", "AMS", "AGP"}
    if sample.to_airport in european:
        threshold = 13000
    elif sample.to_airport in ("LHR", "LGW"):
        threshold = 10000
    else:
        threshold = 7000

    # Rule 1: Absolute cap
    if sample.price_gbp < threshold:
        alerts.append(Alert(sample=sample, rule="absolute"))
        
    # Relative rules: need at least 5 historical samples for a baseline
    if len(history) >= 5:
        median = statistics.median(history)
        if median > 0:
            drop = (median - sample.price_gbp) / median
            if drop >= 0.20:
                alerts.append(Alert(sample=sample, rule="drop_20", median_price=int(median), drop_percent=drop))
            elif drop >= 0.15:
                alerts.append(Alert(sample=sample, rule="drop_15", median_price=int(median), drop_percent=drop))
                
    return alerts
