import asyncio
from dataclasses import dataclass

async def test_input_submission_returns_matches():
    """This is the target function we want to find"""
    result = await some_async_operation()
    return result

def regular_function():
    return "not async"

class SampleClass:
    def method(self):
        pass
    
    async def async_method(self):
        await asyncio.sleep(1)

@dataclass
class DataExample:
    name: str
    value: int

async def some_async_operation():
    await asyncio.sleep(0.1)
    return {"data": "test"}
