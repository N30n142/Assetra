"""
One-time import script for Starzs Investment Company's existing asset
inventory (from OFFICE_INVENTORY and FACILITY_ASSET spreadsheets).

Run this ONCE from inside your assetra folder:
    python3 import_starzs_assets.py

It will:
  - make sure all locations exist
  - insert every asset below (skipping any Asset ID that already exists,
    so it's safe to run more than once)
"""
from db import get_db, init_db

ASSETS = [
    ('STZ-CUSH-001', 'Cushion Set of Chairs', 'Furniture', 'RECEPTION'),
    ('STZ-CUSH-002', 'Cushion Set of Chairs', 'Furniture', 'RECEPTION'),
    ('STZ-CUSH-003', 'Cushion Set of Chairs', 'Furniture', 'RECEPTION'),
    ('STZ-CUSH-004', 'Cushion Set of Chairs', 'Furniture', 'RECEPTION'),
    ('STZ-CUSH-005', 'Cushion Set of Chairs', 'Furniture', 'RECEPTION'),
    ('STZ-TV-001', 'Television (25 inches)', 'Equipment', 'RECEPTION'),
    ('STZ-WCB-001', 'Wall Cabinet', 'Furniture', 'RECEPTION'),
    ('STZ-ERGCH-001', 'Ergonomic Chair', 'Other', 'RECEPTION'),
    ('STZ-WDBL-001', 'Window Blind', 'Other', 'RECEPTION'),
    ('STZ-SDTBL-001', 'Side Table', 'Furniture', 'RECEPTION'),
    ('STZ-WSFC-001', 'Workstation/File Cabinet', 'Furniture', 'RECEPTION'),
    ('STZ-WSTBN-001', 'Waste Bin', 'Furniture', 'RECEPTION'),
    ('STZ-WTRDSP-001', 'Water dispenser', 'Equipment', 'RECEPTION'),
    ('STZ-ERGCH-002', 'Ergonomic Chair', 'Furniture', 'General Work Section'),
    ('STZ-ERGCH-003', 'Ergonomic Chair', 'Furniture', 'General Work Section'),
    ('STZ-ERGCH-004', 'Ergonomic Chair', 'Furniture', 'General Work Section'),
    ('STZ-ERGCH-005', 'Ergonomic Chair', 'Furniture', 'General Work Section'),
    ('STZ-ERGCH-006', 'Ergonomic Chair', 'Furniture', 'General Work Section'),
    ('STZ-ERGCH-007', 'Ergonomic Chair', 'Furniture', 'General Work Section'),
    ('STZ-OFFWRK-001', 'Office Workstation', 'Other', 'General Work Section'),
    ('STZ-OFFWRK-002', 'Office Workstation', 'Other', 'General Work Section'),
    ('STZ-OFFWRK-003', 'Office Workstation', 'Other', 'General Work Section'),
    ('STZ-OFFWRK-004', 'Office Workstation', 'Other', 'General Work Section'),
    ('STZ-OFFWRK-005', 'Office Workstation', 'Other', 'General Work Section'),
    ('STZ-OFFWRK-006', 'Office Workstation', 'Other', 'General Work Section'),
    ('STZ-FILECAB-001', 'File Cabinet', 'Furniture', 'General Work Section'),
    ('STZ-TBLFRDG-001', 'Table fridge', 'Furniture', 'General Work Section'),
    ('STZ-ELEKTL-001', 'Electric Kettle', 'Equipment', 'General Work Section'),
    ('STZ-ELEKTL-002', 'Electric Kettle', 'Equipment', 'General Work Section'),
    ('STZ-BLKCOF-001', 'Black Coffee Maker', 'Other', 'General Work Section'),
    ('STZ-BLKELE-001', 'Black Electric Kettle', 'Equipment', 'General Work Section'),
    ('STZ-BLKELE-002', 'Black Electric Kettle', 'Equipment', 'General Work Section'),
    ('STZ-RTR-001', 'Router', 'Equipment', 'General Work Section'),
    ('STZ-CMIDE-001', 'A/C Midea', 'Equipment', 'General Work Section'),
    ('STZ-WINBLD-001', 'Window Blind', 'Other', 'General Work Section'),
    ('STZ-OFFLGT-001', 'Office LED Light (100W)', 'Equipment', 'General Work Section'),
    ('STZ-OFFLGT-002', 'Office LED Light (100W)', 'Equipment', 'General Work Section'),
    ('STZ-CMIDE-002', 'A/C Midea', 'Equipment', 'General Work Section'),
    ('STZ-ERGCH-008', 'Ergonomic Chair', 'Furniture', 'Account Office 1'),
    ('STZ-ERGCH-009', 'Ergonomic Chair', 'Furniture', 'Account Office 1'),
    ('STZ-ERGCH-010', 'Ergonomic Chair', 'Furniture', 'Account Office 1'),
    ('STZ-FILECAB-002', 'File Cabinet', 'Furniture', 'Account Office 1'),
    ('STZ-FILECAB-003', 'File Cabinet', 'Furniture', 'Account Office 1'),
    ('STZ-FILECAB-004', 'File Cabinet', 'Furniture', 'Account Office 1'),
    ('STZ-CMIDE-003', 'A/C Midea', 'Equipment', 'Account Office 1'),
    ('STZ-WORKTBL-001', 'Working Table', 'Furniture', 'Account Office 1'),
    ('STZ-WORKTBL-002', 'Working Table', 'Furniture', 'Account Office 1'),
    ('STZ-WORKTBL-003', 'Working Table', 'Furniture', 'AGM Office'),
    ('STZ-ERGCH-011', 'Ergonomic Chair', 'Furniture', 'AGM Office'),
    ('STZ-VISCH-001', 'Visitors Chair', 'Furniture', 'AGM Office'),
    ('STZ-CLG-001', 'A/C LG', 'Equipment', 'AGM Office'),
    ('STZ-LEDLGT-001', 'LED Light', 'Equipment', 'AGM Office'),
    ('STZ-FILECABI-001', 'File Cabinet', 'Furniture', 'AGM Office'),
    ('STZ-TBLCABI-001', 'Table Cabinet', 'Furniture', 'AGM Office'),
    ('STZ-GRNFLR-001', 'Green Flower Pot', 'Furniture', 'AGM Office'),
    ('STZ-WINBLD-002', 'Window Blind', 'Other', 'AGM Office'),
    ('STZ-OFFTBL-001', 'Office Table', 'Furniture', 'Account Office 2'),
    ('STZ-OFFTBL-002', 'Office Table', 'Furniture', 'Account Office 2'),
    ('STZ-OFFTBL-003', 'Office Table', 'Furniture', 'Account Office 2'),
    ('STZ-TBLFILE-001', 'Table File Cabinet', 'Furniture', 'Account Office 2'),
    ('STZ-TBLFILE-002', 'Table File Cabinet', 'Furniture', 'Account Office 2'),
    ('STZ-TBLFILE-003', 'Table File Cabinet', 'Furniture', 'Account Office 2'),
    ('STZ-ERGCH-012', 'Ergonomic Chair', 'Furniture', 'Account Office 2'),
    ('STZ-ERGCH-013', 'Ergonomic Chair', 'Furniture', 'Account Office 2'),
    ('STZ-ERGCH-014', 'Ergonomic Chair', 'Furniture', 'Account Office 2'),
    ('STZ-VISCH-002', 'Visitors Chair', 'Furniture', 'Account Office 2'),
    ('STZ-CSKYR-001', 'A/C Skyrun', 'Equipment', 'Account Office 2'),
    ('STZ-WINBLD-003', 'Window Blind', 'Other', 'Account Office 2'),
    ('STZ-WINBLD-004', 'Window Blind', 'Other', 'Account Office 2'),
    ('STZ-WASTBIN-001', 'Waste Bin', 'Furniture', 'Account Office 2'),
    ('STZ-RTR-002', 'Router', 'Equipment', 'Account Office 2'),
    ('STZ-CABLOCK-001', 'Cabinet/Locker', 'Furniture', 'Account Office 2'),
    ('STZ-LEDLGT-002', 'LED Light', 'Equipment', 'Account Office 2'),
    ('STZ-LEDLGT-003', 'LED Light', 'Equipment', 'Account Office 2'),
    ('STZ-ERGOCH-001', 'Ergonomic Chair', 'Furniture', 'Legal/Office'),
    ('STZ-VISCH-003', 'Visitors Chair', 'Furniture', 'Legal/Office'),
    ('STZ-CSKYR-002', 'A/C Skyrun', 'Equipment', 'Legal/Office'),
    ('STZ-FILECAB-005', 'File Cabinet', 'Furniture', 'Legal/Office'),
    ('STZ-SCU-001', 'Sculpture', 'Other', 'Legal/Office'),
    ('STZ-WINBLD-005', 'Window Blind', 'Other', 'Legal/Office'),
    ('STZ-ERGCH-015', 'Ergonomic Chair', 'Furniture', 'Internal Audit Office'),
    ('STZ-VISCH-004', 'Visitors Chair', 'Furniture', 'Internal Audit Office'),
    ('STZ-CMIDE-004', 'A/C Midea', 'Equipment', 'Internal Audit Office'),
    ('STZ-FILECARB-001', 'File Cabinet', 'Furniture', 'Internal Audit Office'),
    ('STZ-OFFTABL-001', 'Office Table', 'Furniture', 'Internal Audit Office'),
    ('STZ-TBLCARB-001', 'Table Cabinet', 'Furniture', 'Internal Audit Office'),
    ('STZ-SCU-002', 'Sculpture', 'Other', 'Internal Audit Office'),
    ('STZ-RTR-003', 'Router', 'Equipment', 'Internal Audit Office'),
    ('STZ-WSTBIN-001', 'Waste Bin', 'Furniture', 'Internal Audit Office'),
    ('STZ-TBLWRK-001', 'Table Workstation', 'Furniture', 'Opt/Tech'),
    ('STZ-OFFTBL-004', 'Office Table', 'Furniture', 'Opt/Tech'),
    ('STZ-OFFTBL-005', 'Office Table', 'Furniture', 'Opt/Tech'),
    ('STZ-ERGCH-016', 'Ergonomic Chair', 'Furniture', 'Opt/Tech'),
    ('STZ-ERGCH-017', 'Ergonomic Chair', 'Furniture', 'Opt/Tech'),
    ('STZ-ERGCH-018', 'Ergonomic Chair', 'Furniture', 'Opt/Tech'),
    ('STZ-ERGCH-019', 'Ergonomic Chair', 'Furniture', 'Opt/Tech'),
    ('STZ-ERGCH-020', 'Ergonomic Chair', 'Furniture', 'Opt/Tech'),
    ('STZ-ERGCH-021', 'Ergonomic Chair', 'Furniture', 'Opt/Tech'),
    ('STZ-ERGCH-022', 'Ergonomic Chair', 'Furniture', 'Opt/Tech'),
    ('STZ-ERGCH-023', 'Ergonomic Chair', 'Furniture', 'Opt/Tech'),
    ('STZ-VISCH-005', 'Visitors Chair', 'Furniture', 'Opt/Tech'),
    ('STZ-TBLFILE-004', 'Table File Cabinet', 'Furniture', 'Opt/Tech'),
    ('STZ-CLG-002', 'A/C (LG)', 'Equipment', 'Opt/Tech'),
    ('STZ-PRVWRK-001', 'Private Workstation', 'Other', 'Opt/Tech'),
    ('STZ-PRVWRK-002', 'Private Workstation', 'Other', 'Opt/Tech'),
    ('STZ-SCU-003', 'Sculpture', 'Other', 'Opt/Tech'),
    ('STZ-WSTBIN-002', 'Waste Bin', 'Furniture', 'Opt/Tech'),
    ('STZ-LEDW-001', 'LED Light (36W)', 'Equipment', 'Opt/Tech'),
    ('STZ-LEDW-002', 'LED Light (36W)', 'Equipment', 'Opt/Tech'),
    ('STZ-LEDW-003', 'LED Light (36W)', 'Equipment', 'Opt/Tech'),
    ('STZ-LEDW-004', 'LED Light (36W)', 'Equipment', 'Opt/Tech'),
    ('STZ-WINBLD-006', 'Window Blind', 'Other', 'Opt/Tech'),
    ('STZ-WINBLD-007', 'Window Blind', 'Other', 'Opt/Tech'),
    ('STZ-WINBLD-008', 'Window Blind', 'Other', 'Opt/Tech'),
    ('STZ-CUSHCH-001', 'Cushion Chair', 'Furniture', 'MD/Secretary Office'),
    ('STZ-OFFTBL-006', 'Office Table', 'Furniture', 'MD/Secretary Office'),
    ('STZ-OFFTBL-007', 'Office Table', 'Furniture', 'MD/Secretary Office'),
    ('STZ-CABI-001', 'Cabinet', 'Furniture', 'MD/Secretary Office'),
    ('STZ-CABI-002', 'Cabinet', 'Furniture', 'MD/Secretary Office'),
    ('STZ-ERGCH-024', 'Ergonomic Chair', 'Furniture', 'MD/Secretary Office'),
    ('STZ-ERGCH-025', 'Ergonomic Chair', 'Furniture', 'MD/Secretary Office'),
    ('STZ-WSTBIN-003', 'Waste Bin', 'Furniture', 'MD/Secretary Office'),
    ('STZ-WSTBIN-004', 'Waste Bin', 'Furniture', 'MD/Secretary Office'),
    ('STZ-WINBLD-009', 'Window Blind', 'Other', 'MD/Secretary Office'),
    ('STZ-TV-002', 'Television', 'Equipment', 'MD/Secretary Office'),
    ('STZ-CSKYR-003', 'A/C (Skyrun)', 'Equipment', 'MD/Secretary Office'),
    ('STZ-PHCPMC-001', 'Photocopy Machine', 'Equipment', 'MD/Secretary Office'),
    ('STZ-SDTBL-002', 'Side Table', 'Furniture', 'MD/Secretary Office'),
    ('STZ-FILECABI-002', 'File Cabinet', 'Furniture', 'MD Office'),
    ('STZ-FILECABI-003', 'File Cabinet', 'Furniture', 'MD Office'),
    ('STZ-TV-003', 'Television', 'Equipment', 'MD Office'),
    ('STZ-TVSTND-001', 'Television Stand', 'Furniture', 'MD Office'),
    ('STZ-FLRVAS-001', 'Flower Vase', 'Furniture', 'MD Office'),
    ('STZ-CUSHCH-002', 'Cushion Chair', 'Furniture', 'MD Office'),
    ('STZ-SDTBL-003', 'Side Table', 'Furniture', 'MD Office'),
    ('STZ-SDTBL-004', 'Side Table', 'Furniture', 'MD Office'),
    ('STZ-ERGCH-026', 'Ergonomic Chair', 'Furniture', 'MD Office'),
    ('STZ-ERGCH-027', 'Ergonomic Chair', 'Furniture', 'MD Office'),
    ('STZ-ERGCH-028', 'Ergonomic Chair', 'Furniture', 'MD Office'),
    ('STZ-OFFWORK-001', 'Office Working Table', 'Furniture', 'MD Office'),
    ('STZ-BEHITBL-001', 'Behind Table Cabinet', 'Furniture', 'MD Office'),
    ('STZ-CLG-003', 'A/C LG & Midea', 'Equipment', 'MD Office'),
    ('STZ-CLG-004', 'A/C LG & Midea', 'Equipment', 'MD Office'),
    ('STZ-CLG-005', 'A/C LG & Midea', 'Equipment', 'MD Office'),
    ('STZ-WC-001', 'W/C (Rest Room)', 'Other', 'MD Office'),
    ('STZ-WST-001', 'Waste Bin', 'Other', 'MD Office'),
    ('STZ-WNECARB-001', 'Wine Cabinet', 'Furniture', 'MD Office'),
    ('STZ-MIR-001', 'Mirror', 'Other', 'MD Office'),
    ('STZ-WSHHND-001', 'Hand Wash Basin', 'Other', 'MD Office'),
    ('STZ-CUSHCH-003', 'Cushion Chair', 'Furniture', 'MD Office'),
    ('STZ-CUSHCH-004', 'Cushion Chair', 'Furniture', 'MD Office'),
    ('STZ-CUSHCH-005', 'Cushion Chair', 'Furniture', 'MD Office'),
    ('STZ-CSKYR-004', 'A/C Skyrun', 'Equipment', 'MD Office'),
    ('STZ-SMKDET-001', 'Smoke Detector', 'Equipment', 'MD Office'),
    ('STZ-CAB-001', 'Cabinet', 'Furniture', 'Boardroom'),
    ('STZ-CAB-002', 'Cabinet', 'Furniture', 'Boardroom'),
    ('STZ-CAB-003', 'Cabinet', 'Furniture', 'Boardroom'),
    ('STZ-CLG-006', 'A/C LG & Midea', 'Equipment', 'Boardroom'),
    ('STZ-CLG-007', 'A/C LG & Midea', 'Equipment', 'Boardroom'),
    ('STZ-FLRVAS-002', 'Flower Vase', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-029', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-030', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-031', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-032', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-033', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-034', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-035', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-036', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-037', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-038', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-ERGCH-039', 'Ergonomic Chair', 'Furniture', 'Boardroom'),
    ('STZ-CNFTBL-001', 'Conference Table', 'Furniture', 'Boardroom'),
    ('STZ-WSTBIN-005', 'Waste Bin', 'Furniture', 'Boardroom'),
    ('STZ-TV-004', 'Television', 'Equipment', 'Boardroom'),
    ('STZ-WHILMKR-001', 'Whiteboard', 'Furniture', 'Boardroom'),
    ('STZ-SCU-004', 'Sculpture', 'Other', 'Boardroom'),
    ('STZ-SCU-005', 'Sculpture', 'Other', 'Boardroom'),
    ('STZ-SCU-006', 'Sculpture', 'Other', 'Boardroom'),
    ('STZ-SCU-007', 'Sculpture', 'Other', 'Boardroom'),
    ('STZ-SCU-008', 'Sculpture', 'Other', 'Boardroom'),
    ('STZ-SCU-009', 'Sculpture', 'Other', 'Boardroom'),
    ('STZ-ITCTEL-001', 'Intercom Telephone', 'Equipment', 'Boardroom'),
    ('STZ-LEDLGT-004', 'LED Light', 'Equipment', 'Boardroom'),
    ('STZ-LEDLGT-005', 'LED Light', 'Equipment', 'Boardroom'),
    ('STZ-LEDLGT-006', 'LED Light', 'Equipment', 'Boardroom'),
    ('STZ-LEDLGT-007', 'LED Light', 'Equipment', 'Boardroom'),
    ('STZ-SMKDET-002', 'Smoke Detector', 'Equipment', 'Boardroom'),
    ('STZ-WINBLD-010', 'Window Blind', 'Other', 'Boardroom'),
    ('STZ-WINBLD-011', 'Window Blind', 'Other', 'Boardroom'),
    ('STZ-OFFTBL-008', 'Office Table', 'Furniture', 'Bus/Dev Office'),
    ('STZ-OFFTBL-009', 'Office Table', 'Furniture', 'Bus/Dev Office'),
    ('STZ-ERGCH-040', 'Ergonomic Chair', 'Furniture', 'Bus/Dev Office'),
    ('STZ-ERGCH-041', 'Ergonomic Chair', 'Furniture', 'Bus/Dev Office'),
    ('STZ-CAB-004', 'Cabinet', 'Furniture', 'Bus/Dev Office'),
    ('STZ-C-001', 'A/C', 'Equipment', 'Bus/Dev Office'),
    ('STZ-WINBLD-012', 'Window Blind', 'Other', 'Bus/Dev Office'),
    ('STZ-ERGCH-042', 'Ergonomic Chair', 'Furniture', 'COO Office'),
    ('STZ-VISCH-006', 'Visitors Chair', 'Furniture', 'COO Office'),
    ('STZ-VISCH-007', 'Visitors Chair', 'Furniture', 'COO Office'),
    ('STZ-OFFTBL-010', 'Office Table', 'Furniture', 'COO Office'),
    ('STZ-CAB-005', 'Cabinet', 'Furniture', 'COO Office'),
    ('STZ-CUSHCH-006', 'Cushion Chair', 'Furniture', 'COO Office'),
    ('STZ-CUSHCH-007', 'Cushion Chair', 'Furniture', 'COO Office'),
    ('STZ-SDTBL-005', 'Side Table', 'Furniture', 'COO Office'),
    ('STZ-TBLCAB-001', 'Table Cabinet', 'Furniture', 'COO Office'),
    ('STZ-SCU-010', 'Sculpture', 'Other', 'COO Office'),
    ('STZ-SCU-011', 'Sculpture', 'Other', 'COO Office'),
    ('STZ-SCU-012', 'Sculpture', 'Other', 'COO Office'),
    ('STZ-SCU-013', 'Sculpture', 'Other', 'COO Office'),
    ('STZ-SCU-014', 'Sculpture', 'Other', 'COO Office'),
    ('STZ-SCU-015', 'Sculpture', 'Other', 'COO Office'),
    ('STZ-TELE-001', 'Television', 'Other', 'COO Office'),
    ('STZ-C-002', 'A/C', 'Equipment', 'COO Office'),
    ('STZ-OFFTBL-011', 'Office Table', 'Furniture', 'CFO Office'),
    ('STZ-SDTBL-006', 'Side Table', 'Furniture', 'CFO Office'),
    ('STZ-ERGCH-043', 'Ergonomic Chair', 'Furniture', 'CFO Office'),
    ('STZ-VISCHAI-001', 'Visitors Chair', 'Furniture', 'CFO Office'),
    ('STZ-VISCHAI-002', 'Visitors Chair', 'Furniture', 'CFO Office'),
    ('STZ-TEATBL-001', 'Tea Table', 'Furniture', 'CFO Office'),
    ('STZ-TV-005', 'Television', 'Equipment', 'CFO Office'),
    ('STZ-CAB-006', 'Cabinet', 'Furniture', 'CFO Office'),
    ('STZ-FLRVAS-003', 'Flower Vase', 'Furniture', 'CFO Office'),
    ('STZ-WINBLD-013', 'Window Blind', 'Other', 'CFO Office'),
    ('STZ-SCU-016', 'Sculpture', 'Other', 'CFO Office'),
    ('STZ-SCU-017', 'Sculpture', 'Other', 'CFO Office'),
    ('STZ-SCU-018', 'Sculpture', 'Other', 'CFO Office'),
    ('STZ-EATTBL-001', 'Eating Table', 'Furniture', 'Kitchen'),
    ('STZ-WDLNG-001', 'Wooden Long Chair', 'Furniture', 'Kitchen'),
    ('STZ-WDLNG-002', 'Wooden Long Chair', 'Furniture', 'Kitchen'),
    ('STZ-WDLNG-003', 'Wooden Long Chair', 'Furniture', 'Kitchen'),
    ('STZ-WALCABI-001', 'Wall Cabinet', 'Furniture', 'Kitchen'),
    ('STZ-C-003', 'A/C', 'Equipment', 'Kitchen'),
    ('STZ-STDFRDG-001', 'Standing fridge', 'Furniture', 'Kitchen'),
    ('STZ-MW-001', 'Microwave', 'Equipment', 'Kitchen'),
    ('STZ-WSTBIN-006', 'Waste Bin', 'Furniture', 'Kitchen'),
    ('STZ-ELEKTL-003', 'Electric Kettle', 'Equipment', 'Kitchen'),
    ('STZ-BRDTST-001', 'Bread Toaster', 'Equipment', 'Kitchen'),
    ('STZ-FIREEXT-001', 'Fire Extinguisher', 'Equipment', 'Kitchen'),
    ('STZ-WINBLD-014', 'Window Blind', 'Other', 'Kitchen'),
    ('STZ-WTRTANK-001', 'Water Tank', 'Other', 'GP'),
]


def run():
    init_db(seed=True)
    conn = get_db()

    loc_ids = {}
    for row in conn.execute("SELECT id, name FROM locations"):
        loc_ids[row["name"]] = row["id"]

    existing = {}
    for row in conn.execute("SELECT asset_tag, name FROM assets"):
        existing[row["asset_tag"]] = row["name"]

    inserted, updated, unchanged, missing_loc = 0, 0, 0, set()

    for asset_tag, name, category, loc_name in ASSETS:
        location_id = loc_ids.get(loc_name)
        if location_id is None:
            missing_loc.add(loc_name)

        if asset_tag not in existing:
            conn.execute(
                """INSERT INTO assets
                   (asset_tag, name, category, location_id, condition, status)
                   VALUES (?, ?, ?, ?, 'Good', 'Available')""",
                (asset_tag, name, category, location_id),
            )
            inserted += 1
        elif existing[asset_tag] != name:
            # Already imported, but the name differs from this reference list
            # (e.g. a spelling fix) -- bring it up to date.
            conn.execute(
                "UPDATE assets SET name = ? WHERE asset_tag = ?",
                (name, asset_tag),
            )
            updated += 1
        else:
            unchanged += 1

    conn.commit()
    conn.close()

    print(f"Inserted (new): {inserted}")
    print(f"Updated (name corrected): {updated}")
    print(f"Already up to date: {unchanged}")
    if missing_loc:
        print(f"WARNING - locations not found in DB: {missing_loc}")
    print()
    print("Note: this script keeps asset names in sync with this list.")
    print("If you've manually renamed an asset inside the app since importing,")
    print("re-running this script will overwrite that name back to the list above.")


if __name__ == "__main__":
    run()