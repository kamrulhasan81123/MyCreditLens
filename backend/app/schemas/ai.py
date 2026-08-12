from pydantic import BaseModel, Field, model_validator


class CounterfactualRequest(BaseModel):
    target_probability: float | None = Field(None, gt=0, lt=1)
    limit: int = Field(5, ge=1, le=10)


class FairnessEvaluationRequest(BaseModel):
    model_id: str
    labels: list[int]
    probabilities: list[float]
    groups: list[str]
    threshold: float = Field(0.5, gt=0, lt=1)
    minimum_group_size: int = Field(30, ge=10)

    @model_validator(mode="after")
    def validate_lengths(self):
        if not (len(self.labels) == len(self.probabilities) == len(self.groups)):
            raise ValueError("labels, probabilities, and groups must have equal length")
        return self


class DriftEvaluationRequest(BaseModel):
    reference: dict[str, list[float]]
    current: dict[str, list[float]]


class PerformanceEvaluationRequest(BaseModel):
    labels: list[int]
    probabilities: list[float]
    threshold: float = Field(0.5, gt=0, lt=1)

    @model_validator(mode="after")
    def validate_lengths(self):
        if len(self.labels) != len(self.probabilities):
            raise ValueError("labels and probabilities must have equal length")
        return self
