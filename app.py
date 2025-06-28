import pandas as pd
import streamlit as st
from io import BytesIO

st.set_page_config(page_title="PO–SO Matcher", layout="centered")

st.title("📦 Purchase to Sales Order Assignment Tool")
st.markdown("Match **Sales Orders** to **Purchase Orders** using FIFO logic and **Location**.")

# File Uploads
po_file = st.file_uploader("📁 Upload Purchase Orders CSV", type="csv")
so_file = st.file_uploader("📁 Upload Sales Orders CSV", type="csv")

# Main assignment function
def assign_pos(po_df, so_df):
    po_df['PO ID'] = po_df.index
    so_df['SO ID'] = so_df.index
    po_df.sort_values(by='PO ID', inplace=True)

    remaining_po = {}
    for _, row in po_df.iterrows():
        key = (row['Item Code'], row['Location'], row['PO Number'])
        remaining_po[key] = row['Quantity']

    assignments = []

    for _, so in so_df.iterrows():
        item = so['Item Code']
        qty_needed = so['Quantity']
        so_number = so['SO Number']
        location = so['Location']

        for (po_item, po_location, po_number), po_qty in list(remaining_po.items()):
            if item == po_item and location == po_location and qty_needed > 0 and po_qty > 0:
                qty_assigned = min(po_qty, qty_needed)

                assignments.append({
                    'Item Code': item,
                    'Location': location,
                    'SO Number': so_number,
                    'PO Number': po_number,
                    'Quantity Assigned': qty_assigned
                })

                remaining_po[(po_item, po_location, po_number)] -= qty_assigned
                qty_needed -= qty_assigned

                if qty_needed <= 0:
                    break

    assigned_df = pd.DataFrame(assignments)

    free_to_sell = []
    for (item, location, po), remaining_qty in remaining_po.items():
        if remaining_qty > 0:
            free_to_sell.append({
                'Item Code': item,
                'Location': location,
                'PO Number': po,
                'Free Quantity': remaining_qty
            })
    free_df = pd.DataFrame(free_to_sell)
    return assigned_df, free_df

# Convert to Excel
def convert_to_excel(df1, df2):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df1.to_excel(writer, sheet_name='Assigned', index=False)
        df2.to_excel(writer, sheet_name='Free To Sell', index=False)
    output.seek(0)
    return output

# Run when both files are uploaded
if po_file and so_file:
    po_df = pd.read_csv(po_file)
    so_df = pd.read_csv(so_file)

    try:
        assigned_df, free_df = assign_pos(po_df, so_df)

        st.success("✅ Assignment Complete!")

        st.subheader("🔗 Sample of Assigned Pairs")
        st.dataframe(assigned_df.head(10))

        excel_data = convert_to_excel(assigned_df, free_df)
        st.download_button("📥 Download Results as Excel",
                           data=excel_data,
                           file_name="po_so_assignment.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("Upload both CSV files to begin.")
