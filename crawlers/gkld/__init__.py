from pydantic import BaseModel

class Trace(BaseModel):
    province: set = set()
    exam_type: str = ''
    info_type: str = ''
    scrape_times: int = 1