from typing import List, Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict

class Point(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    name: str = "P"
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
