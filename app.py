import streamlit as st
import pandas as pd
import json
import hashlib
import datetime
from datetime import date
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np
import os
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials

# Page configuration
st.set_page_config(
    page_title="Alumex Gate Pass System",
    page_icon="📋",
    layout="centered"
)

# Google Sheets setup
def setup_google_sheets():
    try:
        # Use Streamlit secrets for credentials
        if 'gcp_service_account' in st.secrets:
            creds_dict = dict(st.secrets['gcp_service_account'])
            # Convert the private key string to actual newlines
            if 'private_key' in creds_dict:
                creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            creds = Credentials.from_service_account_info(creds_dict)
        else:
            st.error("Google Sheets credentials not found in secrets.")
            return None
        
        client = gspread.authorize(creds)
        
        # Try to open existing sheet or create new one
        try:
            sheet = client.open("Alumex_Gate_Passes").sheet1
            st.success("✅ Connected to Google Sheets successfully!")
        except gspread.SpreadsheetNotFound:
            # Create new spreadsheet if it doesn't exist
            spreadsheet = client.create("Alumex_Gate_Passes")
            sheet = spreadsheet.sheet1
            
            # Set up headers
            headers = [
                "Reference", "Requested_By", "Send_To", "Purpose", 
                "Return_Date", "Dispatch_Type", "Vehicle_Number",
                "Items_JSON", "Certified_Signature", "Authorized_Signature",
                "Received_Signature", "Status", "Created_Date", "Completed_Date"
            ]
            sheet.append_row(headers)
            st.success("✅ Created new Google Sheet: Alumex_Gate_Passes")
        
        return sheet
    except Exception as e:
        st.error(f"Error setting up Google Sheets: {str(e)}")
        return None

# Initialize Google Sheets
gate_pass_sheet = setup_google_sheets()

# Header
st.markdown("<h1 style='text-align: center; font-size: 16px;'>Advice Dispatch Gate Pass</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; font-size: 14px;'>Alumex Group</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Sapugaskanda, Makola</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Tel: 2400332,2400333,2400421</p>", unsafe_allow_html=True)

st.markdown("---")

# Function to generate reference number
def generate_reference(data):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    hash_input = f"{data['requested_by']}{timestamp}"
    return f"GP{hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()}"

# Function to save gate pass to Google Sheets
def save_gate_pass(data):
    try:
        if gate_pass_sheet is None:
            st.error("Google Sheets not initialized")
            return False
        
        # Convert items to JSON string
        items_json = json.dumps(data['items'])
        
        # Prepare row data
        row_data = [
            data['reference'],
            data['requested_by'],
            data['send_to'],
            data['purpose'],
            data.get('return_date', ''),
            data['dispatch_type'],
            data.get('vehicle_number', ''),
            items_json,
            data.get('certified_signature', ''),
            data.get('authorized_signature', ''),
            data.get('received_signature', ''),
            'pending',
            datetime.datetime.now().isoformat(),
            ''  # Completed date (empty for now)
        ]
        
        # Append to Google Sheet
        gate_pass_sheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"Error saving gate pass: {e}")
        return False

# Function to get gate pass by reference from Google Sheets
def get_gate_pass(reference):
    try:
        if gate_pass_sheet is None:
            return None
        
        # Get all records
        records = gate_pass_sheet.get_all_records()
        
        # Find the record with matching reference
        for record in records:
            if record['Reference'] == reference:
                return {
                    'reference': record['Reference'],
                    'requested_by': record['Requested_By'],
                    'send_to': record['Send_To'],
                    'purpose': record['Purpose'],
                    'return_date': record['Return_Date'],
                    'dispatch_type': record['Dispatch_Type'],
                    'vehicle_number': record['Vehicle_Number'],
                    'items': json.loads(record['Items_JSON']),
                    'certified_signature': record['Certified_Signature'],
                    'authorized_signature': record['Authorized_Signature'],
                    'received_signature': record['Received_Signature'],
                    'status': record['Status'],
                    'created_date': record['Created_Date']
                }
        return None
    except Exception as e:
        st.error(f"Error retrieving gate pass: {e}")
        return None

# Function to update signatures in Google Sheets
def update_signatures(reference, certified_sig, authorized_sig, received_sig, vehicle_no):
    try:
        if gate_pass_sheet is None:
            return False
        
        # Get all records
        records = gate_pass_sheet.get_all_records()
        
        # Find the row index
        for i, record in enumerate(records):
            if record['Reference'] == reference:
                # Update the row (add 2 because of header and 1-based indexing)
                row_num = i + 2
                
                gate_pass_sheet.update_cell(row_num, 9, certified_sig)  # Certified Signature
                gate_pass_sheet.update_cell(row_num, 10, authorized_sig)  # Authorized Signature
                gate_pass_sheet.update_cell(row_num, 11, received_sig)  # Received Signature
                gate_pass_sheet.update_cell(row_num, 7, vehicle_no)  # Vehicle Number
                gate_pass_sheet.update_cell(row_num, 12, 'completed')  # Status
                gate_pass_sheet.update_cell(row_num, 14, datetime.datetime.now().isoformat())  # Completed Date
                
                return True
        return False
    except Exception as e:
        st.error(f"Error updating signatures: {e}")
        return False

# Function to create PDF gate pass in A4 size with footer
def create_gate_pass_pdf(gate_pass_data):
    # Create PDF class with footer
    class PDFWithFooter(FPDF):
        def footer(self):
            # Position at 1.5 cm from bottom
            self.set_y(-15)
            # Set font
            self.set_font('Arial', 'I', 9)
            # Add generated date and time
            current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Page number and generation info
            self.cell(0, 10, f'Generated on: {current_date} | Page {self.page_no()}', 0, 0, 'C')
    
    pdf = PDFWithFooter(format='A4')
    pdf.add_page()
    
    # Set margins for A4
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 10, "ADVICE DISPATCH GATE PASS", ln=True, align='C')
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 8, "ALUMEX GROUP", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 6, "Sapugaskanda, Makola", ln=True, align='C')
    pdf.cell(0, 6, "Tel: 2400332,2400333,2400421", ln=True, align='C')
    
    pdf.ln(8)
    
    # Reference Number
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"Reference: {gate_pass_data['reference']}", ln=True, align='L')
    pdf.ln(5)
    
    # Horizontal line separator
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    # Basic Information Section
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "BASIC INFORMATION", ln=True, align='L')
    pdf.set_font("Arial", size=11)
    
    info_data = [
        ("Requested by:", gate_pass_data['requested_by']),
        ("Send to:", gate_pass_data['send_to']),
        ("Purpose:", gate_pass_data['purpose']),
        ("Return Date:", gate_pass_data.get('return_date', 'Not specified')),
        ("Dispatch Type:", gate_pass_data['dispatch_type']),
        ("Vehicle Number:", gate_pass_data.get('vehicle_number', ''))
    ]
    
    for label, value in info_data:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(45, 7, label, 0, 0)
        pdf.set_font("Arial", size=11)
        
        # Handle multi-line text
        if len(str(value)) > 60:  # If text is too long, use multi_cell
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(0, 7, str(value))
            pdf.ln(2)
        else:
            pdf.cell(0, 7, str(value), ln=True)
    
    pdf.ln(8)
    
    # Horizontal line separator
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    # Items Table Section
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "ITEMS DISPATCH DETAILS", ln=True, align='L')
    pdf.ln(5)
    
    # Table headers
    pdf.set_font("Arial", 'B', 11)
    col_widths = [20, 100, 30, 35]  # Adjusted for A4 width
    headers = ["Qty", "Description", "Value", "Invoice No"]
    
    # Draw table header with borders
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()
    
    # Table rows
    pdf.set_font("Arial", size=10)
    for item in gate_pass_data['items']:
        # Quantity
        pdf.cell(col_widths[0], 8, str(item.get('Quantity', '')), 1, 0, 'C')
        
        # Description (handle long text)
        desc = str(item.get('Description', ''))
        if len(desc) > 40:
            desc = desc[:37] + "..."
        pdf.cell(col_widths[1], 8, desc, 1, 0, 'L')
        
        # Total Value
        pdf.cell(col_widths[2], 8, str(item.get('Total Value', '')), 1, 0, 'C')
        
        # Invoice No
        pdf.cell(col_widths[3], 8, str(item.get('Invoice No', '')), 1, 0, 'C')
        pdf.ln()
    
    pdf.ln(12)
    
    # Horizontal line separator
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    # Signatures section
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "AUTHORIZATIONS & SIGNATURES", ln=True, align='C')
    pdf.ln(8)
    
    # Signature boxes - COMPLETE BORDERS
    col_width = 55
    spacing = 10
    start_x = 15
    
    signatures = [
        ("CERTIFIED BY", "Certifying Officer", gate_pass_data.get('certified_signature')),
        ("AUTHORIZED BY", "Authorizing Manager", gate_pass_data.get('authorized_signature')),
        ("RECEIVED BY", "Receiving Party", gate_pass_data.get('received_signature'))
    ]
    
    # Signature titles
    pdf.set_font("Arial", 'B', 11)
    for i, (title, label, signature) in enumerate(signatures):
        x_position = start_x + (i * (col_width + spacing))
        pdf.set_xy(x_position, pdf.get_y())
        pdf.cell(col_width, 6, title, 0, 0, 'C')
    
    pdf.ln(8)
    
    # Signature boxes with COMPLETE BORDERS
    current_y = pdf.get_y()
    for i, (title, label, signature) in enumerate(signatures):
        x_position = start_x + (i * (col_width + spacing))
        
        # Draw complete border around signature box
        pdf.rect(x_position, current_y, col_width, 25)
        
        # Add signature image if available
        if signature and signature.strip():
            try:
                # Convert base64 signature to image file
                sig_img_data = base64.b64decode(signature.split(',')[1])
                sig_img = Image.open(io.BytesIO(sig_img_data))
                
                # Save temporary image
                temp_file = f"temp_sig_{i}_{gate_pass_data['reference']}.png"
                sig_img.save(temp_file)
                
                # Add image to PDF (smaller to fit in box)
                pdf.image(temp_file, x=x_position + 2, y=current_y + 2, w=col_width - 4, h=21)
                
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                # If signature image fails, add text placeholder
                pdf.set_font("Arial", 'I', 8)
                pdf.set_xy(x_position, current_y + 10)
                pdf.cell(col_width, 5, "SIGNED", 0, 0, 'C')
        else:
            # No signature - show placeholder
            pdf.set_font("Arial", 'I', 8)
            pdf.set_xy(x_position, current_y + 10)
            pdf.cell(col_width, 5, "Signature", 0, 0, 'C')
    
    pdf.ln(30)  # Move down after signature boxes
    
    # Labels under signatures
    pdf.set_font("Arial", size=9)
    for i, (title, label, signature) in enumerate(signatures):
        x_position = start_x + (i * (col_width + spacing))
        pdf.set_xy(x_position, pdf.get_y())
        pdf.cell(col_width, 5, label, 0, 0, 'C')
    
    pdf.ln(8)
    
    # Lines for written names
    for i, (title, label, signature) in enumerate(signatures):
        x_position = start_x + (i * (col_width + spacing))
        pdf.line(x_position + 5, pdf.get_y(), x_position + col_width - 5, pdf.get_y())
    
    pdf.ln(5)
    
    # "Name & Designation" labels
    pdf.set_font("Arial", 'I', 8)
    for i, (title, label, signature) in enumerate(signatures):
        x_position = start_x + (i * (col_width + spacing))
        pdf.set_xy(x_position, pdf.get_y())
        pdf.cell(col_width, 4, "Name & Designation", 0, 0, 'C')
    
    return pdf

# Function to create PDF download link
def get_pdf_download_link(pdf, filename, text):
    pdf_output = pdf.output(dest='S').encode('latin-1')
    b64 = base64.b64encode(pdf_output).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="background-color: #4CAF50; color: white; padding: 15px 30px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px; font-size: 16px; font-weight: bold;">{text}</a>'
    return href

# Simple canvas component using Streamlit's drawing functionality
def signature_canvas(label, key):
    st.markdown(f"**{label}**")
    st.write("Draw your signature in the box below:")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=4,
        stroke_color="#000000",
        background_color="#ffffff",
        background_image=None,
        update_streamlit=True,
        height=120,
        width=400,
        drawing_mode="freedraw",
        point_display_radius=0,
        key=key,
    )
    
    return canvas_result

# Import streamlit-drawable-canvas
try:
    from streamlit_drawable_canvas import st_canvas
except ImportError:
    st.error("Please install streamlit-drawable-canvas: pip install streamlit-drawable-canvas")
    st.stop()

# Main app logic
def main():
    # Check if Google Sheets is connected
    if gate_pass_sheet is None:
        st.error("""
        ⚠️ **Google Sheets not connected!**
        
        To set up Google Sheets integration:
        
        1. **Create a Google Service Account:**
           - Go to [Google Cloud Console](https://console.cloud.google.com/)
           - Create a new project or select existing one
           - Enable Google Sheets API
           - Create a service account and download JSON credentials
        
        2. **Add to Streamlit Secrets:**
           In your `.streamlit/secrets.toml` file, add:
           ```toml
           [gcp_service_account]
           type = "service_account"
           project_id = "your-project-id"
           private_key_id = "your-private-key-id"
           private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
           client_email = "your-service-account@your-project.iam.gserviceaccount.com"
           client_id = "your-client-id"
           auth_uri = "https://accounts.google.com/o/oauth2/auth"
           token_uri = "https://oauth2.googleapis.com/token"
           auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
           client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
           ```
        
        3. **Share Google Sheet:**
           - Create a Google Sheet named "Alumex_Gate_Passes"
           - Share it with the service account email (editor permission)
        """)
        return
    
    tab1, tab2 = st.tabs(["Create New Gate Pass", "Sign Existing Gate Pass"])
    
    with tab1:
        st.subheader("Create New Gate Pass")
        
        # Form inputs
        col1, col2 = st.columns(2)
        
        with col1:
            requested_by = st.text_input("1. Requested by (Name of the Executive)")
            send_to = st.text_area("2. Send to (Name & Address)", height=100)
            purpose = st.text_area("3. Purpose of sending", height=80)
        
        with col2:
            st.write("4. Tentative returnable date (Optional)")
            return_date = st.date_input("", value=None, min_value=date.today(), label_visibility="collapsed")
            dispatch_type = st.selectbox("5. Type of dispatch", 
                                       ["Credit Sale", "Cash Sale", "Returnable", "Non Returnable"])
            vehicle_number = st.text_input("6. Vehicle Number", placeholder="Enter vehicle number")
        
        st.subheader("Details of items Dispatch")
        
        # Initialize session state for items if not exists - start with 3 empty rows
        if 'items_df' not in st.session_state:
            st.session_state.items_df = pd.DataFrame({
                'Quantity': ['', '', ''],
                'Description': ['', '', ''],
                'Total Value': ['', '', ''],
                'Invoice No': ['', '', '']
            })
        
        # Editable dataframe for items with more rows and dynamic editing
        st.write("**Add items below (you can add/delete rows as needed):**")
        edited_df = st.data_editor(
            st.session_state.items_df,
            num_rows="dynamic",
            use_container_width=True,
            key="items_editor",
            column_config={
                "Quantity": st.column_config.TextColumn(width="small"),
                "Description": st.column_config.TextColumn(width="large"),
                "Total Value": st.column_config.TextColumn(width="medium"),
                "Invoice No": st.column_config.TextColumn(width="medium")
            }
        )
        
        # Certified signature canvas
        st.subheader("Certified Signature")
        certified_canvas = signature_canvas("Draw your signature below:", "certified_canvas_new")
        
        if st.button("✅ Submit Gate Pass", type="primary"):
            if not requested_by or not send_to or not vehicle_number:
                st.error("Please fill in all required fields including vehicle number")
                return
            
            # Filter out empty rows
            items_data = edited_df.to_dict('records')
            items_data = [item for item in items_data if any(str(value).strip() for value in item.values())]
            
            if not items_data:
                st.error("Please add at least one item")
                return
            
            if certified_canvas.image_data is None:
                st.error("Please provide certified signature")
                return
            
            # Generate reference and save data
            gate_pass_data = {
                'requested_by': requested_by,
                'send_to': send_to,
                'purpose': purpose,
                'return_date': return_date.strftime("%Y-%m-%d") if return_date else "",
                'dispatch_type': dispatch_type,
                'vehicle_number': vehicle_number,
                'items': items_data
            }
            
            reference = generate_reference(gate_pass_data)
            gate_pass_data['reference'] = reference
            
            # Convert canvas to base64
            if certified_canvas.image_data is not None:
                img_data = certified_canvas.image_data
                if img_data is not None:
                    pil_img = Image.fromarray((img_data[:, :, :3]).astype('uint8'))
                    buffered = io.BytesIO()
                    pil_img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    gate_pass_data['certified_signature'] = f"data:image/png;base64,{img_str}"
            
            if save_gate_pass(gate_pass_data):
                st.success(f"🎉 Gate Pass submitted successfully!")
                st.info(f"**Your Reference Number:** **{reference}**")
                st.warning("📝 Please share this reference number with authorized personnel for signing.")
                
                # Generate and provide download link as PDF
                gate_pass_pdf = create_gate_pass_pdf(gate_pass_data)
                st.markdown("---")
                st.markdown("### 📥 Download Your Gate Pass")
                st.markdown(get_pdf_download_link(gate_pass_pdf, f"gate_pass_{reference}.pdf", "⬇️ Download PDF"), unsafe_allow_html=True)
                
                # Reset form with 3 empty rows
                st.session_state.items_df = pd.DataFrame({
                    'Quantity': ['', '', ''],
                    'Description': ['', '', ''],
                    'Total Value': ['', '', ''],
                    'Invoice No': ['', '', '']
                })
    
    with tab2:
        st.subheader("Sign Existing Gate Pass")
        
        reference_input = st.text_input("Enter Reference Number", placeholder="e.g., GP1A2B3C4D")
        
        if reference_input:
            gate_pass_data = get_gate_pass(reference_input)
            
            if gate_pass_data:
                st.success("✅ Gate Pass Found!")
                
                # Display existing data (read-only)
                st.subheader("Gate Pass Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("Requested by", value=gate_pass_data['requested_by'], disabled=True)
                    st.text_area("Send to", value=gate_pass_data['send_to'], disabled=True, height=100)
                    st.text_area("Purpose", value=gate_pass_data['purpose'], disabled=True, height=80)
                
                with col2:
                    st.text_input("Return Date", value=gate_pass_data.get('return_date', 'Not specified'), disabled=True)
                    st.text_input("Dispatch Type", value=gate_pass_data['dispatch_type'], disabled=True)
                    vehicle_number = st.text_input("Vehicle Number", 
                                                 value=gate_pass_data.get('vehicle_number', ''),
                                                 placeholder="Enter vehicle number")
                
                # Display items
                st.subheader("Items Dispatch Details")
                items_df = pd.DataFrame(gate_pass_data['items'])
                st.dataframe(items_df, use_container_width=True)
                
                # Signature sections with canvas
                st.subheader("Signatures Required")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Certified Signature**")
                    if gate_pass_data.get('certified_signature') and gate_pass_data['certified_signature'].strip():
                        st.image(gate_pass_data['certified_signature'], width=200)
                        st.success("✓ Already signed")
                    else:
                        st.warning("Pending signature")
                
                with col2:
                    st.write("**Authorized Signature**")
                    authorized_canvas = signature_canvas("Draw authorized signature", "authorized_canvas")
                
                with col3:
                    st.write("**Received Signature**")
                    received_canvas = signature_canvas("Draw received signature", "received_canvas")
                
                if st.button("✅ Submit All Signatures", type="primary"):
                    if (authorized_canvas.image_data is not None and 
                        received_canvas.image_data is not None and 
                        vehicle_number):
                        
                        # Convert canvases to base64
                        authorized_sig = None
                        received_sig = None
                        
                        if authorized_canvas.image_data is not None:
                            img_data = authorized_canvas.image_data
                            pil_img = Image.fromarray((img_data[:, :, :3]).astype('uint8'))
                            buffered = io.BytesIO()
                            pil_img.save(buffered, format="PNG")
                            img_str = base64.b64encode(buffered.getvalue()).decode()
                            authorized_sig = f"data:image/png;base64,{img_str}"
                        
                        if received_canvas.image_data is not None:
                            img_data = received_canvas.image_data
                            pil_img = Image.fromarray((img_data[:, :, :3]).astype('uint8'))
                            buffered = io.BytesIO()
                            pil_img.save(buffered, format="PNG")
                            img_str = base64.b64encode(buffered.getvalue()).decode()
                            received_sig = f"data:image/png;base64,{img_str}"
                        
                        if update_signatures(reference_input, 
                                          gate_pass_data.get('certified_signature', ''),
                                          authorized_sig, 
                                          received_sig, 
                                          vehicle_number):
                            
                            # Update the gate pass data with new signatures
                            updated_data = gate_pass_data.copy()
                            updated_data['authorized_signature'] = authorized_sig
                            updated_data['received_signature'] = received_sig
                            updated_data['vehicle_number'] = vehicle_number
                            
                            # Generate and provide download link as PDF
                            gate_pass_pdf = create_gate_pass_pdf(updated_data)
                            st.success("🎉 All signatures submitted successfully! Gate Pass is now completed.")
                            st.markdown("---")
                            st.markdown("### 📥 Download Completed Gate Pass")
                            st.markdown(get_pdf_download_link(gate_pass_pdf, f"gate_pass_{reference_input}.pdf", "⬇️ Download Completed Gate Pass (PDF)"), unsafe_allow_html=True)
                    else:
                        st.error("❌ Please provide all signatures and vehicle number")
            else:
                st.error("❌ Gate Pass not found. Please check the reference number.")

if __name__ == "__main__":
    main()

