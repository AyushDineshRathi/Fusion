import json
import os
import random
import re

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

SEED_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(SEED_DIR, "BTech_2023_admitted_students.pdf")
JSON_PATH = os.path.join(SEED_DIR, "btech_2023_students.json")

def generate_synthetic_data(count=570):
    disciplines = ["B.Tech CSE", "B.Tech ECE", "B.Tech ME", "B.Tech SM"]
    prefixes = ["23BCS", "23BEC", "23BME", "23BSM"]
    first_names = ["AADARSH", "AARAV", "VIKAS", "ROHAN", "SNEHA", "PRIYA", "KAVYA", "AMIT", "RAHUL", "ANJALI", "NEHA", "POOJA", "KUNAL", "NISHANT", "PRINCE", "SHREYAS", "MANISH", "SURYANSH", "YASH"]
    last_names = ["NAYAK", "SHARMA", "VERMA", "GUPTA", "SINGH", "PATEL", "KUMAR", "MISHRA", "YADAV", "CHOUDHARY", "JAIN", "BANSAL", "AGARWAL", "RATHORE", "RAJPUT"]
    
    students = []
    
    for i in range(1, count + 1):
        idx = random.randint(0, 3)
        prefix = prefixes[idx]
        disc = disciplines[idx]
        roll_no = f"{prefix}{i:03d}"
        
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        gender = random.choice(["M", "F"])
        
        jee_app_no = f"2303{random.randint(10000000, 99999999)}"
        
        students.append({
            "roll_no": roll_no,
            "name": name,
            "discipline": disc,
            "gender": gender,
            "jee_main_app_no": jee_app_no
        })
        
    return students

def extract_from_pdf(pdf_path):
    students = []
    pattern = re.compile(r"^(\d{2}B[A-Z]{2}\d{3})\s+(.*?)\s+(B\.Tech\s+[A-Z]+)\s+([MF])$")
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    match = pattern.match(line.strip())
                    if match:
                        roll_no, name, disc, gender = match.groups()
                        # Assuming JEE is not in this line, mocking it for now
                        jee_app_no = f"2303{random.randint(10000000, 99999999)}"
                        students.append({
                            "roll_no": roll_no,
                            "name": name.strip(),
                            "discipline": disc.strip(),
                            "gender": gender,
                            "jee_main_app_no": jee_app_no
                        })
    return students

def main():
    students = []
    if os.path.exists(PDF_PATH) and pdfplumber:
        print(f"Reading from PDF: {PDF_PATH}")
        try:
            students = extract_from_pdf(PDF_PATH)
        except Exception as e:
            print(f"Error reading PDF: {e}")
    
    if not students:
        print("PDF not found or unreadable. Generating synthetic data instead (~570 entries).")
        students = generate_synthetic_data(570)
        
    with open(JSON_PATH, "w") as f:
        json.dump(students, f, indent=2)
        
    print(f"Successfully generated {len(students)} student records at {JSON_PATH}")

if __name__ == "__main__":
    main()
