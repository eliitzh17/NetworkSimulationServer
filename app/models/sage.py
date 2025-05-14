from abc import ABC, abstractmethod
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.statuses_enums import TopologyStatusEnum

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')

class AbstractSagaModel(BaseModel, ABC):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[TopologyStatusEnum] = None
    
    #rates
    processed_items: int = 0
    failed_items: int = 0
    success_items: int = 0
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @abstractmethod
    def get_saga_type(self) -> str:
        """Return the type/name of the saga. Should be implemented by subclasses."""
        pass

    @abstractmethod
    def to_mongo_dict(self) -> dict:
        """Return a dict suitable for MongoDB insertion. Should be implemented by subclasses."""
        pass
    
class SimulationSaga(AbstractSagaModel):
    sim_id: str
    simulation_data: Optional[Any] = None  # Can be refined to a more specific type if needed

    def get_saga_type(self) -> str:
        return "simulation"

    def to_mongo_dict(self) -> dict:
        # Use model_dump to get all fields, including aliases for MongoDB
        data = self.model_dump(by_alias=True)
        return data
