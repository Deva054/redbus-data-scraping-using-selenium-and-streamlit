import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Set up the page configuration
st.set_page_config(page_title="Bus Ticket Booking", page_icon="🚌", layout="wide")

# Custom CSS for luxurious styling
st.markdown("""
    <style>
        /* Set primary background color */
        body {
            background-color: #8B0000;  /* Dark red background */
            color: #FFFFFF;  /* White text */
            font-family: 'Arial', sans-serif;
        }

        /* Title Styling */
        h1 {
            font-size: 2.5rem;
            font-weight: bold;
            color: #000000;
            text-align: center;
        }

        /* Subtitle Styling */
        h2 {
            color: #FFFAFA;  /* Snow white */
        }

        h3 {
            color: #FFFFFF;
        }

        /* Sidebar styling */
        .sidebar .sidebar-content {
            background-color: #4B0000;  /* Slightly darker red for sidebar */
            border-right: 2px solid #FFFAFA;  /* White border */
        }

        .sidebar .sidebar-header {
            background-color: #8B0000;
            color: #FFFFFF;
            font-weight: bold;
        }

        /* Input fields styling in the sidebar */
        .stTextInput, .stTextArea, .stSelectbox, .stMultiselect, .stRadio, .stSlider {
            background-color: #FFFAFA;  /* Soft white */
            color: #8B0000;  /* Text in dark red */
            border: 1px solid #8B0000;
            border-radius: 5px;
            padding: 8px;
            font-size: 1rem;
        }

        /* Button Styling */
        .stButton > button {
            background-color: #B22222;  /* Firebrick red */
            color: #FFFFFF;
            font-size: 1.2rem;
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        .stButton > button:hover {
            background-color: #D2691E;  /* Hover color in a lighter shade */
        }

        /* Dataframe styling */
        .dataframe thead th {
            background-color: #8B0000;  /* Header with luxurious red */
            color: #FFFFFF;
        }

        .dataframe tbody tr:nth-child(odd) {
            background-color: #FFFAFA;  /* Light background for rows */
            color: #8B0000;
        }

        .dataframe tbody tr:nth-child(even) {
            background-color: #FFF5EE;  /* Slightly different light color */
            color: #8B0000;
        }

        .dataframe tbody tr:hover {
            background-color: #FA8072;  /* Hover color for rows */
        }

    </style>
""", unsafe_allow_html=True)


# Connect to MySQL database using SQLAlchemy with error handling
def get_connection():
    try:
        engine = create_engine('mysql+pymysql://root:1234@localhost/redbus')
        return engine
    except SQLAlchemyError as e:
        st.error(f"Error connecting to database: {str(e)}")
        return None


# Function to fetch route names starting with a specific letter, arranged alphabetically
# Function to fetch route names starting with a specific letter, arranged alphabetically
@st.cache_data
def fetch_route_names(_engine, starting_letter):
    query = "SELECT DISTINCT Route_Name FROM bus_routes WHERE Route_Name LIKE %s ORDER BY Route_Name"
    route_names = pd.read_sql(query, _engine, params=(f"{starting_letter}%",))['Route_Name'].tolist()
    return route_names


# Function to fetch data from MySQL based on selected Route_Name and price sort order
@st.cache_data
def fetch_data(_engine, route_name, price_sort_order):
    price_sort_order_sql = "ASC" if price_sort_order == "Low to High" else "DESC"
    query = f"SELECT * FROM bus_routes WHERE Route_Name = %s ORDER BY Star_Rating DESC, Price {price_sort_order_sql}"
    df = pd.read_sql(query, _engine, params=(route_name,))
    return df


# Function to filter data based on Star_Rating and Bus_Type
def filter_data(df, star_ratings, bus_types):
    filtered_df = df[df['Star_Rating'].isin(star_ratings) & df['Bus_Type'].isin(bus_types)]
    return filtered_df


# Main Streamlit app
def main():
    # Page Title and Introduction
    st.title("🚌 Easy and Secure Online Bus Tickets Booking")
    st.markdown("""
    Welcome to the **Bus Tickets Booking System**! Find the best bus routes, compare prices, and book your tickets securely online.
    """)

    # Connect to the database using SQLAlchemy
    engine = get_connection()

    if engine:
        try:
            # Sidebar - Input for starting letter of route names
            st.sidebar.header("Search Bus Routes")
            starting_letter = st.sidebar.text_input('Enter starting letter of Route Name', 'A', max_chars=1)

            # Fetch route names starting with the specified letter
            if starting_letter:
                route_names = fetch_route_names(engine, starting_letter.upper())

                if route_names:
                    # Sidebar - Selectbox for Route_Name
                    selected_route = st.sidebar.radio('Select Route Name', route_names)

                    if selected_route:
                        # Sidebar - Selectbox for sorting preference with icons
                        price_sort_order = st.sidebar.selectbox('Sort by Price', ['Low to High', 'High to Low'], index=0, format_func=lambda x: f"💰 {x}")

                        # Fetch data based on selected Route_Name and price sort order
                        data = fetch_data(engine, selected_route, price_sort_order)

                        if not data.empty:
                            # Convert 'Price' and 'Star_Rating' columns to numeric
                            data['Price'] = pd.to_numeric(data['Price'].replace('INR ', '', regex=True), errors='coerce')
                            data['Star_Rating'] = pd.to_numeric(data['Star_Rating'], errors='coerce')

                            # Display data table with a subheader and customized table style
                            st.subheader(f"🛣️ Data for Route: **{selected_route}**")
                            st.dataframe(data.style.format({"Price": "₹{:.2f}", "Star_Rating": "{:.1f}"}))

                            # Filter by Star_Rating and Bus_Type
                            star_ratings = data['Star_Rating'].unique().tolist()
                            selected_ratings = st.multiselect('Filter by Star Rating 🌟', star_ratings, default=star_ratings)

                            bus_types = data['Bus_Type'].unique().tolist()
                            selected_bus_types = st.multiselect('Filter by Bus Type 🚍', bus_types, default=bus_types)

                            if selected_ratings and selected_bus_types:
                                filtered_data = filter_data(data, selected_ratings, selected_bus_types)
                                # Display filtered data table with a subheader
                                st.subheader(f"🔍 Filtered Data for Star Rating: {selected_ratings} and Bus Type: {selected_bus_types}")
                                st.dataframe(filtered_data.style.format({"Price": "₹{:.2f}", "Star_Rating": "{:.1f}"}))
                        else:
                            st.warning(f"No data found for Route: **{selected_route}** with the specified price sort order.")
                else:
                    st.warning("No routes found starting with the specified letter.")
        finally:
            engine.dispose()  # Close the connection when done
    else:
        st.error("Failed to establish database connection.")

if __name__ == '__main__':
    main()