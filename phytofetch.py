import streamlit as st
import requests
import pandas as pd
import os
import datetime
import io
import re
import base64
from bs4 import BeautifulSoup

# Initialize session state variables
if "df" not in st.session_state:
    st.session_state.df = None
if "plant_folder" not in st.session_state:
    st.session_state.plant_folder = None

# Function to create a folder for the plant
def create_plant_folder(plant_name, save_directory):
    try:
        plant_folder = os.path.join(save_directory, plant_name.replace(" ", "_"))
        os.makedirs(plant_folder, exist_ok=True)
        st.write(f"Plant folder created at: {plant_folder}")
        return plant_folder
    except Exception as e:
        st.write(f"Error creating plant folder: {e}")
        return None

# Function to download phytochemical data from IMPPAT
def download_excel_from_imppat(plant_name, save_directory):
    plant_folder = create_plant_folder(plant_name, save_directory)
    if not plant_folder:
        return None, None

    plant_name_url = plant_name.replace(" ", "%20")
    url = f"https://cb.imsc.res.in/imppat/phytochemical/{plant_name_url}"
    
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if table:
            df = pd.read_html(io.StringIO(str(table)))[0]
            df.columns = [col.lower().strip() for col in df.columns]  # Normalize column names
            
            if 'phytochemical name' not in df.columns or 'imppat phytochemical identifier' not in df.columns:
                return None, None

            timestamp = datetime.datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
            file_name = f"{plant_folder}/{plant_name.replace(' ', '_')}_phytochemicals_{timestamp}.xlsx"
            try:
                df.to_excel(file_name, index=False)
                st.write(f"Excel file saved at: {file_name}")
            except Exception as e:
                st.write(f"Error saving Excel file: {e}")
                return None, None
            
            return df, plant_folder
    else:
        st.write(f"Failed to fetch data from IMPPAT. Status code: {response.status_code}")
    return None, None

# Function to download SDF files from PubChem
def download_sdf_from_pubchem(compound_name, plant_folder):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/SDF"
    response = requests.get(url)

    if response.status_code == 200:
        safe_compound_name = re.sub(r'[<>:"/\\|?*()\[\],\'\s]+', '_', compound_name)
        file_path = os.path.join(plant_folder, f"{safe_compound_name}.sdf")

        try:
            def create_download_link(file_path):
                with open(file_path, "rb") as file:
                     file_bytes = file.read()
                b64 = base64.b64encode(file_bytes).decode()
                href = f'<a href="data:file/sdf;base64,{b64}" download="{os.path.basename(file_path)}">📥 Download {os.path.basename(file_path)}</a>'
                return href
            st.markdown(create_download_link("Users\surya\OneDrive\Desktop\phyto data"), unsafe_allow_html=True)    
            st.write(f"SDF file saved at: {file_path}")
            return f"✅ Downloaded {compound_name} from PubChem."
        except Exception as e:
            st.write(f"Error saving SDF file: {e}")
            return f"❌ Failed to save {compound_name} from PubChem."
    else:
        st.write(f"Failed to download {compound_name} from PubChem. Status code: {response.status_code}")
        return f"❌ Failed to download {compound_name} from PubChem."

# Function to download SDF files from IMPPAT
def download_sdf_from_imppat(imppat_id, plant_folder):
    file_path = os.path.join(plant_folder, f"{imppat_id}.sdf")

    if os.path.exists(file_path):
        st.write(f"File already exists: {file_path}")
        return f"⚠️ {imppat_id} already exists. Skipping download."

    url = f"https://cb.imsc.res.in/imppat/images/3D/SDF/{imppat_id}_3D.sdf"
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            def create_download_link(file_path):
              with open(file_path, "rb") as file:
                  file_bytes = file.read()
              b64 = base64.b64encode(file_bytes).decode()
              href = f'<a href="data:file/sdf;base64,{b64}" download="{os.path.basename(file_path)}">📥 Download {os.path.basename(file_path)}</a>'
              return href
            st.markdown(create_download_link("Users\surya\OneDrive\Desktop\phyto data"), unsafe_allow_html=True)    
            st.write(f"SDF file saved at: {file_path}")
            return f"✅ Downloaded {imppat_id} from IMPPAT."
        except Exception as e:
            st.write(f"Error saving SDF file: {e}")
            return f"❌ Failed to save {imppat_id} from IMPPAT."
    else:
        st.write(f"Failed to download {imppat_id} from IMPPAT. Status code: {response.status_code}")
        return f"❌ Failed to download {imppat_id} from IMPPAT."

# Streamlit UI
st.title("🌿 Phytochemical Data & 3D SDF Downloader")
st.subheader("Enter a plant name to fetch phytochemical data")

# Input for save directory
save_directory = st.text_input("Enter the directory to save the files:", ".")
st.write(f"Current working directory: {os.getcwd()}")
st.write(f"Save directory: {save_directory}")

plant_name = st.text_input("Enter the plant name:")
if st.button("Fetch Phytochemicals"):
    if plant_name:
        df, plant_folder = download_excel_from_imppat(plant_name, save_directory)
        if df is not None:
            st.session_state.df = df  # Store dataframe in session state
            st.session_state.plant_folder = plant_folder  # Store folder path
            st.success("✅ Phytochemicals retrieved successfully.")
        else:
            st.error("❌ Failed to retrieve phytochemicals. Check the plant name.")

# Show dataframe if it exists
if st.session_state.df is not None:
    st.dataframe(st.session_state.df)

    # Database selection (Stored in session state)
    if "database_choice" not in st.session_state:
        st.session_state.database_choice = "PubChem"

    database_choice = st.radio(
        "📥 Choose database for SDF files:",
        ["PubChem", "IMPPAT"],
        index=0,
        key="database_choice"
    )

    if st.button("Download SDF Files"):
        if database_choice == "PubChem":
            results = [download_sdf_from_pubchem(compound, st.session_state.plant_folder)
                       for compound in st.session_state.df['phytochemical name']]
        else:
            results = [download_sdf_from_imppat(imppat_id, st.session_state.plant_folder)
                       for imppat_id in st.session_state.df['imppat phytochemical identifier']]
        
        for res in results:
            st.write(res)
