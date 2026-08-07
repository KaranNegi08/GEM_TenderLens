"""
Sample Data Generator for GeM TenderLens.
Creates realistic sample tender files (Bid PDF/Doc, Technical Spec, BOQ) matching GeM Bid GEM/2026/B/7798305
and 3 vendor proposals for immediate out-of-the-box testing.
"""

import os

TENDER_DIR = "./data/uploads/tender_documents"
VENDOR_DIR = "./data/uploads/vendor_submissions"

os.makedirs(TENDER_DIR, exist_ok=True)
os.makedirs(VENDOR_DIR, exist_ok=True)

# 1. Main GeM Bid Document (GEM/2026/B/7798305)
GEM_BID_TEXT = """GeM Bid Document
Bid Number: GEM/2026/B/7798305
Dated: 16-07-2026

BID DETAILS:
Bid End Date/Time: 06-08-2026 21:00:00
Bid Opening Date/Time: 06-08-2026 21:30:00
Bid Offer Validity: 60 Days
Ministry/State Name: Ministry Of Defence
Department Name: Department Of Military Affairs
Organisation Name: Indian Army
Total Quantity: 10
Item Category: Books (10 Technical and Military Strategy Titles)
Primary Product Category: The AI-Driven Leader
Estimated Bid Value: 80000 INR
Evaluation Method: Total value wise evaluation
Delivery Days: 21 Days to Kupwara

ITEM LIST / BOQ TITLES:
1. The AI-Driven Leader (Qty: 1)
2. Kashmir The Unfiltered Truth (Qty: 1)
3. Inside The Terrifying World of Jaish-E-Mohammed (Qty: 1)
4. Artificial Intelligence (Qty: 1)
5. The Jihad Game (Qty: 1)
6. K File The Conspiracy of Silence (Qty: 1)
7. My Frozen Turbulence in Kashmir (Qty: 1)
8. Kashmir The War of Narratives (Qty: 1)
9. Drones Technology for Beginners (Qty: 1)
10. Drone Engineering (Qty: 1)

MANDATORY ELIGIBILITY & TERMS:
- Experience Criteria: Minimum 2 Years past experience in supplying similar books/publications to Central/State Govt/PSU.
- Past Performance: Minimum 10% past performance in last 3 financial years.
- Turnover Criteria: OEM / Bidder average turnover of 1 Lakh INR over last 3 years.
- MSE Exemption: MSE and DPIIT registered Startups are eligible for relaxation from Experience and Turnover criteria.
- Option Clause: Purchaser reserves right to increase/decrease quantity up to 25%.
"""

with open(os.path.join(TENDER_DIR, "GeM_Bid_GEM_2026_B_7798305.txt"), "w", encoding="utf-8") as f:
    f.write(GEM_BID_TEXT)

# 2. Technical Specifications Document
TECH_SPEC_TEXT = """ETG: 2026-27
UNDER MAJOR HEAD 2076, MINOR HEAD 112(D)(i) 3
CODE HEAD 534/03

TECHNICAL SPECIFICATIONS & NOMENCLATURE:

Ser No. | Nomenclature | A/U | Quantity Required
1 | The AI-Driven Leader | Nos | 01
2 | Kashmir The Unfiltered Truth | Nos | 01
3 | Inside The Terrifying World of Jaish-E-Mohammed | Nos | 01
4 | Artificial Intelligence | Nos | 01
5 | The Jihad Game | Nos | 01
6 | K File The Conspiracy of Silence | Nos | 01
7 | My Frozen Turbulence in Kashmir | Nos | 01
8 | Kashmir The War of Narratives | Nos | 01
9 | Drones Technology for Beginners | Nos | 01
10 | Drone Engineering | Nos | 01

Special Instructions:
- Hardcover edition preferred.
- All books must be brand new, official publisher prints.
- Delivery location: Kupwara within 21 days from order placement.
"""

with open(os.path.join(TENDER_DIR, "Technical_Specifications.txt"), "w", encoding="utf-8") as f:
    f.write(TECH_SPEC_TEXT)

# 3. BOQ Line Items CSV
BOQ_CSV_TEXT = """Ser_No,Nomenclature,Unit,Quantity,Estimated_Price_INR
1,The AI-Driven Leader,Nos,1,8000
2,Kashmir The Unfiltered Truth,Nos,1,7500
3,Inside The Terrifying World of Jaish-E-Mohammed,Nos,1,8500
4,Artificial Intelligence,Nos,1,9000
5,The Jihad Game,Nos,1,7000
6,K File The Conspiracy of Silence,Nos,1,8000
7,My Frozen Turbulence in Kashmir,Nos,1,8500
8,Kashmir The War of Narratives,Nos,1,7500
9,Drones Technology for Beginners,Nos,1,8000
10,Drone Engineering,Nos,1,8000
"""

with open(os.path.join(TENDER_DIR, "BOQ_Details.csv"), "w", encoding="utf-8") as f:
    f.write(BOQ_CSV_TEXT)


# 4. Vendor Proposal Submissions

# Vendor 1: Apex Publishers (MSE Verified, L-1 Quote)
v1_dir = os.path.join(VENDOR_DIR, "Vendor_Apex_Publishers")
os.makedirs(v1_dir, exist_ok=True)
v1_proposal = """From: sales@apexpublishers.com
To: tender@defence.gov.in
Subject: Bid Submission for GeM Tender GEM/2026/B/7798305 - Apex Publishers

Respected Buyer,

We are pleased to submit our commercial quotation and technical compliance proposal for GeM Tender GEM/2026/B/7798305 (Books Procurement).

COMMERCIAL QUOTATION:
Quoted Base Price (All 10 Books): INR 68,000.00
Applicable Tax / GST (5%): INR 3,400.00
Total Quoted Price: INR 71,400.00

DELIVERY & WARRANTY TERMS:
Offered Delivery Period: 14 Days to Kupwara (Well within 21 days requirement).
Warranty: 12 Months replacement warranty against printing or binding defects.

TECHNICAL COMPLIANCE & CREDENTIALS:
- All 10 books offered in brand new, hardcover official publisher editions.
- Apex Publishers is an MSE Udyam Registered Micro Enterprise (Certificate No: UDYAM-JK-01-0012345).
- Past experience of supplying Defence units for 3 years attached.
"""
with open(os.path.join(v1_dir, "proposal_apex_publishers.eml"), "w", encoding="utf-8") as f:
    f.write(v1_proposal)


# Vendor 2: Frontier Book House (Standard Non-MSE, L-2 Quote)
v2_dir = os.path.join(VENDOR_DIR, "Vendor_Frontier_Books")
os.makedirs(v2_dir, exist_ok=True)
v2_proposal = """From: tender@frontierbooks.in
To: tender@defence.gov.in
Subject: Proposal Submission for Bid GEM/2026/B/7798305 - Frontier Book House

Dear Procurement Officer,

Please find our proposal for the procurement of 10 technical book titles under GeM Tender GEM/2026/B/7798305.

COMMERCIAL OFFER:
Quoted Base Amount: INR 74,000.00
GST (5%): INR 3,700.00
Total Quoted Amount: INR 77,700.00

DELIVERY & WARRANTY:
Delivery Lead Time: 20 Days to Kupwara.
Warranty Period: 12 Months.

COMPLIANCE DETAILS:
- 100% compliant with mandatory technical specifications and nomenclature.
- Past Performance certificates of supplying Central Govt orders attached.
- GST registration and turnover certificate attached.
"""
with open(os.path.join(v2_dir, "proposal_frontier_books.txt"), "w", encoding="utf-8") as f:
    f.write(v2_proposal)


# Vendor 3: Vanguard Tech & Books (Overpriced, Exceeds Delivery limit)
v3_dir = os.path.join(VENDOR_DIR, "Vendor_Vanguard_Tech")
os.makedirs(v3_dir, exist_ok=True)
v3_proposal = """From: bids@vanguardtech.co.in
To: tender@defence.gov.in
Subject: Bid Submission GEM/2026/B/7798305 - Vanguard Tech

PROPOSAL DETAILS:
Quoted Amount: INR 85,000.00
Tax / GST: INR 4,250.00
Total Quoted Amount: INR 89,250.00

TERMS:
Delivery Days: 30 Days (Requires extension).
Warranty: 6 Months.

NOTE: Scanned copy of experience certificate attached for manual review.
"""
with open(os.path.join(v3_dir, "proposal_vanguard_tech.txt"), "w", encoding="utf-8") as f:
    f.write(v3_proposal)

print("Sample data generated successfully!")
