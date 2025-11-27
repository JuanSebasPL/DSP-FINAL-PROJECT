from typing import List, Dict
from pydantic import BaseModel


class InputData(BaseModel):
    data: List[Dict]