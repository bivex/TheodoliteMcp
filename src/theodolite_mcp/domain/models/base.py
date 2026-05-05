from typing import List, Optional
from pydantic import BaseModel

class Point(BaseModel):
    name: str = "P"
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
