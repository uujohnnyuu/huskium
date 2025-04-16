# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations


type TupleCoordinate = tuple[int, int, int, int] | tuple[float, float, float, float]
type Coordinate = TupleCoordinate | dict[str, int] | dict[str, float]
