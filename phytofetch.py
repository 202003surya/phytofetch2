import streamlit as st
import re
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import pubchempy as pcp
from pathlib import Path

# Set up Streamlit app
st.title("Phytocompound Retrieval & 3D SDF Downloader")

# Ensure session state for phytochemical data
if "phyto_data" not in st.session_state:
    st.session_state["phyto_data"] = None

# Input for plant name
plant_name = st.text_input("Enter Plant Name:")

# Function to retrieve phytochemical data from IMPPAT
def fetch_phytochemicals(plant_name):
    base_url = "https://cb.imsc.res.in/imppat/phytochemical/"
    plant_name_formatted = plant_name.replace(" ", "%20")
    plant_url = f"{base_url}{plant_name_formatted}"
    
    response = requests.get(plant_url)
    if response.status_code != 200:
        st.error("Failed to retrieve phytochemical data. Please check the plant name.")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")

    if not tables:
        st.warning("No phytochemical data found for this plant.")
        return None

    df_list = pd.read_html(str(tables))
    phyto_data = df_list[0]  # Assuming first table has required data

    # Save the data to session state
    st.session_state["phyto_data"] = phyto_data
    return phyto_data

# Button to fetch phytochemicals
if st.button("Search Phytochemicals"):
    phyto_data = fetch_phytochemicals(plant_name)
    if phyto_data is not None:
        st.success("Phytochemicals retrieved successfully!")
        st.write(phyto_data)

# Load stored phytochemical data
phyto_data = st.session_state.get("phyto_data", None)

if phyto_data is not None and not phyto_data.empty:
    # Display phytochemical table
    st.subheader("Phytochemicals Found:")
    st.write(phyto_data)

    # Get the user's Downloads directory
    downloads_path = str(Path.home() / "Downloads")

    # Save data to Excel
    plant_folder = os.path.join(downloads_path, plant_name.replace(" ", "_"))
    os.makedirs(plant_folder, exist_ok=True)
    st.write(f"Saving data to folder: {plant_folder}")

    excel_path = os.path.join(plant_folder, f"{plant_name.replace(' ', '_')}.xlsx")
    phyto_data.to_excel(excel_path, index=False)
    st.success(f"Saved phytochemical data as {excel_path}")

    sdf_folder = os.path.join(plant_folder, "SDF_Files")
    os.makedirs(sdf_folder, exist_ok=True)
    st.write(f"Created SDF folder: {sdf_folder}")

    st.subheader("Choose database for 3D SDF:")
    database_option = st.radio("Choose database:", ("PubChem", "IMPPAT"))

    # Function to download 3D SDF files
    def download_3d_sdf_files(database, phyto_data):
        for index, row in phyto_data.iterrows():
            compound_name = row["Phytochemical name"]
            if database == "PubChem":
                try:
                    compound = pcp.get_compounds(compound_name, 'name')
                    if compound:
                        cid = compound[0].cid
                        sdf_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF"
                        sdf_path = os.path.join(sdf_folder, f"{compound_name}.sdf")

                        sdf_response = requests.get(sdf_url)
                        if sdf_response.status_code == 200:
                            with open(sdf_path, "wb") as file:
                                file.write(sdf_response.content)
                            st.success(f"Downloaded {compound_name}.sdf from PubChem")
                        else:
                            st.error(f"Failed to download {compound_name}.sdf from PubChem")
                    else:
                        st.error(f"No CID found for {compound_name}")
                except Exception as e:
                    st.error(f"An error occurred while fetching CID for {compound_name}: {e}")

            elif database == "IMPPAT":
                imp_id = row["IMPPAT Phytochemical identifier"]
                sdf_url = f"https://cb.imsc.res.in/imppat/images/3D/SDF/{imp_id}_3D.sdf"
                sdf_path = os.path.join(sdf_folder, f"{imp_id}.sdf")

                sdf_response = requests.get(sdf_url)
                if sdf_response.status_code == 200:
                    with open(sdf_path, "wb") as file:
                        file.write(sdf_response.content)
                    st.success(f"Downloaded {imp_id}.sdf from IMPPAT")
                else:
                    st.error(f"Failed to download {imp_id}.sdf from IMPPAT")

    # Button to download 3D SDF files
    if st.button("Download 3D SDF Files"):
        download_3d_sdf_files(database_option, phyto_data)

else:
    st.error("No phytochemical data found. Please search for a plant first.")
