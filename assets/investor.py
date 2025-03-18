import streamlit as st
import openai
import os
from dotenv import load_dotenv
import pickle
import pandas as pd

############################
# 1) LOAD YOUR CSVs
############################
df_london = pd.read_csv("london_listings.csv")
df_paris = pd.read_csv("paris_listings.csv")  # Always load Paris CSV

def generate_csv_summary(df, city_name):
    """
    Summarize the Airbnb CSV (by neighbourhood & room_type).
    """
    grouped = (
        df.groupby(["neighbourhood", "room_type"])["price"]
          .agg(["mean", "count"])
          .reset_index()
          .rename(columns={"mean": "avg_price", "count": "listings_count"})
    )
    lines = [f"Summary of {city_name} data (by neighbourhood & room_type):"]
    for _, row in grouped.iterrows():
        nb = row["neighbourhood"]
        rt = row["room_type"]
        avgp = row["avg_price"]
        cnt = row["listings_count"]
        lines.append(f"- {nb} / {rt}: Average Price = £{avgp:.2f}, Listings = {cnt}")
    return "\n".join(lines)

def get_df_for_city(city):
    """
    Return the raw DataFrame for the chosen city.
    """
    if city == "London":
        return df_london
    elif city == "Paris":
        return df_paris
    return None

############################
# 2) LOAD OPENAI KEY
############################
load_dotenv("OPEN_API_KEY.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

############################
# 3) PAGE CONFIG
############################
st.set_page_config(page_title="Airbnb Investment Advisor", page_icon="🏡", layout="wide")

############################
# 4) AUTHENTICATION
############################
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

valid_users = {"KPMG": "AIRBNB", "Leire Diez": "AIRBNB"}

if not st.session_state.authenticated:
    st.image("assets/airbnb_banner.png", use_container_width=True)
    st.markdown(
        "<h1 style='margin-top:20px; text-align:center; font-weight:bold;'>Airbnb Smart Investment Chatbot</h1>", 
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <p style='text-align:center; color:#333333; font-size:16px; line-height:1.6;'>
            Welcome to the <strong>Airbnb Investment Advisor</strong>, your personalized professional chatbot 
            designed specifically for real estate investors seeking data-driven, actionable insights 
            to maximize their Airbnb investments.
        </p>
        """,
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        if st.button("LOG IN"):
            if username_input in valid_users and valid_users[username_input] == password_input:
                st.session_state.authenticated = True
                st.session_state.username = username_input
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")
    st.stop()

############################
# 5) AFTER AUTH
############################
else:
    # Sidebar
    st.sidebar.success(f"✅ You're logged in as {st.session_state.username}")
    if st.sidebar.button("LOG OUT"):
        st.session_state.authenticated = False
        for key in ["city_selected", "messages", "question_asked", "csv_summary", "csv_info", "show_map"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.sidebar.image("assets/airbnb_logo.png", use_container_width=True)

    # ---- CITY SELECTION WITH SUBHEADER ----
    st.sidebar.subheader("Select a City")
    if "city_selected" not in st.session_state:
        st.session_state.city_selected = None

    chosen_city = st.sidebar.selectbox(
        "",
        options=["None", "London", "Paris"],
        index=0 if st.session_state.city_selected is None else (
            1 if st.session_state.city_selected == "London" else 2
        )
    )

    # HOME BUTTON: Resets city to None, returning to landing page
    if st.sidebar.button("Go to the Homepage"):
        st.session_state.city_selected = None
        st.rerun()

    if chosen_city == "None":
        if st.session_state.city_selected is not None:
            st.session_state.city_selected = None
            st.rerun()
    else:
        if chosen_city != st.session_state.city_selected:
            st.session_state.city_selected = chosen_city
            for key in ["messages", "question_asked", "csv_summary", "csv_info", "show_map"]:
                st.session_state.pop(key, None)
            st.rerun()

    # Load data if city chosen
    df_current = get_df_for_city(st.session_state.city_selected)

    # Generate summary once
    if df_current is not None and "csv_summary" not in st.session_state:
        summary_text = generate_csv_summary(df_current, st.session_state.city_selected)
        st.session_state["csv_summary"] = summary_text

    # ---- PROPERTY DETAILS WITH EXPANDER ----
    if df_current is not None:
        with st.sidebar.expander("Enter Property Details (Optional)", expanded=False):
            possible_neighborhoods = sorted(df_current["neighbourhood"].dropna().unique())
            possible_room_types = sorted(df_current["room_type"].dropna().unique())

            selected_neighborhood = st.selectbox("Neighborhood", possible_neighborhoods)
            selected_room_type = st.selectbox("Property Type", possible_room_types)

            if st.button("Get Insights"):
                df_filtered = df_current[
                    (df_current["neighbourhood"] == selected_neighborhood)
                    & (df_current["room_type"] == selected_room_type)
                ]
                if not df_filtered.empty:
                    average_price = df_filtered["price"].mean()
                else:
                    average_price = df_current["price"].mean()

                predicted_price = average_price
                monthly_revenue = predicted_price * 20

                st.sidebar.success(f"**Estimated Nightly Price:** £{predicted_price:.2f}")
                st.sidebar.info(f"**Estimated Monthly Revenue:** £{monthly_revenue:.2f}")

                st.session_state["csv_info"] = (
                    f"For neighborhood '{selected_neighborhood}' and property type '{selected_room_type}', "
                    f"the average nightly price is £{predicted_price:.2f}. Estimated monthly revenue is £{monthly_revenue:.2f}."
                )

    # MAIN CONTENT
    if st.session_state.city_selected is None:
        st.image("assets/airbnb_banner.png", use_container_width=True)
        st.title("Airbnb Smart Investment Advisor")
        st.markdown(
            """
            **Welcome!**

            This AI assistant is designed to help you make more strategic, data-driven decisions about Airbnb property investments. 
            By analyzing real-time market data, property prices, and trends in popular neighborhoods, the chatbot provides:

            - **Financial Analyses:** Potential ROI, monthly revenue, and break-even points based on local property values.
            - **ROI Estimates:** Understand how quickly you can recover your investment under different market conditions.
            - **Neighborhood Comparisons:** Compare areas by average prices, demand levels, and potential profitability.
            - **Personalized Recommendations:** Receive advice on the best property types, budgets, or locations to maximize returns.

            ---
            ### How the App Works

            1. **Select a City (Sidebar):**  
               Use the dropdown in the sidebar to choose a city. The app automatically loads 
               summarized Airbnb data for that location, including average prices and listing counts.

            2. **(Optional) Enter Property Details:**  
               If you want a more specific analysis, expand **"Enter Property Details"** in the sidebar. Select a 
               neighborhood and property type to see an **estimated nightly price** and **monthly revenue**.

            3. **Chat with the AI Assistant:**  
               In the main area, you can ask questions about ROI predictions, neighborhood comparisons, or any Airbnb 
               investment topic. The assistant references the summarized dataset and, if missing certain info, will 
               provide approximate numeric or percentage-based insights from external sources.

            4. **Check Example Questions:**  
               If you’re unsure what to ask, open the **"Example Questions"** expanders for typical queries.

            ---       
            **Please now use the sidebar to select a city.**
            """
        )
    else:
        # Show city-specific banner
        if st.session_state.city_selected == "London":
            st.image("assets/london_banner.png", use_container_width=True)
        elif st.session_state.city_selected == "Paris":
            st.image("assets/paris_banner.png", use_container_width=True)

        st.title("Airbnb Smart Investment Chatbot")
        st.markdown(f"**Selected city:** {st.session_state.city_selected}")

        # Toggle logic for the MAP (no st.experimental_rerun)
        if "show_map" not in st.session_state:
            st.session_state["show_map"] = False

        import plotly.express as px

        # Build a cleaned DataFrame for the map
        if df_current is not None:
            df_map = df_current.copy()
            df_map["price"] = pd.to_numeric(df_map["price"], errors="coerce")
            df_map.dropna(subset=["price", "latitude", "longitude"], inplace=True)

        # If show_map is True, show the map page
        if st.session_state["show_map"]:
            st.title(f"Interactive Map of {st.session_state.city_selected}")

            fig = px.scatter_mapbox(
                df_map,
                lat="latitude",
                lon="longitude",
                color="price",
                size="price",
                color_continuous_scale=px.colors.cyclical.IceFire,
                size_max=15,
                zoom=10,
                mapbox_style="carto-positron",
                hover_name="neighbourhood",
                hover_data={
                    "price": True,
                    "latitude": False,
                    "longitude": False
                },
                title=(
                    f"Interactive Map of {st.session_state.city_selected} Listings "
                    "Colored by Average Price and Sized by Average Price"
                )
            )
            st.plotly_chart(fig)

            if st.button("Back to Chatbot"):
                st.session_state["show_map"] = False

            st.stop()

        # Light-Blue Buttons for "Explore London Map" or "Explore Paris Map"
        st.markdown(
            """
            <style>
            button[aria-label='Explore London Map'],
            button[aria-label='Explore Paris Map'] {
                background-color: #87CEFA !important; /* Light Blue */
                color: white !important;
                border: none !important;
                font-size: 1rem !important;
                border-radius: 0.5rem !important;
                cursor: pointer !important;
                margin-top: 10px !important;
            }
            button[aria-label='Explore London Map']:hover,
            button[aria-label='Explore Paris Map']:hover {
                background-color: #00BFFF !important; /* Deep Sky Blue */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # City-specific Explore Map button
        if st.session_state.city_selected == "London":
            if st.button("Explore London Map", key="explore_map_london"):
                st.session_state["show_map"] = True
        elif st.session_state.city_selected == "Paris":
            if st.button("Explore Paris Map", key="explore_map_paris"):
                st.session_state["show_map"] = True

        # Chatbot logic
        if "question_asked" not in st.session_state:
            st.session_state.question_asked = False

        if not st.session_state.question_asked:
            if st.session_state.city_selected == "London":
                with st.expander("Example Questions for London", expanded=False):
                    st.markdown(
                        """
                        <strong>🏡 Neighborhood & Market Analysis (London):</strong>
                        <ul style='color:#333333; font-size:15px;'>
                            <li><em>'Which neighborhood in London has the highest Airbnb occupancy rate?'</em></li>
                            <li><em>'What are the best areas in London for Airbnb investment in 2025?'</em></li>
                            <li><em>'How do occupancy rates compare between Shoreditch, Soho, and Camden?'</em></li>
                        </ul>
                        <strong>💰 Financial & ROI Analysis:</strong>
                        <ul style='color:#333333; font-size:15px;'>
                            <li><em>'What is the expected ROI for a £500,000 property in London?'</em></li>
                            <li><em>'How long does it take to recover my investment for an Airbnb in Westminster?'</em></li>
                            <li><em>'How do property taxes and maintenance costs impact Airbnb profitability in London?'</em></li>
                        </ul>
                        <strong>🔍 Personalized Investment Recommendations:</strong>
                        <ul style='color:#333333; font-size:15px;'>
                            <li><em>'I have a £750,000 budget. Which area in London offers the best Airbnb returns?'</em></li>
                            <li><em>'Is it better to invest in a studio or a two-bedroom apartment for Airbnb in London?'</em></li>
                            <li><em>'Which neighborhoods in London offer the best balance between affordability and high demand?'</em></li>
                        </ul>
                        <strong>⚠️ Regulation & Legal Checks:</strong>
                        <ul style='color:#333333; font-size:15px;'>
                            <li><em>'Are there any short-term rental restrictions in Westminster?'</em></li>
                            <li><em>'Can I legally list my property as an Airbnb in central London?'</em></li>
                        </ul>
                        """,
                        unsafe_allow_html=True
                    )
            else:  # Paris
                with st.expander("Example Questions for Paris", expanded=False):
                    st.markdown(
                        """
                        <strong>🏡 Neighborhood & Market Analysis (Paris):</strong>
                        <ul style='color:#333333; font-size:15px;'>
                            <li><em>'Which arrondissement in Paris has the highest Airbnb occupancy rate?'</em></li>
                            <li><em>'What are the best areas in Paris for Airbnb investment in 2025?'</em></li>
                            <li><em>'How do occupancy rates compare between Le Marais, Montmartre, and the Latin Quarter?'</em></li>
                        </ul>
                        <strong>💰 Financial & ROI Analysis:</strong>
                        <ul style='color:#333333; font-size:15px;'>
                            <li><em>'What is the expected ROI for a €600,000 apartment in Paris?'</em></li>
                            <li><em>'How long does it take to recover my investment for an Airbnb near the Eiffel Tower?'</em></li>
                            <li><em>'How do property taxes and maintenance costs impact Airbnb profitability in Paris?'</em></li>
                        </ul>
                        <strong>🔍 Personalized Investment Recommendations:</strong>
                        <ul style='color:#333333; font-size:15px;'>
                            <li><em>'I have a €750,000 budget. Which area in Paris offers the best Airbnb returns?'</em></li>
                            <li><em>'Is it better to invest in a studio or a two-bedroom apartment for Airbnb in Paris?'</em></li>
                            <li><em>'Which arrondissements in Paris offer the best balance between affordability and high demand?'</em></li>
                        </ul>
                        <strong>⚠️ Regulation & Legal Checks:</strong>
                        <ul style='color:#333333; font-size:15px;'>
                            <li><em>'Are there any short-term rental restrictions in central Paris?'</em></li>
                            <li><em>'Can I legally list my property as an Airbnb near the Champs-Élysées?'</em></li>
                        </ul>
                        """,
                        unsafe_allow_html=True
                    )

        if st.session_state.city_selected is not None:
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Display chat history
            for message in st.session_state.messages:
                if message["role"] == "user":
                    # Right-aligned, pink background
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.empty()
                    with col2:
                        st.markdown(
                            f"<div style='text-align: right; "
                            f"background-color:mistyrose; "
                            f"padding: 10px; "
                            f"border-radius: 10px; "
                            f"margin-bottom: 10px;'>"
                            f"{message['content']}</div>",
                            unsafe_allow_html=True
                        )
                else:
                    # Assistant (chatbot) message
                    col1, col2 = st.columns([1, 15])
                    with col1:
                        st.image("assets/robot_pet.png", width=200)
                    with col2:
                        # Light blue background
                        st.markdown(
                            f"<div style='background-color:#E1F5FE; "
                            f"padding: 10px; "
                            f"border-radius: 10px; "
                            f"margin-bottom: 10px;'>"
                            f"{message['content']}</div>",
                            unsafe_allow_html=True
                        )

            user_input = st.chat_input("Write here...")

            def chat_with_gpt(prompt):
                city = st.session_state.city_selected
                csv_summary = st.session_state.get("csv_summary", "")
                csv_info = st.session_state.get("csv_info", "")

                system_message = (
                    f"You are an Airbnb Investment Advisor for {city}.\n\n"
                    f"Below is the summarized CSV data for all listings:\n{csv_summary}\n\n"
                    f"Additionally, optional snippet: {csv_info}\n\n"
                    "If the CSV does not have certain data (like occupancy rates), disclaim that Airbnb does not "
                    "provide those data points in this dataset, but you can approximate from external sources "
                    "using numeric or percentage-based insights. Always provide numeric or percentage-based data if possible. "
                    "Be concise, professional, and directly to the point. Present key details and the final most important output in bold or bullet points."
                )
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response["choices"][0]["message"]["content"]

            if user_input:
                st.session_state.question_asked = True
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.empty()
                with col2:
                    st.markdown(
                        f"<div style='text-align: right; background-color:mistyrose; "
                        f"padding: 10px; border-radius: 10px; margin-bottom: 10px;'>"
                        f"{user_input}</div>",
                        unsafe_allow_html=True
                    )
                st.session_state.messages.append({"role": "user", "content": user_input})

                response = chat_with_gpt(user_input)

                col1, col2 = st.columns([1, 15])
                with col1:
                    st.image("assets/robot_pet.png", width=200)
                with col2:
                    st.markdown(
                        f"<div style='background-color:#E1F5FE; padding: 10px; border-radius: 10px; margin-bottom: 10px;'>"
                        f"{response}</div>",
                        unsafe_allow_html=True
                    )

                st.session_state.messages.append({"role": "assistant", "content": response})

