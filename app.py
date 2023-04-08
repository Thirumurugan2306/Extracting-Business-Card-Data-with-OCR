import streamlit as st
from PIL import Image
import mysql.connector
import pandas as pd
import pytesseract
import re


def set_page_config():
    im = Image.open("bscrd.png")
    st.set_page_config(
        page_title="Extracting Business Card Data with OCR",
        page_icon=im,
        layout="wide",
    )

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("https://images.unsplash.com/photo-1623305463957-df17547327cb?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80");
            background-attachment: scroll;
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display
    st.title("Extracting Business Card Data with OCR")


def display_navigation():
    menu = ['view', 'Edit&update', 'view the DB', 'Delete']
    choice = st.sidebar.selectbox("Select an option", menu)

    return choice


def image():
    image = st.file_uploader(
        "Upload a business card image", type=["jpg", "jpeg", "png"])
    return image


def create_database():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="siddhu23",
        database="OCR")
    mycursor = mydb.cursor()

    # Create a table to store the business card information
    mycursor.execute("CREATE TABLE IF NOT EXISTS Business_card (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), job_title VARCHAR(255), address VARCHAR(255), postcode VARCHAR(255), phone VARCHAR(255), email VARCHAR(255), website VARCHAR(255), company_name VARCHAR(225))")

    return mydb, mycursor


def extract_information_from_image(uploaded_file):
    image = Image.open(uploaded_file)
    text = pytesseract.image_to_string(image)
    lines = text.split('\n')
    cleaned_data = [item for item in lines if item]

    characters_to_remove = ['&', '~', ',', "'"]
    for i in range(len(cleaned_data)):
        for c in characters_to_remove:
            cleaned_data[i] = cleaned_data[i].replace(c, '')
    phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    website_pattern = r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'

    for item in cleaned_data:
        if re.search(website_pattern, item):
            website = item

        elif re.search(phone_pattern, item):
            phone = item

        elif re.search(email_pattern, item):
            email = item

    cleaned_data.remove(website)
    cleaned_data.remove(phone)
    cleaned_data.remove(email)

    cleaned_data.append(phone)
    cleaned_data.append(email)
    cleaned_data.append(website)

    return cleaned_data


def view(uploaded_file):
    col_1, col_2 = st.columns(2)
    with col_1:
        if st.button("Click here to view the image"):
            with col_2:
                st.image(uploaded_file, caption='Uploaded business card image',
                         use_column_width=True)
    with col_1:
        if st.button("Click here to Extract"):
            with col_2:
                cleaned_data = extract_information_from_image(uploaded_file)
                st.write("Name:", cleaned_data[0])
                st.write("Job Title:", cleaned_data[1])
                st.write("Address:", cleaned_data[2])
                st.write("Postcode:", cleaned_data[3])
                st.write("company_name:", cleaned_data[4])
                st.write("Phone:", cleaned_data[5])
                st.write("Email:", cleaned_data[6])
                if len(cleaned_data) <= 7:
                    st.write("Website:", "none")
                else:
                    st.write("Website:", cleaned_data[7])
                st.success(
                    "Business card information Extracted succesfully.")


def Edit(uploaded_file):
    cleaned_data = extract_information_from_image(uploaded_file)
    # Get new information for the business card
    name = st.text_input("Name:", cleaned_data[0])
    job_title = st.text_input("Job Title:", cleaned_data[1])
    address = st.text_input("Address:", cleaned_data[2])
    postcode = st.text_input("Postcode", cleaned_data[3])
    company_name = st.text_input(
        "Company Name", cleaned_data[4])
    phone = st.text_input("Phone", cleaned_data[5])
    email = st.text_input("Email", cleaned_data[6])
    if len(cleaned_data) <= 7:
        website = st.text_input("Website", "None")
    else:
        website = st.text_input("Website", cleaned_data[7])

    if st.button("click to upload"):
        sql = "INSERT INTO Business_card(name, job_title, address, postcode, company_name, phone, email, website) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (name, job_title, address, postcode,
               company_name, phone, email, website)

        mydb, mycursor = create_database()
        mycursor.execute(sql, val)
        mydb.commit()
        st.success("Business card information successfully uploaded to database.")


def view_db():
    mydb, mycursor = create_database()
    mycursor.execute("SELECT * FROM Business_card")
    result = mycursor.fetchall()
    df = pd.DataFrame(result, columns=[
                      'id', 'name', 'job_title', 'address', 'postcode', 'phone', 'Email', 'Website', 'company_name'])
    df = df.drop('id', axis=1)
    st.write(df)


def delete():
    mydb, mycursor = create_database()
    # Create a dropdown menu to select a business card to delete
    mycursor.execute("SELECT id, name FROM Business_card")
    result = mycursor.fetchall()
    business_cards = {}
    for row in result:
        business_cards[row[0]] = row[1]
    selected_card_id = st.selectbox("Select a business card to delete", list(
        business_cards.keys()), format_func=lambda x: business_cards[x])

    # Get the name of the selected business card
    mycursor.execute(
        "SELECT name FROM Business_card WHERE id=%s", (selected_card_id,))
    result = mycursor.fetchone()
    selected_card_name = result[0]

    # Display the current information for the selected business card
    st.write("Name:", selected_card_name)
    # Display the rest of the information for the selected business card

    # Create a button to confirm the deletion of the selected business card
    if st.button("Delete Business Card"):
        mycursor.execute("DELETE FROM Business_card WHERE name=%s",
                         (selected_card_name,))
        mydb.commit()
        st.success("Business card information deleted Successfully.")


if __name__ == '__main__':
    set_page_config()
    uploaded_file = image()
    choice = display_navigation()
    if choice == "view":
        view(uploaded_file)
    if choice == "Edit&update":
        Edit(uploaded_file)
    if choice == "view the DB":

        view_db()
    if choice == "Delete":
        delete()
