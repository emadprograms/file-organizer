import subprocess
import sys
import os

houses = [
    "723 - محمد علي ميرزا"
]

def main():
    # Make sure stdout uses utf-8
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    for house in houses:
        print(f"Processing House: {house}")
        path = f"D:\\areas\\Safra D\\{house}"
        
        print(f"Running create for {house}...")
        cmd_create = ["python", "src/main.py", "create", path, "--model", "gemma-4-31b-it", "--categorization-model", "gemini-3.5-flash-lite"]
        res_create = subprocess.run(cmd_create)
        if res_create.returncode != 0:
            print(f"Create command failed for '{house}' with exit code {res_create.returncode}. Halting script.", file=sys.stderr)
            sys.exit(res_create.returncode)
            
        print(f"Running verify for {house}...")
        cmd_verify = ["python", "src/main.py", "verify", path]
        res_verify = subprocess.run(cmd_verify)
        if res_verify.returncode != 0:
            print(f"Verify command failed for '{house}' with exit code {res_verify.returncode}. Halting script.", file=sys.stderr)
            sys.exit(res_verify.returncode)
            
    print("Successfully processed the final house!")

if __name__ == "__main__":
    main()
