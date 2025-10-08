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

# Google Sheets setup with proper private key handling
# Robust Google Sheets setup
def setup_google_sheets():
    try:
        # Check if secrets are available
        if 'gcp_service_account' not in st.secrets:
            st.sidebar.warning("Google Sheets credentials not found")
            return None
        
        # Get the service account info directly from secrets
        sa_secrets = st.secrets['gcp_service_account']
        
        # Create the service account info dictionary
        service_account_info = {
            "type": sa_secrets["type"],
            "project_id": sa_secrets["project_id"],
            "private_key_id": sa_secrets["private_key_id"],
            "private_key": sa_secrets["private_key"],
            "client_email": sa_secrets["client_email"],
            "client_id": sa_secrets["client_id"],
            "auth_uri": sa_secrets["auth_uri"],
            "token_uri": sa_secrets["token_uri"],
            "auth_provider_x509_cert_url": sa_secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": sa_secrets["client_x509_cert_url"]
        }
        
        # Create credentials
        creds = Credentials.from_service_account_info(service_account_info)
        client = gspread.authorize(creds)
        
        # Try to open the sheet
        try:
            sheet = client.open("Alumex_Gate_Passes").sheet1
            st.sidebar.success("✅ Connected to Google Sheets!")
            return sheet
        except gspread.SpreadsheetNotFound:
            # Create new sheet
            spreadsheet = client.create("Alumex_Gate_Passes")
            sheet = spreadsheet.sheet1
            headers = [
                "Reference", "Requested_By", "Send_To", "Purpose", 
                "Return_Date", "Dispatch_Type", "Vehicle_Number",
                "Items_JSON", "Certified_Signature", "Authorized_Signature",
                "Received_Signature", "Status", "Created_Date", "Completed_Date"
            ]
            sheet.append_row(headers)
            st.sidebar.success("✅ Created new Google Sheet!")
            return sheet
            
    except Exception as e:
        st.sidebar.error(f"❌ Google Sheets: {str(e)}")
        # Show more detailed error for debugging
        if "padding" in str(e).lower():
            st.sidebar.error("Private key formatting error - check secrets format")
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

# Function to save gate pass
def save_gate_pass(data):
    try:
        if gate_pass_sheet is None:
            # Fallback to session state
            if 'local_gate_passes' not in st.session_state:
                st.session_state.local_gate_passes = {}
            st.session_state.local_gate_passes[data['reference']] = data
            return True
        
        # Save to Google Sheets
        items_json = json.dumps(data['items'])
        row_data = [
            data['reference'], data['requested_by'], data['send_to'], data['purpose'],
            data.get('return_date', ''), data['dispatch_type'], data.get('vehicle_number', ''),
            items_json, data.get('certified_signature', ''), '', '',
            'pending', datetime.datetime.now().isoformat(), ''
        ]
        gate_pass_sheet.append_row(row_data)
        return True
        
    except Exception as e:
        st.error(f"Error saving: {e}")
        # Fallback
        if 'local_gate_passes' not in st.session_state:
            st.session_state.local_gate_passes = {}
        st.session_state.local_gate_passes[data['reference']] = data
        return True

# Function to get gate pass by reference
def get_gate_pass(reference):
    try:
        if gate_pass_sheet is not None:
            # Try Google Sheets first
            records = gate_pass_sheet.get_all_records()
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
                        'status': record['Status']
                    }
        
        # Fallback to session state
        if 'local_gate_passes' in st.session_state:
            return st.session_state.local_gate_passes.get(reference)
            
        return None
        
    except Exception as e:
        # Fallback to session state
        if 'local_gate_passes' in st.session_state:
            return st.session_state.local_gate_passes.get(reference)
        return None

# Function to update signatures
def update_signatures(reference, certified_sig, authorized_sig, received_sig, vehicle_no):
    try:
        if gate_pass_sheet is not None:
            # Update in Google Sheets
            records = gate_pass_sheet.get_all_records()
            for i, record in enumerate(records):
                if record['Reference'] == reference:
                    row_num = i + 2
                    gate_pass_sheet.update_cell(row_num, 10, authorized_sig)
                    gate_pass_sheet.update_cell(row_num, 11, received_sig)
                    gate_pass_sheet.update_cell(row_num, 7, vehicle_no)
                    gate_pass_sheet.update_cell(row_num, 12, 'completed')
                    return True
        
        # Fallback to session state
        if 'local_gate_passes' in st.session_state and reference in st.session_state.local_gate_passes:
            st.session_state.local_gate_passes[reference]['authorized_signature'] = authorized_sig
            st.session_state.local_gate_passes[reference]['received_signature'] = received_sig
            st.session_state.local_gate_passes[reference]['vehicle_number'] = vehicle_no
            st.session_state.local_gate_passes[reference]['status'] = 'completed'
            return True
            
        return False
        
    except Exception as e:
        st.error(f"Error updating: {e}")
        return False

# PDF creation function
def create_gate_pass_pdf(gate_pass_data):
    class PDFWithFooter(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 9)
            current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cell(0, 10, f'Generated on: {current_date} | Page {self.page_no()}', 0, 0, 'C')
    
    pdf = PDFWithFooter(format='A4')
    pdf.add_page()
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
    
    # Basic Information
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
        pdf.cell(0, 7, str(value), ln=True)
    
    pdf.ln(8)
    
    # Items Table
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "ITEMS DISPATCH DETAILS", ln=True, align='L')
    pdf.ln(5)
    
    # Table headers
    pdf.set_font("Arial", 'B', 11)
    col_widths = [20, 100, 30, 35]
    headers = ["Qty", "Description", "Value", "Invoice No"]
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()
    
    # Table rows
    pdf.set_font("Arial", size=10)
    for item in gate_pass_data['items']:
        pdf.cell(col_widths[0], 8, str(item.get('Quantity', '')), 1, 0, 'C')
        
        desc = str(item.get('Description', ''))
        if len(desc) > 40:
            desc = desc[:37] + "..."
        pdf.cell(col_widths[1], 8, desc, 1, 0, 'L')
        
        pdf.cell(col_widths[2], 8, str(item.get('Total Value', '')), 1, 0, 'C')
        pdf.cell(col_widths[3], 8, str(item.get('Invoice No', '')), 1, 0, 'C')
        pdf.ln()
    
    pdf.ln(12)
    
    # Signatures section
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "AUTHORIZATIONS & SIGNATURES", ln=True, align='C')
    pdf.ln(8)
    
    # Signature boxes
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
    
    # Signature boxes
    current_y = pdf.get_y()
    for i, (title, label, signature) in enumerate(signatures):
        x_position = start_x + (i * (col_width + spacing))
        pdf.rect(x_position, current_y, col_width, 25)
        
        if signature and signature.strip():
            try:
                sig_img_data = base64.b64decode(signature.split(',')[1])
                sig_img = Image.open(io.BytesIO(sig_img_data))
                temp_file = f"temp_sig_{i}.png"
                sig_img.save(temp_file)
                pdf.image(temp_file, x=x_position + 2, y=current_y + 2, w=col_width - 4, h=21)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pdf.set_font("Arial", 'I', 8)
                pdf.set_xy(x_position, current_y + 10)
                pdf.cell(col_width, 5, "SIGNED", 0, 0, 'C')
        else:
            pdf.set_font("Arial", 'I', 8)
            pdf.set_xy(x_position, current_y + 10)
            pdf.cell(col_width, 5, "Signature", 0, 0, 'C')
    
    pdf.ln(30)
    
    # Labels under signatures
    pdf.set_font("Arial", size=9)
    for i, (title, label, signature) in enumerate(signatures):
        x_position = start_x + (i * (col_width + spacing))
        pdf.set_xy(x_position, pdf.get_y())
        pdf.cell(col_width, 5, label, 0, 0, 'C')
    
    return pdf

def get_pdf_download_link(pdf, filename, text):
    pdf_output = pdf.output(dest='S').encode('latin-1')
    b64 = base64.b64encode(pdf_output).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="background-color: #4CAF50; color: white; padding: 15px 30px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px; font-size: 16px; font-weight: bold;">{text}</a>'
    return href

def signature_canvas(label, key):
    st.markdown(f"**{label}**")
    st.write("Draw your signature in the box below:")
    
    from streamlit_drawable_canvas import st_canvas
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

# Main app logic
def main():
    tab1, tab2 = st.tabs(["Create New Gate Pass", "Sign Existing Gate Pass"])
    
    with tab1:
        st.subheader("Create New Gate Pass")
        
        col1, col2 = st.columns(2)
        
        with col1:
            requested_by = st.text_input("1. Requested by (Name of the Executive)")
            send_to = st.text_area("2. Send to (Name & Address)", height=100)
            purpose = st.text_area("3. Purpose of sending", height=80)
        
        with col2:
            st.write("4. Tentative returnable date (Optional)")
            # FIXED: Added proper label to avoid warning
            return_date = st.date_input("Return Date", value=None, min_value=date.today(), label_visibility="collapsed")
            dispatch_type = st.selectbox("5. Type of dispatch", 
                                       ["Credit Sale", "Cash Sale", "Returnable", "Non Returnable"])
            vehicle_number = st.text_input("6. Vehicle Number", placeholder="Enter vehicle number")
        
        st.subheader("Details of items Dispatch")
        
        if 'items_df' not in st.session_state:
            st.session_state.items_df = pd.DataFrame({
                'Quantity': ['', '', ''],
                'Description': ['', '', ''],
                'Total Value': ['', '', ''],
                'Invoice No': ['', '', '']
            })
        
        st.write("**Add items below (you can add/delete rows as needed):**")
        # FIXED: Replaced use_container_width with width
        edited_df = st.data_editor(
            st.session_state.items_df,
            num_rows="dynamic",
            width='stretch',  # Changed from use_container_width=True
            key="items_editor",
            column_config={
                "Quantity": st.column_config.TextColumn(width="small"),
                "Description": st.column_config.TextColumn(width="large"),
                "Total Value": st.column_config.TextColumn(width="medium"),
                "Invoice No": st.column_config.TextColumn(width="medium")
            }
        )
        
        st.subheader("Certified Signature")
        certified_canvas = signature_canvas("Draw your signature below:", "certified_canvas_new")
        
        if st.button("✅ Submit Gate Pass", type="primary"):
            if not requested_by or not send_to or not vehicle_number:
                st.error("Please fill in all required fields including vehicle number")
                return
            
            items_data = edited_df.to_dict('records')
            items_data = [item for item in items_data if any(str(value).strip() for value in item.values())]
            
            if not items_data:
                st.error("Please add at least one item")
                return
            
            if certified_canvas.image_data is None:
                st.error("Please provide certified signature")
                return
            
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
                
                gate_pass_pdf = create_gate_pass_pdf(gate_pass_data)
                st.markdown("---")
                st.markdown("### 📥 Download Your Gate Pass")
                st.markdown(get_pdf_download_link(gate_pass_pdf, f"gate_pass_{reference}.pdf", "⬇️ Download PDF"), unsafe_allow_html=True)
                
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
                
                st.subheader("Items Dispatch Details")
                # FIXED: Replaced use_container_width with width
                items_df = pd.DataFrame(gate_pass_data['items'])
                st.dataframe(items_df, width='stretch')  # Changed from use_container_width=True
                
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
                            
                            updated_data = gate_pass_data.copy()
                            updated_data['authorized_signature'] = authorized_sig
                            updated_data['received_signature'] = received_sig
                            updated_data['vehicle_number'] = vehicle_number
                            
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



