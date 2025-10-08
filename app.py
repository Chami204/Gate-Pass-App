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

# Function to create gate pass image in Landscape A4
def create_gate_pass_image(gate_pass_data):
    # Create landscape A4 size (297x210mm at 300 DPI = 3508x2480 pixels)
    # Using a more manageable size for better performance
    width, height = 2480, 1754  # Landscape A4 at 200 DPI
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Define colors
    title_color = (0, 0, 139)  # Dark Blue
    header_color = (0, 100, 0)  # Dark Green
    border_color = (0, 0, 0)  # Black
    text_color = (0, 0, 0)  # Black
    
    # Try to use Calibri font with larger sizes and letter spacing
    try:
        # Larger font sizes for better readability
        title_font = ImageFont.truetype("calibri.ttf", 100)  # Increased from 32
        header_font = ImageFont.truetype("calibri.ttf", 80)  # Increased from 24
        normal_font = ImageFont.truetype("calibri.ttf", 60)  # Increased from 18 (Calibri 14 equivalent)
        table_font = ImageFont.truetype("calibri.ttf", 60)   # Increased from 16
    except:
        try:
            # Try Arial if Calibri not available
            title_font = ImageFont.truetype("arial.ttf", 100)
            header_font = ImageFont.truetype("arial.ttf", 80)
            normal_font = ImageFont.truetype("arial.ttf", 60)
            table_font = ImageFont.truetype("arial.ttf", 60)
        except:
            # Fallback to default fonts
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()
            table_font = ImageFont.load_default()
    
    # Draw border around entire gate pass
    draw.rectangle([20, 20, width-20, height-20], outline=border_color, width=4)
    
    # Header with colors and better spacing
    draw.text((width//2, 80), "Advice Dispatch Gate Pass", fill=title_color, font=title_font, anchor='mm')
    draw.text((width//2, 140), "Alumex Group", fill=header_color, font=header_font, anchor='mm')
    draw.text((width//2, 190), "Sapugaskanda, Makola", fill=text_color, font=normal_font, anchor='mm')
    draw.text((width//2, 240), "Tel: 2400332,2400333,2400421", fill=text_color, font=normal_font, anchor='mm')
    
    # Separator line
    draw.line([50, 280, width-50, 280], fill=border_color, width=3)
    
    # Basic information with more spacing
    y_position = 330
    draw.text((100, y_position), f"Reference No: {gate_pass_data['reference']}", fill=text_color, font=normal_font)
    y_position += 60  # Increased spacing
    draw.text((100, y_position), f"Requested by: {gate_pass_data['requested_by']}", fill=text_color, font=normal_font)
    y_position += 60  # Increased spacing
    draw.text((100, y_position), f"Send to: {gate_pass_data['send_to']}", fill=text_color, font=normal_font)
    y_position += 60  # Increased spacing
    draw.text((100, y_position), f"Purpose: {gate_pass_data['purpose']}", fill=text_color, font=normal_font)
    y_position += 60  # Increased spacing
    draw.text((100, y_position), f"Return Date: {gate_pass_data.get('return_date', 'Not specified')}", fill=text_color, font=normal_font)
    y_position += 60  # Increased spacing
    draw.text((100, y_position), f"Dispatch Type: {gate_pass_data['dispatch_type']}", fill=text_color, font=normal_font)
    y_position += 60  # Increased spacing
    draw.text((100, y_position), f"Vehicle Number: {gate_pass_data.get('vehicle_number', '')}", fill=text_color, font=normal_font)
    
    # Items table with borders - moved to right side for landscape
    y_position = 330  # Reset to top for right column
    right_column_x = width // 2 + 50
    
    draw.text((right_column_x, y_position), "Items Dispatch Details", fill=header_color, font=header_font)
    y_position += 60
    
    # Table headers with background
    header_bg_color = (240, 240, 240)  # Light gray
    cell_height = 50  # Increased cell height
    col_widths = [120, 400, 200, 200]  # Width for each column
    
    # Table headers
    headers = ["Quantity", "Description", "Total Value", "Invoice No"]
    x_pos = right_column_x
    
    # Draw header background
    draw.rectangle([x_pos, y_position, x_pos + sum(col_widths), y_position + cell_height], fill=header_bg_color, outline=border_color, width=2)
    
    for i, header in enumerate(headers):
        draw.text((x_pos + col_widths[i]//2, y_position + cell_height//2), header, fill=text_color, font=table_font, anchor='mm')
        if i < len(headers) - 1:
            draw.line([x_pos + col_widths[i], y_position, x_pos + col_widths[i], y_position + cell_height], fill=border_color, width=2)
        x_pos += col_widths[i]
    
    y_position += cell_height
    
    # Table rows with borders
    for item in gate_pass_data['items']:
        x_pos = right_column_x
        # Draw row background (alternating colors for better readability)
        row_color = (255, 255, 255) if gate_pass_data['items'].index(item) % 2 == 0 else (250, 250, 250)
        draw.rectangle([x_pos, y_position, x_pos + sum(col_widths), y_position + cell_height], fill=row_color, outline=border_color, width=2)
        
        # Draw cell content with proper spacing
        draw.text((x_pos + col_widths[0]//2, y_position + cell_height//2), str(item.get('Quantity', '')), fill=text_color, font=table_font, anchor='mm')
        x_pos += col_widths[0]
        draw.line([x_pos, y_position, x_pos, y_position + cell_height], fill=border_color, width=2)
        
        draw.text((x_pos + col_widths[1]//2, y_position + cell_height//2), str(item.get('Description', '')), fill=text_color, font=table_font, anchor='mm')
        x_pos += col_widths[1]
        draw.line([x_pos, y_position, x_pos, y_position + cell_height], fill=border_color, width=2)
        
        draw.text((x_pos + col_widths[2]//2, y_position + cell_height//2), str(item.get('Total Value', '')), fill=text_color, font=table_font, anchor='mm')
        x_pos += col_widths[2]
        draw.line([x_pos, y_position, x_pos, y_position + cell_height], fill=border_color, width=2)
        
        draw.text((x_pos + col_widths[3]//2, y_position + cell_height//2), str(item.get('Invoice No', '')), fill=text_color, font=table_font, anchor='mm')
        
        y_position += cell_height
    
    # Signatures section at bottom
    signature_y = height - 350
    signature_title_y = signature_y - 40
    
    # Signature titles
    draw.text((width//6, signature_title_y), "Certified by", fill=header_color, font=normal_font, anchor='mm')
    draw.text((width//2, signature_title_y), "Authorized by", fill=header_color, font=normal_font, anchor='mm')
    draw.text((5*width//6, signature_title_y), "Received by", fill=header_color, font=normal_font, anchor='mm')
    
    # Signature boxes with borders
    sig_box_width = 300
    sig_box_height = 120
    
    # Certified Signature
    cert_x = width//6 - sig_box_width//2
    draw.rectangle([cert_x, signature_y, cert_x + sig_box_width, signature_y + sig_box_height], outline=border_color, width=3)
    if gate_pass_data.get('certified_signature'):
        try:
            sig_img = Image.open(io.BytesIO(base64.b64decode(gate_pass_data['certified_signature'].split(',')[1])))
            sig_img = sig_img.resize((sig_box_width - 20, sig_box_height - 20))
            img.paste(sig_img, (cert_x + 10, signature_y + 10))
        except:
            draw.text((cert_x + sig_box_width//2, signature_y + sig_box_height//2), "Signed", fill=text_color, font=normal_font, anchor='mm')
    
    # Authorized Signature
    auth_x = width//2 - sig_box_width//2
    draw.rectangle([auth_x, signature_y, auth_x + sig_box_width, signature_y + sig_box_height], outline=border_color, width=3)
    if gate_pass_data.get('authorized_signature'):
        try:
            sig_img = Image.open(io.BytesIO(base64.b64decode(gate_pass_data['authorized_signature'].split(',')[1])))
            sig_img = sig_img.resize((sig_box_width - 20, sig_box_height - 20))
            img.paste(sig_img, (auth_x + 10, signature_y + 10))
        except:
            draw.text((auth_x + sig_box_width//2, signature_y + sig_box_height//2), "Signed", fill=text_color, font=normal_font, anchor='mm')
    
    # Received Signature
    rec_x = 5*width//6 - sig_box_width//2
    draw.rectangle([rec_x, signature_y, rec_x + sig_box_width, signature_y + sig_box_height], outline=border_color, width=3)
    if gate_pass_data.get('received_signature'):
        try:
            sig_img = Image.open(io.BytesIO(base64.b64decode(gate_pass_data['received_signature'].split(',')[1])))
            sig_img = sig_img.resize((sig_box_width - 20, sig_box_height - 20))
            img.paste(sig_img, (rec_x + 10, signature_y + 10))
        except:
            draw.text((rec_x + sig_box_width//2, signature_y + sig_box_height//2), "Signed", fill=text_color, font=normal_font, anchor='mm')
    
    return img

# Function to create download link for JPG
def get_jpg_download_link(img, filename, text):
    buffered = io.BytesIO()
    # Save as high quality JPG
    img.save(buffered, format="JPEG", quality=95)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:image/jpeg;base64,{img_str}" download="{filename}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">{text}</a>'
    return href

# Simple canvas component using Streamlit's drawing functionality
def signature_canvas(label, key):
    st.write(f"**{label}**")
    st.write("Draw your signature in the box below:")
    
    # Create a canvas with border
    canvas_style = """
    <style>
    .canvas-container {
        border: 2px solid #000000;
        border-radius: 5px;
        padding: 10px;
        background-color: #ffffff;
    }
    </style>
    """
    st.markdown(canvas_style, unsafe_allow_html=True)
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",  # Transparent background
        stroke_width=3,  # Thicker strokes for better visibility
        stroke_color="#000000",  # Black color
        background_color="#ffffff",  # White background
        background_image=None,
        update_streamlit=True,
        height=150,
        width=300,
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
        
        # Initialize session state for items if not exists - start with 5 empty rows
        if 'items_df' not in st.session_state:
            st.session_state.items_df = pd.DataFrame({
                'Quantity': ['', '', '', '', ''],
                'Description': ['', '', '', '', ''],
                'Total Value': ['', '', '', '', ''],
                'Invoice No': ['', '', '', '', '']
            })
        
        # Editable dataframe for items with more rows and dynamic editing
        st.write("**Add items below (you can add/delete rows as needed):**")
        edited_df = st.data_editor(
            st.session_state.items_df,
            num_rows="dynamic",  # Allows adding and deleting rows
            use_container_width=True,
            key="items_editor",
            column_config={
                "Quantity": st.column_config.TextColumn(width="small"),
                "Description": st.column_config.TextColumn(width="medium"),
                "Total Value": st.column_config.TextColumn(width="medium"),
                "Invoice No": st.column_config.TextColumn(width="medium")
            }
        )
        
        # Certified signature canvas
        st.subheader("Certified Signature")
        certified_canvas = signature_canvas("Draw your signature below:", "certified_canvas_new")
        
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
                # Remove alpha channel and convert to PIL Image
                img_data = certified_canvas.image_data
                if img_data is not None:
                    # Convert to PIL Image and then to base64
                    pil_img = Image.fromarray((img_data[:, :, :3]).astype('uint8'))
                    buffered = io.BytesIO()
                    pil_img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    gate_pass_data['certified_signature'] = f"data:image/png;base64,{img_str}"
            
            if save_gate_pass(gate_pass_data):
                st.success(f"Gate Pass submitted successfully!")
                st.info(f"**Your Reference Number:** {reference}")
                st.warning("Please share this reference number with authorized personnel for signing.")
                
                # Generate and provide download link as JPG
                gate_pass_img = create_gate_pass_image(gate_pass_data)
                st.markdown(get_jpg_download_link(gate_pass_img, f"gate_pass_{reference}.jpg", "📥 Download Gate Pass (JPG)"), unsafe_allow_html=True)
                
                # Reset form with 5 empty rows
                st.session_state.items_df = pd.DataFrame({
                    'Quantity': ['', '', '', '', ''],
                    'Description': ['', '', '', '', ''],
                    'Total Value': ['', '', '', '', ''],
                    'Invoice No': ['', '', '', '', '']
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
                
                # Signature sections with canvas
                st.subheader("Signatures")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Certified by signature**")
                    if gate_pass_data.get('certified_signature'):
                        st.image(gate_pass_data['certified_signature'], width=200)
                    else:
                        st.write("No signature yet")
                
                with col2:
                    authorized_canvas = signature_canvas("Authorized by", "authorized_canvas")
                
                with col3:
                    received_canvas = signature_canvas("Received by", "received_canvas")
                
                if st.button("Submit Signatures"):
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
                            
                            # Generate and provide download link as JPG
                            gate_pass_img = create_gate_pass_image(updated_data)
                            st.success("Signatures submitted successfully! Gate Pass is now completed.")
                            st.markdown(get_jpg_download_link(gate_pass_img, f"gate_pass_{reference_input}.jpg", "📥 Download Completed Gate Pass (JPG)"), unsafe_allow_html=True)
                    else:
                        st.error("Please provide all signatures and vehicle number")
            else:
                st.error("Gate Pass not found. Please check the reference number.")

if __name__ == "__main__":
    main()

