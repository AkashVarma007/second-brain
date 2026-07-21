"""Pydantic schemas — the Python side of the HTTP protocol contract."""

from typing import Literal

from pydantic import BaseModel

Mode = Literal["note", "task"]
Priority = Literal["high", "medium", "low"]


class NoteResult(BaseModel):
    text: str


class TaskResult(BaseModel):
    title: str
    priority: Priority


class ProcessResponse(BaseModel):
    transcript: str
    result: NoteResult | TaskResult


class NoteOut(BaseModel):
    id: int
    text: str
    created_at: str


class TaskOut(BaseModel):
    id: int
    title: str
    priority: Priority
    created_at: str
