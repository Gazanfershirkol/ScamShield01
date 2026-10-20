"""
ScamShield AI — Data Preparation & Stratified Splitting Pipeline

This script:
1. Generates the curated ScamShield benchmark dataset (2,500 samples:
   60% benign communications [1,500], 40% realistic scams & phishing lures [1,000]).
2. Performs data cleaning and strict post-scrubbing deduplication.
3. Applies PII scrubbing (phone numbers, emails, account numbers).
4. Produces deterministic 70/15/15 stratified train/val/test splits (random_state=42):
   - Train: 1,750 rows (1,050 benign, 700 scam — 40.0% scam)
   - Val:   375 rows (225 benign, 150 scam — 40.0% scam)
   - Test:  375 rows (225 benign, 150 scam — 40.0% scam)
5. Exports clean CSV files to data/processed/ and validates zero cross-split leakage.
"""

import hashlib
import os
from pathlib import Path
import random
import re
from typing import Dict, List, Set, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"

RAW_DATA_FILE = RAW_DATA_DIR / "benchmark_messages.csv"
TRAIN_FILE = PROCESSED_DATA_DIR / "train.csv"
VAL_FILE = PROCESSED_DATA_DIR / "val.csv"
TEST_FILE = PROCESSED_DATA_DIR / "test.csv"

TOTAL_TARGET_SAMPLES = 2500
SAFE_TARGET_SAMPLES = 1500  # 60%
SCAM_TARGET_SAMPLES = 1000  # 40%
RANDOM_SEED = 42


# -----------------------------------------------------------------------------
# PII Scrubbing & Preprocessing Filters
# -----------------------------------------------------------------------------

def scrub_pii(text: str) -> str:
    """
    Scrub identifiable personal information:
    - Replace 10-12 digit phone numbers with <PHONE>
    - Replace email addresses with <EMAIL>
    - Replace account/card numbers (10-16 consecutive digits) with <ACCOUNT_NUM>
    """
    # Scrub emails
    text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "<EMAIL>", text)
    # Scrub international/Indian phone numbers (+91-..., +91..., 098..., or 10-digit mobile)
    text = re.sub(r"(?:\+91[-\s]?|0)?[6-9]\d{9}", "<PHONE>", text)
    # Scrub 10-16 digit account or card numbers
    text = re.sub(r"\b\d{10,16}\b", "<ACCOUNT_NUM>", text)
    return text.strip()


def clean_text(text: str) -> str:
    """Normalize excess whitespace and linebreaks."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -----------------------------------------------------------------------------
# High-Variety Benign Message Generation (1,500 unique post-scrubbed samples)
# -----------------------------------------------------------------------------

def generate_benign_messages(target_count: int = SAFE_TARGET_SAMPLES, seed: int = RANDOM_SEED) -> List[Dict]:
    """Generate diverse, realistic benign communications across everyday digital channels."""
    rng = random.Random(seed)

    first_names = [
        "Aarav", "Priya", "Rahul", "Ananya", "Rohan", "Sneha", "Vikram", "Neha",
        "Aditya", "Pooja", "Arjun", "Kavya", "Siddharth", "Meera", "Karan", "Tanvi",
        "Alex", "Sarah", "David", "Emma", "Michael", "Olivia", "James", "Sophia",
        "Nikhil", "Deepa", "Manish", "Shweta", "Gaurav", "Divya", "Suresh", "Lakshmi",
        "Varun", "Ritu", "Harish", "Pallavi", "Naveen", "Swati", "Abhishek", "Aishwarya",
        "Rajesh", "Geeta", "Sunil", "Anita", "Pranav", "Bhavna", "Kunal", "Preeti"
    ]
    colleges = [
        "KLE BCA Department", "KLE Tech Campus", "Main Library", "Computer Lab 2",
        "Coding Club Hall", "Seminar Room A", "Academic Block 3", "Auditorium",
        "Department of Computer Science", "Library Reading Room", "Student Center",
        "Innovation Hub", "Robotics Lab", "Electronics Lab", "Campus Cafeteria"
    ]
    subjects = [
        "Database Management Systems", "Data Structures and Algorithms", "Python Programming",
        "Machine Learning Fundamentals", "Web Technologies and Frameworks", "Operating Systems",
        "Cloud Computing Architecture", "Software Engineering Principles", "Cybersecurity Basics",
        "Computer Networks", "Mobile App Development", "Object Oriented Java"
    ]
    banks = [
        "SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank",
        "Bank of Baroda", "Canara Bank", "Union Bank of India", "Punjab National Bank", "IndusInd Bank"
    ]
    merchants = [
        "Amazon", "Flipkart", "Swiggy", "Zomato", "Myntra", "Uber", "Blinkit",
        "Zepto", "BookMyShow", "IRCTC", "MakeMyTrip", "BigBasket", "Ola Cabs", "Nykaa"
    ]
    locations = [
        "Indiranagar", "Koramangala", "HSR Layout", "Whitefield", "Jayanagar",
        "Malleshwaram", "Hebbal", "BTM Layout", "Electronic City", "MG Road"
    ]

    personal_templates = [
        "Hey {name}, are we still meeting at {place} today around {time}?",
        "Hi {name}, I left my notebook in {place}. Could you please check if it is still there?",
        "Good morning {name}, please find attached the study notes for {subject}.",
        "Hey! Are you attending the {subject} lecture this afternoon with professor?",
        "Thanks for helping with the assignment yesterday, {name}! Really appreciate your time.",
        "Let's grab a quick coffee at the canteen after our {subject} practical class.",
        "{name}, did the department share the submission deadline for the {subject} project?",
        "Happy birthday {name}! Wishing you a fantastic year ahead with great achievements.",
        "Hey {name}, please ping me when you reach home safely after class.",
        "Could you send me the code repository link we worked on during the {subject} lab?",
        "Hi {name}, are you free for a 10-minute phone call regarding the group project?",
        "Don't forget to bring your ID card tomorrow for the {subject} practical examination, {name}.",
        "Hey {name}, I will be arriving 15 minutes late to {place} due to traffic on {loc}.",
        "Great presentation today in {subject}, {name}! You explained the architecture very clearly.",
        "Can you share the PDF textbook for {subject}? I cannot find it on the college portal.",
        "Hey {name}, let's form a team for the upcoming KLE BCA Coding Club hackathon.",
        "Hi {name}, the professor rescheduled tomorrow's {subject} test to next Monday at {time}."
    ]

    bank_templates = [
        "Your {bank} account ending in XX{acc} was debited by Rs {amt}.00 on {date} for UPI ref {ref}. Available balance: Rs {bal}.",
        "Rs {amt}.00 credited to your {bank} A/C XX{acc} via NEFT from {name} on {date}. Current balance: Rs {bal}.",
        "{bank} Alert: ATM cash withdrawal of Rs {amt} carried out from ATM located at {loc} on {date}. Balance: Rs {bal}.",
        "Dear Customer, your monthly e-statement for {bank} A/C XX{acc} has been generated and sent to your registered email.",
        "Security Alert: Your {bank} NetBanking login password was successfully updated on {date}. If not done by you, contact customer service.",
        "Your {bank} credit card ending XX{acc} statement is ready. Minimum due: Rs {amt}. Due date: {date}. Pay via mobile banking.",
        "Transaction successful: Rs {amt}.00 paid to {merchant} from your {bank} A/C XX{acc} on {date} at {time}.",
        "{bank} Alert: Mandate for Rs {amt}.00 created successfully for {merchant}. Next deduction scheduled on {date}.",
        "Your fixed deposit with {bank} for Rs {bal} has been renewed automatically for 1 year at 7.1% interest.",
        "Salary credited: Rs {bal}.00 deposited into your {bank} account XX{acc} for the month of October."
    ]

    otp_templates = [
        "{otp} is your verification code for {merchant} login. Valid for 10 minutes. Do NOT share this code with anyone.",
        "Your OTP for {bank} NetBanking login is {otp}. Valid for 5 minutes. Bank officials will NEVER ask for your OTP.",
        "Use OTP {otp} to authenticate your transaction of Rs {amt}.00 on {merchant}. Valid for 3 mins. Never disclose OTP.",
        "{otp} is your one-time verification password to confirm your mobile number on {merchant}. Expires in 5 minutes.",
        "Delivery code: {otp} for order #{num}. Please share this secret code with your delivery partner upon package handover.",
        "Your two-factor authentication code for account recovery is {otp}. If you did not request this, secure your account.",
        "Enter {otp} to complete payment of Rs {amt}.00 to {merchant}. Do not share this OTP with anyone to avoid fraud."
    ]

    delivery_templates = [
        "Your order from {merchant} has been dispatched! Delivery expected by {time} on {date}. Track package via official app.",
        "Out for delivery: Your {merchant} order containing electronics will be delivered today by courier partner.",
        "Your {merchant} package has been delivered safely at your address. Thank you for shopping with us!",
        "Your cab is arriving in 4 minutes. Driver: {name}, White Sedan, vehicle number KA-02-AB-{num}.",
        "Your table reservation at the restaurant in {loc} for party of 4 is confirmed for today at {time}.",
        "Your ticket for Train #{num} departing on {date} at {time} is confirmed. Seat details: Coach B3, Berth 42.",
        "Your flight ticket booking to New Delhi is confirmed. PNR: {acc}. Check-in opens 24 hours prior to departure at {time}."
    ]

    notice_templates = [
        "Notice from {college}: All students must submit {subject} lab practical records by Friday 4 PM.",
        "Coding Club Hackathon Announcement: Round 1 evaluation starts at {time} sharp in {place}.",
        "Campus placement drive: Technical interviews for shortlisted candidates will commence tomorrow at 9 AM in {place}.",
        "The scheduled seminar on {subject} will take place on {date} in the {college}. Attendance is mandatory.",
        "Library reminder: The book '{subject} Guide' is due for return on {date}. Renew online via campus portal if needed.",
        "Semester Examination Circular: Download your hall ticket from the student intranet portal before {date}.",
        "Guest lecture by industry expert on {subject} scheduled for this Saturday at {time} in {place}."
    ]

    categories = [
        ("personal_chat", personal_templates),
        ("bank_transaction", bank_templates),
        ("transactional_otp", otp_templates),
        ("delivery_update", delivery_templates),
        ("college_notice", notice_templates),
    ]

    messages = []
    seen_scrubbed: Set[str] = set()
    sample_id = 1

    while len(messages) < target_count:
        for cat_name, template_list in categories:
            if len(messages) >= target_count:
                break
            template = rng.choice(template_list)
            name = rng.choice(first_names)
            place = rng.choice(colleges)
            subject = rng.choice(subjects)
            bank = rng.choice(banks)
            merchant = rng.choice(merchants)
            loc = rng.choice(locations)
            amt = rng.choice([99, 149, 299, 450, 780, 1250, 2400, 3850, 5600, 8900, 14500, 22000])
            bal = rng.choice([2500, 5800, 11400, 24500, 48000, 72500, 95000, 145000])
            acc = f"{rng.randint(1000, 9999)}"
            ref = f"{rng.randint(10000000, 99999999)}"
            otp = f"{rng.randint(100000, 999999)}"
            time_str = f"{rng.randint(1, 12)}:{rng.choice(['00', '15', '30', '45'])} {rng.choice(['AM', 'PM'])}"
            date_str = f"{rng.randint(1, 28)}-Oct-2026"
            num = f"{rng.randint(1000, 9999)}"

            raw_text = template.format(
                name=name, place=place, subject=subject, bank=bank,
                merchant=merchant, loc=loc, amt=amt, bal=bal, acc=acc,
                ref=ref, otp=otp, time=time_str, date=date_str,
                college=place, num=num
            )
            raw_text = clean_text(raw_text)
            scrubbed_key = scrub_pii(raw_text).lower()

            if scrubbed_key not in seen_scrubbed:
                seen_scrubbed.add(scrubbed_key)
                messages.append({
                    "id": f"MSG-BENIGN-{sample_id:05d}",
                    "text": raw_text,
                    "label": 0,
                    "category": cat_name
                })
                sample_id += 1

    return messages[:target_count]


# -----------------------------------------------------------------------------
# High-Variety Scam Message Generation (1,000 unique post-scrubbed samples)
# -----------------------------------------------------------------------------

def generate_scam_messages(target_count: int = SCAM_TARGET_SAMPLES, seed: int = RANDOM_SEED) -> List[Dict]:
    """Generate realistic phishing, social engineering, and fraud messages."""
    rng = random.Random(seed + 100)

    banks = ["SBI", "HDFC", "ICICI", "Axis", "Canara Bank", "PNB", "Kotak", "Bank of Baroda", "Union Bank"]
    spoof_tlds = [".xyz", ".top", ".click", ".buzz", ".surf", ".cfd", ".rest", ".online", ".site", ".live"]
    amounts = ["25,000", "50,000", "1,25,000", "2,50,000", "5,00,000", "15,00,000", "25,00,000"]
    tech_brands = ["Netflix", "Amazon Prime", "Microsoft", "Apple Support", "WhatsApp Support", "Norton Antivirus"]
    officer_names = ["Sharma", "Verma", "Gupta", "Mishra", "Patel", "Singh", "Kumar", "Choudhury"]

    kyc_templates = [
        "URGENT: Dear customer, your {bank} account has been suspended due to pending KYC verification. Update PAN card details immediately at http://{bank_lower}-kyc-update{tld}/login to avoid permanent block.",
        "Dear {bank} User, your net banking access will be terminated within 24 hours. Verify your account credentials now at http://secure-{bank_lower}-portal{tld}/verify or visit bank branch with penalty fee.",
        "Your {bank} debit card has been blocked due to suspicious activity. Unblock immediately by confirming OTP and PIN at http://{bank_lower}-card-unblock{tld}/auth",
        "Alert: Unusual transaction attempt of Rs 48,990 detected on your {bank} account. If you did not authorize, stop payment immediately at http://{bank_lower}-fraud-dispute{tld}/cancel",
        "Dear customer, your credit points of Rs 9,850 on {bank} Credit Card are expiring tonight. Redeem cash directly to your account at http://{bank_lower}-rewards-claim{tld}/redeem",
        "{bank} Notice: Mandatory Aadhar-PAN link pending for A/C ending {acc}. Complete e-KYC within 12 hours at http://{bank_lower}-aadhaar-verification{tld}/portal to prevent account freeze.",
        "Final warning: Your {bank} account will be permanently deactivated tonight due to non-compliance of KYC. Restore access at http://restore-{bank_lower}-service{tld}/activate",
        "Dear {bank} customer, Rs {amt} reward has been credited to your reward wallet. Click http://{bank_lower}-cashback-wallet{tld}/claim to deposit into your bank account immediately."
    ]

    electricity_templates = [
        "Dear consumer, your electricity power will be disconnected tonight at 9:30 PM from the power station because your previous month bill was not updated. Call electricity officer at +9198{phone_tail} immediately.",
        "URGENT ELECTRICITY NOTICE: Power cutoff scheduled for your meter tonight due to pending arrears of Rs 3,450. Contact executive Mr. {officer} on +9187{phone_tail} to settle immediately.",
        "Electricity Department: Your bill payment was rejected. Pay now via http://state-electricity-bill-pay{tld}/quickpay to prevent automatic power disconnection.",
        "Gas supply warning: Your LPG pipeline connection will be terminated within 2 hours. Update Aadhaar details on http://lpg-subsidy-update{tld}/kyc immediately.",
        "Water Supply Dept Alert: Disconnection order issued for consumer meter #{num}. Pay pending surcharge at http://municipal-water-billing{tld}/pay to avoid disconnection today.",
        "Urgent Power Alert: Electricity will be cut off today at 8:00 PM for bill unpaid. Call electricity superintendent Mr. {officer} on +9170{phone_tail} to stop disconnection."
    ]

    lottery_templates = [
        "Congratulations! Your mobile number won cash prize of Rs {amt} in KBC Season 16 Lucky Draw. Call lottery manager Mr. {officer} on +9191{phone_tail} with your winning code {otp}.",
        "Income Tax Department Alert: A tax refund of Rs {tax_amt} has been approved for your PAN card. Submit bank account and verify Aadhaar at http://incometax-refund-verification{tld}/claim to receive funds.",
        "Winner Notice: You have been selected for free gift voucher worth Rs 10,000 from Amazon Shopping festival! Claim your gift card before midnight at http://amazon-festive-rewards{tld}/freegift",
        "Dear user, you received a scratch card bonus of Rs 4,999 in GooglePay! Tap link to transfer reward directly to your bank: http://gpay-reward-claim{tld}/payout",
        "Jio 5G Lucky Winner: Your SIM card won Rs {amt} cash prize! Contact lottery officer on WhatsApp at +9192{phone_tail} to claim your prize cheque today.",
        "You have won a free iPhone 15 Pro in the festive customer appreciation draw! Confirm your delivery address and pay Rs 199 shipping fee at http://apple-festive-giveaway{tld}/claim"
    ]

    job_templates = [
        "Earn Rs 2,500 to Rs 8,000 daily from home! Part-time online job liking YouTube videos and rating hotels on Google Maps. No experience needed. Contact HR manager on WhatsApp: https://wa.me/9199{phone_tail}?text=JOB",
        "Telegram Part-Time Hiring: Work 30 minutes daily and earn Rs 3,000 instant payout. Daily payment guaranteed. Join our recruitment channel immediately: https://t.me/vip_task_earning_{num}",
        "Dear candidate, your resume has been shortlisted for Amazon remote data entry executive. Salary Rs 45,000/month. Pay Rs 499 registration fee to download appointment letter at http://remote-careers-portal{tld}/apply",
        "Work from home opportunity! Earn easy money reviewing products on shopping platforms. Daily payout via UPI. Message our team on Telegram at @daily_task_payout_{num}",
        "Part-time job vacancy: Earn Rs 1,500 per hour by evaluating movie trailers on your mobile phone. Instant daily withdrawal. Register at http://quick-freelance-jobs{tld}/signup",
        "Online survey recruitment: Get paid Rs 500 per survey directly to UPI. Limited slots remaining today. Apply now at http://instant-survey-rewards{tld}/start"
    ]

    delivery_templates = [
        "India Post Alert: Your parcel #IN{num} could not be delivered due to incomplete street address. Please update address details within 24 hours at http://indiapost-parcel-redirection{tld}/tracking or parcel will be returned.",
        "FedEx Notification: Your international parcel has been held at customs. Pay mandatory clearance duty of Rs 149 at http://fedex-parcel-clearance{tld}/pay to release your package.",
        "DHL Express: Package #982{num} is pending dispatch. Confirm your contact details and postal code at http://dhl-express-dispatch{tld}/confirm to avoid cancellation.",
        "Courier delivery attempt failed! Delivery partner was unable to locate you. Reschedule free delivery now: http://express-parcel-reschedule{tld}/book",
        "SpeedPost Alert: Your document consignment #SP{num} requires signature verification. Verify your identity at http://speedpost-delivery-update{tld}/verify or visit depot."
    ]

    extortion_templates = [
        "ATTENTION: I have recorded a video of you browsing adult content using your webcam. Send 0.15 Bitcoin to my wallet address {wallet} within 48 hours or I will forward the video to all your Facebook and phone contacts.",
        "Critical Security Warning: Your Windows PC has been infected with spyware trojan virus. Your passwords and credit cards are compromised. Call Microsoft certified technician immediately at 1800-419-{num}.",
        "Your {brand} subscription has expired and auto-renewed for Rs 12,499. If you did not make this purchase, call support at +9180{phone_tail} to cancel and request instant refund.",
        "Security Alert: Someone accessed your email from IP address 185.220.101.4 in Moscow, Russia. Secure your account now at http://account-security-checkpoint{tld}/auth",
        "Traffic Police E-Challan Notice: You have 1 unpaid traffic violation fine of Rs 1,500 on vehicle #KA-03-EX-{num}. Pay immediately at http://echallan-parivahan-traffic{tld}/pay to avoid court warrant.",
        "SIM Card Notice: Your Airtel / Jio mobile number will be blocked in 24 hours for illegal SMS activity. Call customer verification officer immediately at +9193{phone_tail}."
    ]

    categories = [
        ("kyc_bank_phishing", kyc_templates),
        ("electricity_threat", electricity_templates),
        ("lottery_reward", lottery_templates),
        ("job_offer", job_templates),
        ("delivery_phishing", delivery_templates),
        ("extortion_tech_support", extortion_templates),
    ]

    messages = []
    seen_scrubbed: Set[str] = set()
    sample_id = 1

    while len(messages) < target_count:
        for cat_name, template_list in categories:
            if len(messages) >= target_count:
                break
            template = rng.choice(template_list)
            bank = rng.choice(banks)
            bank_lower = bank.lower().replace(" ", "")
            tld = rng.choice(spoof_tlds)
            amt = rng.choice(amounts)
            tax_amt = rng.choice(["18,450", "24,800", "36,500", "42,100", "55,200", "73,400"])
            brand = rng.choice(tech_brands)
            officer = rng.choice(officer_names)
            phone_tail = f"{rng.randint(10000000, 99999999)}"
            num = f"{rng.randint(1000, 9999)}"
            acc = f"{rng.randint(1000, 9999)}"
            otp = f"{rng.randint(100000, 999999)}"
            wallet = f"1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa{rng.randint(10, 99)}"

            raw_text = template.format(
                bank=bank, bank_lower=bank_lower, tld=tld, amt=amt,
                tax_amt=tax_amt, brand=brand, officer=officer,
                phone_tail=phone_tail, num=num, acc=acc, otp=otp,
                wallet=wallet
            )
            raw_text = clean_text(raw_text)
            scrubbed_key = scrub_pii(raw_text).lower()

            if scrubbed_key not in seen_scrubbed:
                seen_scrubbed.add(scrubbed_key)
                messages.append({
                    "id": f"MSG-SCAM-{sample_id:05d}",
                    "text": raw_text,
                    "label": 1,
                    "category": cat_name
                })
                sample_id += 1

    return messages[:target_count]


# -----------------------------------------------------------------------------
# Pipeline Execution
# -----------------------------------------------------------------------------

def prepare_data(seed: int = RANDOM_SEED) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Builds the dataset, scrubs PII, enforces deduplication, and generates
    exact 70/15/15 stratified train/val/test splits (1750/375/375).
    """
    print("=" * 70)
    print("ScamShield AI — Data Pipeline & Stratified Split Generator")
    print("=" * 70)

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Generate unique benchmark messages (1,500 benign, 1,000 scam)
    print(f"\n[1/5] Generating unique benchmark corpus ({TOTAL_TARGET_SAMPLES} samples)...")
    benign_samples = generate_benign_messages(SAFE_TARGET_SAMPLES, seed=seed)
    scam_samples = generate_scam_messages(SCAM_TARGET_SAMPLES, seed=seed)

    all_raw_samples = benign_samples + scam_samples
    rng = random.Random(seed)
    rng.shuffle(all_raw_samples)

    raw_df = pd.DataFrame(all_raw_samples)
    raw_df.to_csv(RAW_DATA_FILE, index=False, encoding="utf-8")
    print(f" -> Saved raw benchmark corpus to: {RAW_DATA_FILE}")
    print(f"    Total rows: {len(raw_df)} (Benign: {len(benign_samples)}, Scam: {len(scam_samples)})")

    # 2. Preprocess & Scrub PII
    print("\n[2/5] Cleaning text and scrubbing PII...")
    raw_df["text"] = raw_df["text"].apply(clean_text)
    raw_df["text_scrubbed"] = raw_df["text"].apply(scrub_pii)

    # Content hash deduplication check
    raw_df["content_hash"] = raw_df["text_scrubbed"].apply(
        lambda t: hashlib.sha256(t.lower().encode("utf-8")).hexdigest()
    )

    before_dedup = len(raw_df)
    df_clean = raw_df.drop_duplicates(subset=["content_hash"]).copy()
    after_dedup = len(df_clean)
    print(f" -> Deduplication check: {before_dedup} -> {after_dedup} unique post-scrubbed items.")
    assert after_dedup == TOTAL_TARGET_SAMPLES, (
        f"Expected {TOTAL_TARGET_SAMPLES} unique items, but got {after_dedup}"
    )

    # 3. Stratified Partitioning: 70% Train (1750), 15% Val (375), 15% Test (375)
    print("\n[3/5] Computing 70% Train (1750), 15% Val (375), 15% Test (375) stratified splits...")
    train_df, temp_df = train_test_split(
        df_clean,
        train_size=1750,
        random_state=seed,
        stratify=df_clean["label"]
    )

    val_df, test_df = train_test_split(
        temp_df,
        train_size=375,
        test_size=375,
        random_state=seed,
        stratify=temp_df["label"]
    )

    # Prepare export schemas (standard columns: id, text, label, category)
    train_export = train_df[["id", "text_scrubbed", "label", "category"]].rename(columns={"text_scrubbed": "text"})
    val_export = val_df[["id", "text_scrubbed", "label", "category"]].rename(columns={"text_scrubbed": "text"})
    test_export = test_df[["id", "text_scrubbed", "label", "category"]].rename(columns={"text_scrubbed": "text"})

    # 4. Leakage Verification
    print("\n[4/5] Verifying zero cross-split leakage...")
    train_hashes = set(train_df["content_hash"])
    val_hashes = set(val_df["content_hash"])
    test_hashes = set(test_df["content_hash"])

    train_val_leak = train_hashes.intersection(val_hashes)
    train_test_leak = train_hashes.intersection(test_hashes)
    val_test_leak = val_hashes.intersection(test_hashes)

    assert len(train_val_leak) == 0, f"LEAKAGE DETECTED: {len(train_val_leak)} hashes overlap between train and val"
    assert len(train_test_leak) == 0, f"LEAKAGE DETECTED: {len(train_test_leak)} hashes overlap between train and test"
    assert len(val_test_leak) == 0, f"LEAKAGE DETECTED: {len(val_test_leak)} hashes overlap between val and test"
    print(" -> Leakage Check PASSED: Exactly 0 overlapping messages across all three splits.")

    # 5. Export Processed Splits
    print("\n[5/5] Exporting clean CSV splits to data/processed/...")
    train_export.to_csv(TRAIN_FILE, index=False, encoding="utf-8")
    val_export.to_csv(VAL_FILE, index=False, encoding="utf-8")
    test_export.to_csv(TEST_FILE, index=False, encoding="utf-8")

    print(f" -> Train set:      {TRAIN_FILE} ({len(train_export)} rows, {train_export['label'].mean():.1%} scam)")
    print(f" -> Validation set: {VAL_FILE} ({len(val_export)} rows, {val_export['label'].mean():.1%} scam)")
    print(f" -> Test set:       {TEST_FILE} ({len(test_export)} rows, {test_export['label'].mean():.1%} scam)")

    print("\n" + "=" * 70)
    print("Phase 2 Data Pipeline Execution COMPLETE.")
    print("=" * 70)

    return train_export, val_export, test_export


if __name__ == "__main__":
    prepare_data()
