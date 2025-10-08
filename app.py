import streamlit as st
import pandas as pd
import json
import hashlib
import datetime
from datetime import date
import sqlite3
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# Page configuration
st.set_page_config(
    page_title="Alumex Gate Pass System",
    page_icon="📋",
    layout="centered"
)

# Initialize database
def init_db():
    try:
        conn = sqlite3.connect('gate_pass.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS gate_passes
            (reference TEXT PRIMARY KEY,
             requested_by TEXT,
             send_to TEXT,
             purpose TEXT,
             return_date TEXT,
             dispatch_type TEXT,
             items TEXT,
             certified_signature TEXT,
             authorized_signature TEXT,
             received_signature TEXT,
             vehicle_number TEXT,
             status TEXT,
             created_date TEXT)
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")

init_db()

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
        conn = sqlite3.connect('gate_pass.db')
        c = conn.cursor()
        
        items_json = json.dumps(data['items'])
        
        c.execute('''
            INSERT INTO gate_passes 
            (reference, requested_by, send_to, purpose, return_date, dispatch_type, 
             items, certified_signature, authorized_signature, received_signature, 
             vehicle_number, status, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['reference'], data['requested_by'], data['send_to'], data['purpose'],
              data['return_date'], data['dispatch_type'], items_json, 
              data.get('certified_signature', ''), data.get('authorized_signature', ''),
              data.get('received_signature', ''), data.get('vehicle_number', ''),
              'pending', datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving gate pass: {e}")
        return False

# Function to get gate pass by reference
def get_gate_pass(reference):
    try:
        conn = sqlite3.connect('gate_pass.db')
        c = conn.cursor()
        c.execute('SELECT * FROM gate_passes WHERE reference = ?', (reference,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'reference': result[0],
                'requested_by': result[1],
                'send_to': result[2],
                'purpose': result[3],
                'return_date': result[4],
                'dispatch_type': result[5],
                'items': json.loads(result[6]),
                'certified_signature': result[7],
                'authorized_signature': result[8],
                'received_signature': result[9],
                'vehicle_number': result[10],
                'status': result[11],
                'created_date': result[12]
            }
        return None
    except Exception as e:
        st.error(f"Error retrieving gate pass: {e}")
        return None

# Function to update signatures
def update_signatures(reference, certified_sig, authorized_sig, received_sig, vehicle_no):
    try:
        conn = sqlite3.connect('gate_pass.db')
        c = conn.cursor()
        c.execute('''
            UPDATE gate_passes 
            SET certified_signature = ?, authorized_signature = ?, 
                received_signature = ?, vehicle_number = ?, status = 'completed'
            WHERE reference = ?
        ''', (certified_sig, authorized_sig, received_sig, vehicle_no, reference))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating signatures: {e}")
        return False

# Function to create gate pass image
def create_gate_pass_image(gate_pass_data):
    # Create a blank image with white background
    img = Image.new('RGB', (800, 1200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default if not available
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        header_font = ImageFont.truetype("arial.ttf", 18)
        normal_font = ImageFont.truetype("arial.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
    
    # Header
    draw.text((400, 50), "Advice Dispatch Gate Pass", fill='black', font=title_font, anchor='mm')
    draw.text((400, 80), "Alumex Group", fill='black', font=header_font, anchor='mm')
    draw.text((400, 100), "Sapugaskanda, Makola", fill='black', font=normal_font, anchor='mm')
    draw.text((400, 120), "Tel: 2400332,2400333,2400421", fill='black', font=normal_font, anchor='mm')
    
    # Basic information
    y_position = 180
    draw.text((50, y_position), f"Reference: {gate_pass_data['reference']}", fill='black', font=normal_font)
    y_position += 30
    draw.text((50, y_position), f"Requested by: {gate_pass_data['requested_by']}", fill='black', font=normal_font)
    y_position += 30
    draw.text((50, y_position), f"Send to: {gate_pass_data['send_to']}", fill='black', font=normal_font)
    y_position += 30
    draw.text((50, y_position), f"Purpose: {gate_pass_data['purpose']}", fill='black', font=normal_font)
    y_position += 30
    draw.text((50, y_position), f"Return Date: {gate_pass_data.get('return_date', 'Not specified')}", fill='black', font=normal_font)
    y_position += 30
    draw.text((50, y_position), f"Dispatch Type: {gate_pass_data['dispatch_type']}", fill='black', font=normal_font)
    y_position += 30
    draw.text((50, y_position), f"Vehicle Number: {gate_pass_data.get('vehicle_number', '')}", fill='black', font=normal_font)
    
    # Items table
    y_position += 50
    draw.text((50, y_position), "Items Dispatch Details:", fill='black', font=header_font)
    y_position += 30
    
    # Table headers
    draw.text((50, y_position), "Quantity", fill='black', font=normal_font)
    draw.text((150, y_position), "Description", fill='black', font=normal_font)
    draw.text((400, y_position), "Total Value", fill='black', font=normal_font)
    draw.text((550, y_position), "Invoice No", fill='black', font=normal_font)
    y_position += 20
    draw.line((50, y_position, 750, y_position), fill='black', width=2)
    
    # Table rows
    for item in gate_pass_data['items']:
        y_position += 25
        draw.text((50, y_position), str(item.get('Quantity', '')), fill='black', font=normal_font)
        draw.text((150, y_position), str(item.get('Description', '')), fill='black', font=normal_font)
        draw.text((400, y_position), str(item.get('Total Value', '')), fill='black', font=normal_font)
        draw.text((550, y_position), str(item.get('Invoice No', '')), fill='black', font=normal_font)
    
    # Signatures
    y_position += 80
    col_width = 250
    
    # Certified Signature
    draw.text((125, y_position), "Certified by:", fill='black', font=normal_font)
    if gate_pass_data.get('certified_signature'):
        try:
            sig_img = Image.open(io.BytesIO(base64.b64decode(gate_pass_data['certified_signature'].split(',')[1])))
            sig_img = sig_img.resize((200, 80))
            img.paste(sig_img, (50, y_position + 20))
        except:
            draw.text((50, y_position + 50), "Signed", fill='black', font=normal_font)
    
    # Authorized Signature
    draw.text((375, y_position), "Authorized by:", fill='black', font=normal_font)
    if gate_pass_data.get('authorized_signature'):
        try:
            sig_img = Image.open(io.BytesIO(base64.b64decode(gate_pass_data['authorized_signature'].split(',')[1])))
            sig_img = sig_img.resize((200, 80))
            img.paste(sig_img, (300, y_position + 20))
        except:
            draw.text((300, y_position + 50), "Signed", fill='black', font=normal_font)
    
    # Received Signature
    draw.text((625, y_position), "Received by:", fill='black', font=normal_font)
    if gate_pass_data.get('received_signature'):
        try:
            sig_img = Image.open(io.BytesIO(base64.b64decode(gate_pass_data['received_signature'].split(',')[1])))
            sig_img = sig_img.resize((200, 80))
            img.paste(sig_img, (550, y_position + 20))
        except:
            draw.text((550, y_position + 50), "Signed", fill='black', font=normal_font)
    
    return img

# Function to create download link
def get_image_download_link(img, filename, text):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{img_str}" download="{filename}">{text}</a>'
    return href

# Main app logic
def main():
    tab1, tab2 = st.tabs(["Create New Gate Pass", "Sign Existing Gate Pass"])
    
    with tab1:
        st.subheader("Create New Gate Pass")
        
        # Form inputs
        requested_by = st.text_input("1. Requested by (Name of the Executive)")
        send_to = st.text_area("2. Send to (Name & Address)", height=80)
        purpose = st.text_area("3. Purpose of sending (For non scale items)", height=80)
        
        # Make return date optional
        st.write("4. Tentative returnable date (Optional)")
        return_date = st.date_input("", value=None, min_value=date.today(), label_visibility="collapsed")
        
        dispatch_type = st.selectbox("5. Type of dispatch", 
                                   ["Credit Sale", "Cash Sale", "Returnable", "Non Returnable"])
        vehicle_number = st.text_input("6. Vehicle Number", placeholder="Enter vehicle number")
        
        st.subheader("Details of items Dispatch")
        
        # Initialize session state for items if not exists
        if 'items_df' not in st.session_state:
            st.session_state.items_df = pd.DataFrame({
                'Quantity': [''],
                'Description': [''],
                'Total Value': [''],
                'Invoice No': ['']
            })
        
        # Editable dataframe for items
        edited_df = st.data_editor(
            st.session_state.items_df,
            num_rows="dynamic",
            use_container_width=True,
            key="items_editor"
        )
        
        # Certified signature using file upload (fallback)
        st.subheader("Certified Signature")
        st.write("Upload your signature image:")
        certified_signature = st.file_uploader("Choose signature image", type=['png', 'jpg', 'jpeg'], key="certified_upload")
        
        if certified_signature is not None:
            st.image(certified_signature, width=200)
        
        if st.button("Submit Gate Pass"):
            if not requested_by or not send_to or not vehicle_number:
                st.error("Please fill in all required fields including vehicle number")
                return
            
            # Filter out empty rows
            items_data = edited_df.to_dict('records')
            items_data = [item for item in items_data if any(str(value).strip() for value in item.values())]
            
            if not items_data:
                st.error("Please add at least one item")
                return
            
            if certified_signature is None:
                st.error("Please upload certified signature")
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
            
            # Convert uploaded signature to base64
            if certified_signature is not None:
                certified_bytes = certified_signature.getvalue()
                certified_b64 = base64.b64encode(certified_bytes).decode()
                gate_pass_data['certified_signature'] = f"data:image/png;base64,{certified_b64}"
            
            if save_gate_pass(gate_pass_data):
                st.success(f"Gate Pass submitted successfully!")
                st.info(f"**Your Reference Number:** {reference}")
                st.warning("Please share this reference number with authorized personnel for signing.")
                
                # Generate and provide download link
                gate_pass_img = create_gate_pass_image(gate_pass_data)
                st.markdown(get_image_download_link(gate_pass_img, f"gate_pass_{reference}.png", "📥 Download Gate Pass"), unsafe_allow_html=True)
                
                # Reset form
                st.session_state.items_df = pd.DataFrame({
                    'Quantity': [''],
                    'Description': [''],
                    'Total Value': [''],
                    'Invoice No': ['']
                })
    
    with tab2:
        st.subheader("Sign Existing Gate Pass")
        
        reference_input = st.text_input("Enter Reference Number")
        
        if reference_input:
            gate_pass_data = get_gate_pass(reference_input)
            
            if gate_pass_data:
                st.success("Gate Pass Found!")
                
                # Display existing data (read-only)
                st.subheader("Gate Pass Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("Requested by", value=gate_pass_data['requested_by'], disabled=True)
                    st.text_area("Send to", value=gate_pass_data['send_to'], disabled=True, height=80)
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
                
                # Signature sections with file upload
                st.subheader("Signatures")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Certified by signature**")
                    if gate_pass_data.get('certified_signature'):
                        st.image(gate_pass_data['certified_signature'], width=200)
                    else:
                        st.write("No signature yet")
                
                with col2:
                    st.write("**Authorized by**")
                    st.write("Upload signature image:")
                    authorized_signature = st.file_uploader("Authorized signature", type=['png', 'jpg', 'jpeg'], key="authorized_upload")
                    if authorized_signature is not None:
                        st.image(authorized_signature, width=150)
                
                with col3:
                    st.write("**Received by**")
                    st.write("Upload signature image:")
                    received_signature = st.file_uploader("Received signature", type=['png', 'jpg', 'jpeg'], key="received_upload")
                    if received_signature is not None:
                        st.image(received_signature, width=150)
                
                if st.button("Submit Signatures"):
                    if authorized_signature is not None and received_signature is not None and vehicle_number:
                        # Convert uploaded signatures to base64
                        authorized_b64 = base64.b64encode(authorized_signature.getvalue()).decode()
                        received_b64 = base64.b64encode(received_signature.getvalue()).decode()
                        
                        authorized_sig = f"data:image/png;base64,{authorized_b64}"
                        received_sig = f"data:image/png;base64,{received_b64}"
                        
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
                            
                            # Generate and provide download link
                            gate_pass_img = create_gate_pass_image(updated_data)
                            st.success("Signatures submitted successfully! Gate Pass is now completed.")
                            st.markdown(get_image_download_link(gate_pass_img, f"gate_pass_{reference_input}.png", "📥 Download Completed Gate Pass"), unsafe_allow_html=True)
                    else:
                        st.error("Please provide all signatures and vehicle number")
            else:
                st.error("Gate Pass not found. Please check the reference number.")

if __name__ == "__main__":
    main()
