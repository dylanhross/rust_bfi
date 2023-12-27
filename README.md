# rust-bfi
A toy brainfuck interpreter written in Python and Rust for learning purposes.

https://en.wikipedia.org/wiki/Brainfuck

## Example script with Python enums and case-match

```Python
from enum import Enum, auto
from typing import List


class PrimalCuts(Enum):
    Chuck = auto()
    Brisket = auto()
    Plate = auto()
    Rib = auto()
    ShortLoin = auto()
    Sirloin = auto()
    Round = auto()
    Shank = auto()


def get_retail_cuts(primal: PrimalCuts) -> List[str]:
    match primal:
        case PrimalCuts.Chuck:
            return ["burger", "roast"]
        case PrimalCuts.Plate:
            return ["short ribs", "flank steak"]
        case PrimalCuts.Rib:
            return ["ribeye steak", "standing rib roast"]
        case PrimalCuts.ShortLoin:
            return ["tenderloin", "porterhouse steak", "T-bone steak", "New York strip steak"]
        case PrimalCuts.Sirloin:
            return ["tritip roast"]
        case _:
            return []


def _main():
    for primal in PrimalCuts:
        print("-" * 20)
        print(primal)
        for retail in get_retail_cuts(primal):
            print(retail)


if __name__ == "__main__":
    _main()
```
