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
# Function to create gate pass image with EXTRA LARGE, READABLE text
def create_gate_pass_image(gate_pass_data):
    # --- Image setup ---
    width, height = 1300, 900
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # --- Colors ---
    title_color = (25, 25, 112)            # Midnight Blue
    header_color = (30, 144, 255)          # Dodger Blue (replacing green)
    accent_color = (135, 206, 250)         # Light Sky Blue
    border_color = (0, 0, 0)
    text_color = (0, 0, 0)
    table_header_color = (224, 240, 255)   # Very light blue

    # --- Fonts ---
    try:
        title_font = ImageFont.truetype("arial.ttf", 100)
        header_font = ImageFont.truetype("arial.ttf", 70)
        normal_font = ImageFont.truetype("arial.ttf", 50)
        table_font = ImageFont.truetype("arial.ttf", 48)
        signature_font = ImageFont.truetype("arial.ttf", 42)
    except:
        title_font = ImageFont.load_default()
        header_font = normal_font = table_font = signature_font = ImageFont.load_default()

    # --- Helper to draw spaced text ---
    def draw_spaced_text(draw, position, text, font, fill, spacing=3, anchor=None):
        x, y = position
        for ch in text:
            w, h = draw.textsize(ch, font=font)
            if anchor == 'mm':  # center anchor handling
                draw.text((x, y), ch, font=font, fill=fill, anchor="mm")
                x += w + spacing
            else:
                draw.text((x, y), ch, font=font, fill=fill)
                x += w + spacing

    # --- Border ---
    draw.rectangle([20, 20, width - 20, height - 20], outline=border_color, width=6)

    # --- Header ---
    header_bg_color = (240, 248, 255)
    draw.rectangle([30, 30, width - 30, 150], fill=header_bg_color, outline=accent_color, width=3)
    draw_spaced_text(draw, (width//2 - 300, 60), "ADVICE DISPATCH GATE PASS", title_font, title_color, spacing=5)
    draw_spaced_text(draw, (width//2 - 150, 120), "ALUMEX GROUP", header_font, header_color, spacing=4)

    # Contact info
    draw.text((width//2, 180), "Sapugaskanda, Makola", fill=text_color, font=normal_font, anchor='mm')
    draw.text((width//2, 230), "Tel: 2400332,2400333,2400421", fill=text_color, font=normal_font, anchor='mm')

    # --- Reference Box ---
    ref_bg_color = (224, 240, 255)
    draw.rectangle([width - 350, 40, width - 30, 120], fill=ref_bg_color, outline=accent_color, width=3)
    draw.text((width - 190, 80), f"REF: {gate_pass_data['reference']}", fill=title_color, font=header_font, anchor='mm')

    # --- Basic Information ---
    content_start_y = 270
    draw.rectangle([30, content_start_y, width//2 - 10, content_start_y + 45], fill=accent_color)
    draw.text((width//4, content_start_y + 22), "BASIC INFORMATION", fill=title_color, font=header_font, anchor='mm')

    info_y = content_start_y + 60
    fields = [
        ("Requested by:", gate_pass_data['requested_by']),
        ("Send to:", gate_pass_data['send_to']),
        ("Purpose:", gate_pass_data['purpose']),
        ("Return Date:", gate_pass_data.get('return_date', 'Not specified')),
        ("Dispatch Type:", gate_pass_data['dispatch_type']),
        ("Vehicle No:", gate_pass_data.get('vehicle_number', ''))
    ]
    for label, value in fields:
        draw_spaced_text(draw, (50, info_y), label, normal_font, header_color, spacing=2)
        draw.text((350, info_y), str(value), fill=text_color, font=normal_font)
        info_y += 55

    # --- Items Section ---
    items_start_y = content_start_y
    draw.rectangle([width//2 + 10, items_start_y, width - 30, items_start_y + 45], fill=accent_color)
    draw.text((width//2 + width//4, items_start_y + 22), "ITEMS DISPATCH DETAILS", fill=title_color, font=header_font, anchor='mm')

    table_y = items_start_y + 60
    col_widths = [100, 300, 150, 150]
    row_height = 45
    headers = ["QTY", "DESCRIPTION", "VALUE", "INVOICE"]

    x_pos = width//2 + 10
    draw.rectangle([x_pos, table_y, x_pos + sum(col_widths), table_y + row_height], fill=table_header_color)
    for i, header in enumerate(headers):
        draw_spaced_text(draw, (x_pos + col_widths[i]//2 - 25, table_y + 5), header, table_font, text_color, spacing=2, anchor=None)
        x_pos += col_widths[i]

    current_y = table_y + row_height
    for idx, item in enumerate(gate_pass_data['items']):
        x_pos = width//2 + 10
        row_color = (255, 255, 255) if idx % 2 == 0 else (245, 250, 255)
        draw.rectangle([x_pos, current_y, x_pos + sum(col_widths), current_y + row_height], fill=row_color, outline=(200, 200, 200), width=1)

        cell_values = [
            str(item.get('Quantity', '')),
            str(item.get('Description', '')),
            str(item.get('Total Value', '')),
            str(item.get('Invoice No', ''))
        ]
        for i, val in enumerate(cell_values):
            draw.text((x_pos + 10, current_y + 8), val, fill=text_color, font=table_font)
            x_pos += col_widths[i]
        current_y += row_height

    # --- Signatures ---
    signature_y = height - 220
    draw.rectangle([30, signature_y - 40, width - 30, signature_y - 10], fill=accent_color)
    draw.text((width//2, signature_y - 25), "SIGNATURES", fill=title_color, font=header_font, anchor='mm')

    sig_width = 280
    spacing = 60
    start_x = (width - (3*sig_width + 2*spacing)) // 2
    signatures = [
        ("CERTIFIED BY", "Certifying Officer", gate_pass_data.get('certified_signature')),
        ("AUTHORIZED BY", "Authorizing Manager", gate_pass_data.get('authorized_signature')),
        ("RECEIVED BY", "Receiving Party", gate_pass_data.get('received_signature'))
    ]

    for i, (title, label, signature) in enumerate(signatures):
        x_pos = start_x + i * (sig_width + spacing)
        draw.rectangle([x_pos, signature_y, x_pos + sig_width, signature_y + 90], outline=border_color, width=2)
        draw.text((x_pos + sig_width//2, signature_y - 15), title, fill=header_color, font=normal_font, anchor='mm')

        if signature:
            try:
                sig_img = Image.open(io.BytesIO(base64.b64decode(signature.split(',')[1])))
                sig_img = sig_img.resize((sig_width - 20, 70))
                img.paste(sig_img, (x_pos + 10, signature_y + 10))
            except:
                draw.text((x_pos + sig_width//2, signature_y + 40), "SIGNED", fill=(100, 100, 100), font=normal_font, anchor='mm')
        else:
            draw.text((x_pos + sig_width//2, signature_y + 40), "Signature", fill=(200, 200, 200), font=normal_font, anchor='mm')

        draw.text((x_pos + sig_width//2, signature_y + 110), label, fill=text_color, font=signature_font, anchor='mm')

    # --- Footer ---
    footer_y = height - 40
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((width//2, footer_y), f"Generated: {current_date}", fill=(100, 100, 100), font=signature_font, anchor='mm')

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









