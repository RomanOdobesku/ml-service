from sqlalchemy import ForeignKey, Integer
from sqlmodel import Column, Field, Relationship, SQLModel


class Prediction(SQLModel, table=True):
    id: int = Field(primary_key=True)
    N_Days: int = Field()
    Drug: str = Field()
    Age: int = Field()
    Sex: str = Field()
    Ascites: str = Field()
    Hepatomegaly: str = Field()
    Spiders: str = Field()
    Edema: str = Field()
    Bilirubin: float = Field()
    Cholesterol: float = Field()
    Albumin: float = Field()
    Copper: float = Field()
    Alk_Phos: float = Field()
    SGOT: float = Field()
    Tryglicerides: float = Field()
    Platelets: float = Field()
    Prothrombin: float = Field()
    Stage: int = Field()
    answer: int = Field()
    batch_id: int = Field(sa_column=Column(Integer, ForeignKey("predictionbatch.id")))
    batch: "PredictionBatch" = Relationship(back_populates="predictions")
