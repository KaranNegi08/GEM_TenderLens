import json
from services.vendor_service import VendorService
from services.comparison_service import ComparisonService

vs = VendorService()
v1 = vs.process_vendor_submission('Bharat Digital Solutions', 'GEM_9146015', ['./data/uploads/vendor_submissions/Bharat_digital_email/vendor_B_bharat_digital_email.eml'])
v2 = vs.process_vendor_submission('Technova Pvt Ltd', 'GEM_9146015', ['./data/uploads/vendor_submissions/technova/vendor_A_technova_proposal.docx'])
v3 = vs.process_vendor_submission('Sunrise Infotech', 'GEM_9146015', ['./data/uploads/vendor_submissions/sunrise_infotech/vendor_C_sunrise_infotech_proposal.pdf'])

cs = ComparisonService()
comp = cs.generate_comparison_matrix('GEM_9146015', [v1, v2, v3])

print("=== COMMERCIAL COMPARISON ===")
for c in comp['commercial_comparison']:
    tax_note_clean = str(c['tax_note']).replace('\u20b9', 'INR ')
    print(f"Rank {c['rank']} ({c['l_status']}): {c['vendor_name']} - Base: {c['base_price']} | Tax: {c['tax_amount']} | Total: {c['total_cost']} | TaxNote: {tax_note_clean}")

print("\n=== COMPLIANCE FINDINGS (Total:", len(comp['compliance_findings']), ") ===")
for f in comp['compliance_findings']:
    print(f"{f['vendor_name']:25} | {f['requirement_id']:7} | {f['status']:15} | {f['explanation']}")

print("\nL1 Vendor:", comp['l1_vendor'], "(Cost:", comp['l1_cost'], ")")
print("L1 Qualified Vendor:", comp['l1_qualified_vendor'], "(Cost:", comp['l1_qualified_cost'], ")")
print("L1 Deviations Count:", comp['l1_deviations_count'])
