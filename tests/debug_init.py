import os
import sys
from dotenv import load_dotenv
print("import genai")
from google import genai
print("import Pipeline")
from src.pipeline import Pipeline

print("loading env")
load_dotenv()
print("init Pipeline")
p = Pipeline(delay_between_pages=0)
print("done!")
