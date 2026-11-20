from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str

    model_config = {
        "from_attributes": True
    }
