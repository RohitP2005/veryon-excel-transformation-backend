"""Generates sample "customer-style" Excel workbooks for each built-in template.

These are intentionally messy/varied compared to the template's destination columns (different
header names, split address fields, etc.) so the mapping screen has something real to map. Output
is written into the frontend's public/samples/ folder so it can be served statically and linked
from the Upload Excel step ("Download a sample file to try this out").

Run: python scripts/generate_sample_files.py
"""
from pathlib import Path

from openpyxl import Workbook

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "veryon-sheet-sorter" / "public" / "samples"

SAMPLES: dict[str, tuple[list[str], list[list[object]]]] = {
    "customer_import_sample.xlsx": (
        ["ID", "Full Name", "Mail", "Phone Number", "Addr1", "Addr2", "Nation"],
        [
            [1, "Alice Johnson", "alice.johnson@example.com", "555-0101", "1 Main St", "Suite 5", "USA"],
            [2, "Bruno Silva", "bruno.silva@example.com", "555-0102", "22 Oak Ave", "", "Canada"],
            [3, "Chen Wei", "chen.wei@example.com", "555-0103", "8 River Rd", "Apt 3B", "Singapore"],
            [4, "Dana Kim", "dana.kim@example.com", "555-0104", "400 Pine Blvd", "", "South Korea"],
            [5, "Emeka Obi", "emeka.obi@example.com", "555-0105", "17 Palm Cres", "Unit 2", "Nigeria"],
        ],
    ),
    "inventory_sample.xlsx": (
        ["Item Code", "Item Name", "Qty On Hand", "Cost Per Unit", "Location"],
        [
            ["SKU-1001", "Hydraulic Hose 3/8in", 120, 8.50, "Warehouse A"],
            ["SKU-1002", "Turbine Bearing Kit", 35, 145.00, "Warehouse B"],
            ["SKU-1003", "Cabin Air Filter", 80, 22.75, "Warehouse A"],
            ["SKU-1004", "Landing Gear Bushing", 60, 61.20, "Warehouse C"],
            ["SKU-1005", "Avionics Fuse 5A", 500, 1.35, "Warehouse A"],
        ],
    ),
    "employee_sample.xlsx": (
        ["Emp No", "Name", "Dept", "Email Address", "Start Date"],
        [
            ["E-001", "Fatima Noor", "Engineering", "fatima.noor@example.com", "2022-03-14T00:00:00"],
            ["E-002", "George Papas", "Maintenance", "george.papas@example.com", "2021-07-01T00:00:00"],
            ["E-003", "Hana Sato", "Quality Assurance", "hana.sato@example.com", "2023-01-09T00:00:00"],
            ["E-004", "Ivan Petrov", "Logistics", "ivan.petrov@example.com", "2020-11-23T00:00:00"],
            ["E-005", "Julia Novak", "Engineering", "julia.novak@example.com", "2024-05-06T00:00:00"],
        ],
    ),
    "supplier_sample.xlsx": (
        ["Vendor Code", "Vendor Name", "Email", "Telephone", "Street", "Nation"],
        [
            ["V-100", "Atlas Components Ltd", "sales@atlascomp.example", "+44-20-5550100", "12 Kings Rd", "United Kingdom"],
            ["V-101", "Meridian Aero Supply", "orders@meridianaero.example", "+1-214-5550101", "900 Skyway Dr", "USA"],
            ["V-102", "NordFast Fasteners", "info@nordfast.example", "+46-8-5550102", "5 Storgatan", "Sweden"],
            ["V-103", "Pacific Rim Parts", "contact@pacificrim.example", "+81-3-5550103", "3-1 Ginza", "Japan"],
        ],
    ),
    "aircraft_parts_sample.xlsx": (
        ["Part No", "Description", "Maker", "Cond", "Qty", "Cost Each"],
        [
            ["AP-2001", "Fuel Pump Assembly", "Boeing", "New", 4, 1250.00],
            ["AP-2002", "Nose Gear Actuator", "Airbus", "Overhauled", 2, 3400.00],
            ["AP-2003", "Cockpit Display Unit", "Honeywell", "New", 6, 980.50],
            ["AP-2004", "Wing Flap Track Roller", "Boeing", "Serviceable", 12, 145.75],
            ["AP-2005", "APU Starter Motor", "Pratt & Whitney", "Overhauled", 3, 2670.00],
        ],
    ),
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, (headers, rows) in SAMPLES.items():
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for row in rows:
            ws.append(row)
        for col_idx, header in enumerate(headers, start=1):
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = max(
                14, len(header) + 2
            )
        output_path = OUTPUT_DIR / filename
        wb.save(output_path)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
