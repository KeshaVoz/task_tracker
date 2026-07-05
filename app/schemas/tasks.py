from datetime import datetime
from typing import Optional
from fastapi import Form
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class STaskIn(BaseModel):
    title: str
    text: Optional[str] = None
    is_completed: Optional[bool] = False 

    model_config = ConfigDict(
        alias_generator=to_camel, 
        populate_by_name=True,
    )

    @classmethod
    def as_form(
        cls,
        title: Optional[str] = Form(None),
        text: Optional[str] = Form(None)
    ) -> dict:
        form_data = {}
        if title is not None: form_data["title"] = title
        if text is not None: form_data["text"] = text
        return form_data


class STaskOut(BaseModel):
    id: int
    title: str
    text: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class STaskUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    is_completed: Optional[bool] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    @classmethod
    def as_form(
        cls,
        title: Optional[str] = Form(None),
        text: Optional[str] = Form(None),
        isCompleted: Optional[str] = Form(None)
    ) -> dict:
        form_data = {}
        if title is not None: 
            form_data["title"] = title
            
        if text is not None: 
            form_data["text"] = text
            
        if isCompleted is not None:
            form_data["is_completed"] = isCompleted.lower() == "true"

        return form_data
