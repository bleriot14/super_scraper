from pydantic import BaseModel, Field, root_validator
from selenium.webdriver.common.by import By

class ElementLocator(BaseModel):
    by: str = Field(..., description="Selenium By strategy (e.g., ID, CLASS_NAME)")
    value: str = Field(..., description="Value of the element locator")