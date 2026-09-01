import os
import sys
import subprocess
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

AREA_DIR = r"D:\Areas\Safra C"

def verify_all():
    dirs = [d for d in os.listdir(AREA_DIR) if os.path.isdir(os.path.join(AREA_DIR, d)) and " - " in d]
    
    passed = 0
    failed = 0
    results = []
    
    for d in sorted(dirs):
        full_path = os.path.join(AREA_DIR, d)
        
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        result = subprocess.run([sys.executable, "src/main.py", "verify", full_path], capture_output=True, text=True, encoding="utf-8", env=env)
        
        if result.returncode == 0:
            passed += 1
            print(f"✅ {d} - PASS")
        else:
            failed += 1
            print(f"❌ {d} - FAIL")
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 5:
                    print("\n".join(lines[-5:]))
                else:
                    print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr.strip()}")
            
    print("\n" + "="*40)
    print(f"  Verified: {len(dirs)} houses")
    print(f"  ✅ Passed:  {passed}")
    print(f"  ❌ Failed:   {failed}")
    print("="*40)

if __name__ == '__main__':
    verify_all()
