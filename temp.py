import dearpygui.dearpygui as dpg
import csv

dpg.create_context()

def save_table_to_file(sender, app_data, user_data):
    """Saves DPG table data to a .csv or .txt file"""
    table_id, file_type = user_data  # Unpack table ID and file type



    # Get table columns (headers)
    column_children = dpg.get_item_children(table_id, slot=0)
    
    if column_children and isinstance(column_children, list):  # Ensure it's a list
        headers = [dpg.get_item_label(col) for col in column_children]
        for col in column_children: print(col)

    else:
        headers = []  # No columns found


    # Get table rows (data)
    rows = []
    row_children = dpg.get_item_children(table_id, slot=1)
    if row_children and isinstance(row_children, list):
        for row in row_children:  
            cell_children = dpg.get_item_children(row, slot=1)
            if cell_children and isinstance(cell_children, list):
                row_data = [dpg.get_value(cell) for cell in cell_children]
                print("Row Data:", row_data)  # Debugging
                rows.append(row_data)


    # Save to CSV or TXT
    filename = f"table_data.{file_type}"
    if file_type == "csv":
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            if headers:
                writer.writerow(headers)  # Write headers
            writer.writerows(rows)  # Write data
    else:
        with open(filename, mode="w") as file:
            if headers:
                file.write("\t".join(headers) + "\n")  # Tab-separated headers
            for row in rows:
                file.write("\t".join(map(str, row)) + "\n")  # Tab-separated values

    print(f"Table saved as {filename}")

# Example Table
with dpg.window(label="Table Example"):
    with dpg.table(header_row=True) as table_id:
        dpg.add_table_column(label="Column 1")  # FIXED: No 'with' needed
        dpg.add_table_column(label="Column 2")

        with dpg.table_row():
            dpg.add_text("Data 1")
            dpg.add_text("Data 2")

        with dpg.table_row():
            dpg.add_text("Data 3")
            dpg.add_text("Data 4")

    dpg.add_button(label="Save as CSV", callback=save_table_to_file, user_data=(table_id, "csv"))
    dpg.add_button(label="Save as TXT", callback=save_table_to_file, user_data=(table_id, "txt"))

dpg.create_viewport(title='DPG Table Save Example', width=600, height=400)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
