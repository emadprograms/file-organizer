import sys

def test_vision():
    try:
        import Vision
        import Quartz
        from Foundation import NSData
        import re
        
        print("Vision and Quartz imported successfully!")
    except ImportError as e:
        print(f"ImportError: {e}")

if __name__ == "__main__":
    test_vision()
