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
import numpy as np

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

# Function to create gate pass image with EXTRA LARGE, READABLE text
def create_gate_pass_image(gate_pass_data):
    # Create a larger image for better readability
    width, height = 2400, 1800  # Increased size for larger fonts
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Define colors - professional color scheme
    title_color = (25, 25, 112)  # Midnight Blue
    header_color = (0, 100, 0)   # Dark Green
    accent_color = (70, 130, 180)  # Steel Blue
    border_color = (0, 0, 0)     # Black
    text_color = (0, 0, 0)       # Black
    table_header_color = (220, 220, 220)  # Light Gray
    
    # Try different fonts in order of preference - TRIPLE THE SIZES
    fonts_to_try = [
        "calibri.ttf",
        "arial.ttf", 
        "arialbd.ttf",
        "times.ttf"
    ]
    
    title_font = None
    header_font = None
    normal_font = None
    table_font = None
    signature_font = None
    
    for font_path in fonts_to_try:
        try:
            if title_font is None:
                title_font = ImageFont.truetype(font_path, 72)  # TRIPLED: 72px (was 24px)
            if header_font is None:
                header_font = ImageFont.truetype(font_path, 54)  # TRIPLED: 54px (was 18px)
            if normal_font is None:
                normal_font = ImageFont.truetype(font_path, 42)  # TRIPLED: 42px (was 14px)
            if table_font is None:
                table_font = ImageFont.truetype(font_path, 36)   # TRIPLED: 36px (was 12px)
            if signature_font is None:
                signature_font = ImageFont.truetype(font_path, 30)  # For signature labels
        except:
            continue
    
    # Fallback to default fonts if none found
    if title_font is None:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        table_font = ImageFont.load_default()
        signature_font = ImageFont.load_default()
    
    # Draw thick border around entire gate pass
    draw.rectangle([30, 30, width-30, height-30], outline=border_color, width=8)
    
    # Header section with professional styling
    header_bg_color = (240, 248, 255)  # Alice Blue background
    draw.rectangle([40, 40, width-40, 220], fill=header_bg_color, outline=accent_color, width=4)
    
    # Main title - EXTRA LARGE and prominent
    draw.text((width//2, 90), "ADVICE DISPATCH GATE PASS", fill=title_color, font=title_font, anchor='mm')
    draw.text((width//2, 160), "ALUMEX GROUP", fill=header_color, font=header_font, anchor='mm')
    draw.text((width//2, 210), "Sapugaskanda, Makola • Tel: 2400332,2400333,2400421", fill=text_color, font=normal_font, anchor='mm')
    
    # Reference number - highlighted
    ref_bg_color = (255, 250, 205)  # Lemon Chiffon
    draw.rectangle([width-500, 240, width-40, 300], fill=ref_bg_color, outline=accent_color, width=3)
    draw.text((width-270, 270), f"REF: {gate_pass_data['reference']}", fill=title_color, font=header_font, anchor='mm')
    
    # Main content area
    content_start_y = 340
    
    # Left column - Basic information
    left_col_x = 60
    right_col_x = width // 2 + 40
    
    # Section title for basic info
    draw.rectangle([left_col_x, content_start_y, width//2 - 30, content_start_y + 60], fill=header_color)
    draw.text((left_col_x + 300, content_start_y + 30), "BASIC INFORMATION", fill=(255, 255, 255), font=header_font, anchor='mm')
    
    info_y = content_start_y + 100
    
    # Field labels and values with better spacing
    fields = [
        ("Requested by:", gate_pass_data['requested_by']),
        ("Send to:", gate_pass_data['send_to']),
        ("Purpose:", gate_pass_data['purpose']),
        ("Return Date:", gate_pass_data.get('return_date', 'Not specified')),
        ("Dispatch Type:", gate_pass_data['dispatch_type']),
        ("Vehicle No:", gate_pass_data.get('vehicle_number', ''))
    ]
    
    for label, value in fields:
        # Label
        draw.text((left_col_x + 30, info_y), label, fill=header_color, font=normal_font)
        # Value with background
        if value:  # Only draw background if there's a value
            draw.rectangle([left_col_x + 300, info_y - 10, width//2 - 60, info_y + 50], fill=(250, 250, 250), outline=(200, 200, 200), width=2)
        draw.text((left_col_x + 320, info_y + 20), str(value), fill=text_color, font=normal_font)
        info_y += 80  # More space between fields
    
    # Right column - Items table
    # Section title for items
    draw.rectangle([right_col_x, content_start_y, width-60, content_start_y + 60], fill=accent_color)
    draw.text((right_col_x + 300, content_start_y + 30), "ITEMS DISPATCH DETAILS", fill=(255, 255, 255), font=header_font, anchor='mm')
    
    # Table setup
    table_start_y = content_start_y + 100
    col_widths = [150, 500, 200, 200]  # Adjusted widths for larger text
    cell_height = 70  # Taller cells for larger text
    
    # Table headers
    headers = ["QUANTITY", "DESCRIPTION", "TOTAL VALUE", "INVOICE NO"]
    x_pos = right_col_x
    
    # Draw header row
    draw.rectangle([x_pos, table_start_y, x_pos + sum(col_widths), table_start_y + cell_height], 
                   fill=table_header_color, outline=border_color, width=3)
    
    for i, header in enumerate(headers):
        draw.text((x_pos + col_widths[i]//2, table_start_y + cell_height//2), 
                 header, fill=text_color, font=table_font, anchor='mm')
        if i < len(headers) - 1:
            draw.line([x_pos + col_widths[i], table_start_y, x_pos + col_widths[i], table_start_y + cell_height], 
                     fill=border_color, width=3)
        x_pos += col_widths[i]
    
    # Table rows
    current_y = table_start_y + cell_height
    
    for item in gate_pass_data['items']:
        x_pos = right_col_x
        
        # Alternate row colors for better readability
        row_color = (255, 255, 255) if gate_pass_data['items'].index(item) % 2 == 0 else (245, 245, 245)
        draw.rectangle([x_pos, current_y, x_pos + sum(col_widths), current_y + cell_height], 
                       fill=row_color, outline=border_color, width=2)
        
        # Cell contents
        draw.text((x_pos + col_widths[0]//2, current_y + cell_height//2), 
                 str(item.get('Quantity', '')), fill=text_color, font=table_font, anchor='mm')
        x_pos += col_widths[0]
        
        draw.line([x_pos, current_y, x_pos, current_y + cell_height], fill=border_color, width=2)
        draw.text((x_pos + col_widths[1]//2, current_y + cell_height//2), 
                 str(item.get('Description', '')), fill=text_color, font=table_font, anchor='mm')
        x_pos += col_widths[1]
        
        draw.line([x_pos, current_y, x_pos, current_y + cell_height], fill=border_color, width=2)
        draw.text((x_pos + col_widths[2]//2, current_y + cell_height//2), 
                 str(item.get('Total Value', '')), fill=text_color, font=table_font, anchor='mm')
        x_pos += col_widths[2]
        
        draw.line([x_pos, current_y, x_pos, current_y + cell_height], fill=border_color, width=2)
        draw.text((x_pos + col_widths[3]//2, current_y + cell_height//2), 
                 str(item.get('Invoice No', '')), fill=text_color, font=table_font, anchor='mm')
        
        current_y += cell_height
    
    # Signatures section at bottom
    signature_section_y = height - 350
    
    # Signature section title
    draw.rectangle([60, signature_section_y - 70, width-60, signature_section_y - 10], fill=header_color)
    draw.text((width//2, signature_section_y - 40), "AUTHORIZATIONS & SIGNATURES", fill=(255, 255, 255), font=header_font, anchor='mm')
    
    # Signature boxes
    sig_box_width = 400
    sig_box_height = 120
    spacing = (width - 120 - 3*sig_box_width) // 4
    
    signature_titles = ["CERTIFIED BY", "AUTHORIZED BY", "RECEIVED BY"]
    signature_labels = ["Certifying Officer", "Authorizing Manager", "Receiving Party"]
    signature_x_positions = [60 + spacing, 60 + spacing*2 + sig_box_width, 60 + spacing*3 + sig_box_width*2]
    
    for i, title in enumerate(signature_titles):
        x_pos = signature_x_positions[i]
        
        # Signature box with border
        draw.rectangle([x_pos, signature_section_y, x_pos + sig_box_width, signature_section_y + sig_box_height], 
                       outline=border_color, width=4)
        
        # Title above box
        draw.text((x_pos + sig_box_width//2, signature_section_y - 25), title, fill=header_color, font=normal_font, anchor='mm')
        
        # Signature image if available
        sig_key = ['certified_signature', 'authorized_signature', 'received_signature'][i]
        if gate_pass_data.get(sig_key):
            try:
                sig_img = Image.open(io.BytesIO(base64.b64decode(gate_pass_data[sig_key].split(',')[1])))
                sig_img = sig_img.resize((sig_box_width - 30, sig_box_height - 30))
                img.paste(sig_img, (x_pos + 15, signature_section_y + 15))
            except:
                draw.text((x_pos + sig_box_width//2, signature_section_y + sig_box_height//2), 
                         "SIGNED", fill=(150, 150, 150), font=normal_font, anchor='mm')
        else:
            draw.text((x_pos + sig_box_width//2, signature_section_y + sig_box_height//2), 
                     "[Signature Required]", fill=(200, 200, 200), font=table_font, anchor='mm')
        
        # Party name label below the signature box
        label_y = signature_section_y + sig_box_height + 20
        draw.text((x_pos + sig_box_width//2, label_y), signature_labels[i], fill=text_color, font=signature_font, anchor='mm')
        
        # Line for written name
        draw.line([x_pos + 50, label_y + 30, x_pos + sig_box_width - 50, label_y + 30], fill=border_color, width=2)
        draw.text((x_pos + sig_box_width//2, label_y + 50), "Name & Designation", fill=(150, 150, 150), font=signature_font, anchor='mm')
    
    # Footer with date
    footer_y = height - 40
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((width//2, footer_y), f"Generated on: {current_date}", fill=(100, 100, 100), font=table_font, anchor='mm')
    
    return img

# Function to create download link for HIGH QUALITY JPG
def get_jpg_download_link(img, filename, text):
    buffered = io.BytesIO()
    # Save as HIGH quality JPG
    img.save(buffered, format="JPEG", quality=100, optimize=True)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:image/jpeg;base64,{img_str}" download="{filename}" style="background-color: #4CAF50; color: white; padding: 15px 30px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px; font-size: 16px; font-weight: bold;">{text}</a>'
    return href

# Simple canvas component using Streamlit's drawing functionality
def signature_canvas(label, key):
    st.markdown(f"**{label}**")
    st.write("Draw your signature in the box below:")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=4,  # Thicker strokes
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
                
                # Generate and provide download link as HIGH QUALITY JPG
                gate_pass_img = create_gate_pass_image(gate_pass_data)
                st.markdown("---")
                st.markdown("### 📥 Download Your Gate Pass")
                st.markdown(get_jpg_download_link(gate_pass_img, f"gate_pass_{reference}.jpg", "⬇️ Download High Quality JPG"), unsafe_allow_html=True)
                
                # Show preview
                st.image(gate_pass_img, caption="Gate Pass Preview", use_column_width=True)
                
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
                    if gate_pass_data.get('certified_signature'):
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
                            
                            # Generate and provide download link as HIGH QUALITY JPG
                            gate_pass_img = create_gate_pass_image(updated_data)
                            st.success("🎉 All signatures submitted successfully! Gate Pass is now completed.")
                            st.markdown("---")
                            st.markdown("### 📥 Download Completed Gate Pass")
                            st.markdown(get_jpg_download_link(gate_pass_img, f"gate_pass_{reference_input}.jpg", "⬇️ Download Completed Gate Pass (JPG)"), unsafe_allow_html=True)
                            
                            # Show preview
                            st.image(gate_pass_img, caption="Completed Gate Pass Preview", use_column_width=True)
                    else:
                        st.error("❌ Please provide all signatures and vehicle number")
            else:
                st.error("❌ Gate Pass not found. Please check the reference number.")

if __name__ == "__main__":
    main()
