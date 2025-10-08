import streamlit as st
import pandas as pd
import json
import hashlib
import datetime
from datetime import date
import sqlite3
import base64

# Page configuration
st.set_page_config(
    page_title="Alumex Gate Pass System",
    page_icon="📋",
    layout="centered"
)

# Initialize database
def init_db():
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

# Function to get gate pass by reference
def get_gate_pass(reference):
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

# Function to update signatures
def update_signatures(reference, certified_sig, authorized_sig, received_sig, vehicle_no):
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

# Main app logic
def main():
    tab1, tab2 = st.tabs(["Create New Gate Pass", "Sign Existing Gate Pass"])
    
    with tab1:
        st.subheader("Create New Gate Pass")
        
        # Form inputs
        requested_by = st.text_input("1. Requested by (Name of the Executive)")
        send_to = st.text_area("2. Send to (Name & Address)", height=80)
        purpose = st.text_area("3. Purpose of sending (For non scale items)", height=80)
        return_date = st.date_input("4. Tentative returnable date", min_value=date.today())
        dispatch_type = st.selectbox("5. Type of dispatch", 
                                   ["Credit Sale", "Cash Sale", "Returnable", "Non Returnable"])
        
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
        
        if st.button("Submit Gate Pass"):
            if not requested_by or not send_to:
                st.error("Please fill in all required fields")
                return
            
            # Filter out empty rows
            items_data = edited_df.to_dict('records')
            items_data = [item for item in items_data if any(str(value).strip() for value in item.values())]
            
            if not items_data:
                st.error("Please add at least one item")
                return
            
            # Generate reference and save data
            gate_pass_data = {
                'requested_by': requested_by,
                'send_to': send_to,
                'purpose': purpose,
                'return_date': return_date.strftime("%Y-%m-%d"),
                'dispatch_type': dispatch_type,
                'items': items_data
            }
            
            reference = generate_reference(gate_pass_data)
            gate_pass_data['reference'] = reference
            
            save_gate_pass(gate_pass_data)
            
            st.success(f"Gate Pass submitted successfully!")
            st.info(f"**Your Reference Number:** {reference}")
            st.warning("Please share this reference number with authorized personnel for signing.")
            
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
                    st.text_input("Return Date", value=gate_pass_data['return_date'], disabled=True)
                    st.text_input("Dispatch Type", value=gate_pass_data['dispatch_type'], disabled=True)
                
                # Display items
                st.subheader("Items Dispatch Details")
                items_df = pd.DataFrame(gate_pass_data['items'])
                st.dataframe(items_df, use_container_width=True)
                
                # Signature sections
                st.subheader("Signatures")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Certified by signature**")
                    certified_sig = st.text_input("Certified Signature", key="certified_sig", 
                                                placeholder="Enter signature")
                
                with col2:
                    st.write("**Authorized by**")
                    authorized_sig = st.text_input("Authorized Signature", key="authorized_sig",
                                                 placeholder="Enter signature")
                
                with col3:
                    st.write("**Received by**")
                    received_sig = st.text_input("Received Signature", key="received_sig",
                                               placeholder="Enter signature")
                
                vehicle_number = st.text_input("Vehicle Number", placeholder="Enter vehicle number")
                
                if st.button("Submit Signatures"):
                    if certified_sig and authorized_sig and received_sig and vehicle_number:
                        update_signatures(reference_input, certified_sig, authorized_sig, 
                                        received_sig, vehicle_number)
                        st.success("Signatures submitted successfully! Gate Pass is now completed.")
                    else:
                        st.error("Please fill all signature fields and vehicle number")
            else:
                st.error("Gate Pass not found. Please check the reference number.")

if __name__ == "__main__":
    main()