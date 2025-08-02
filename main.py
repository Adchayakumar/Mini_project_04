import streamlit as st
import pandas as pd
import numpy as np
import os

# Load clustered data with corrected path
@st.cache_data
def load_data():
    file_path = 'C:/Users/Admin/OneDrive/Desktop/swiggy_restarunt/swiggy_restaurants_clustered.csv'
    df = pd.read_csv(file_path)
    
    # Convert cuisine to list if needed
    if isinstance(df['cuisine'].iloc[0], str):
        df['cuisine'] = df['cuisine'].apply(lambda x: x.strip("[]").replace("'", "").split(", "))
    return df

df = load_data()

# Function to generate cluster labels based on characteristics
def generate_cluster_labels(cluster_df):
    cluster_labels = {}
    for cluster_id in cluster_df['cluster'].unique():
        cluster_data = cluster_df[cluster_df['cluster'] == cluster_id]
        
        # Calculate cluster characteristics
        avg_rating = cluster_data['rating'].mean()
        avg_cost = cluster_data['cost'].mean()
        
        # Get top 3 cuisines
        all_cuisines = [item for sublist in cluster_data['cuisine'].dropna() for item in sublist]
        if all_cuisines:
            top_cuisines = pd.Series(all_cuisines).value_counts().head(3).index.tolist()
            cuisine_str = ", ".join(top_cuisines)
        else:
            cuisine_str = "Varied"
        
        # Create descriptive label
        cost_category = "Premium" if avg_cost > 350 else "Mid-range" if avg_cost > 200 else "Budget"
        rating_category = "Top Rated" if avg_rating > 4.2 else "Good" if avg_rating > 3.8 else "Average"
        
        cluster_labels[cluster_id] = f"{cost_category} • {rating_category} • {cuisine_str}"
    
    return cluster_labels

# Streamlit app
st.title("🍜 Swiggy Restaurant Explorer")
st.subheader("Discover restaurants with similar profiles in your city")

# City selection
cities = sorted(df['city'].unique())
selected_city = st.selectbox("Select a City", cities, index=0)

# Filter data for selected city
city_df = df[df['city'] == selected_city]

if not city_df.empty:
    # Generate descriptive cluster labels
    cluster_labels = generate_cluster_labels(city_df)
    
    # Cluster selection with descriptive labels
    cluster_options = sorted(city_df['cluster'].unique())
    selected_cluster = st.selectbox(
        "Select Restaurant Profile", 
        options=cluster_options,
        format_func=lambda x: f"{cluster_labels[x]} ({len(city_df[city_df['cluster']==x])} restaurants)"
    )
    
    # Filter restaurants in selected cluster
    cluster_df = city_df[city_df['cluster'] == selected_cluster]

    # Sort by rating and popularity
    cluster_df = cluster_df.sort_values(
        by=['rating', 'rating_count'], 
        ascending=[False, False]
    ).reset_index(drop=True)

    # Display cluster characteristics
    st.subheader(f"Profile Characteristics: {cluster_labels[selected_cluster]}")
    
    # Calculate metrics
    avg_rating = cluster_df['rating'].mean()
    avg_cost = cluster_df['cost'].mean()
    all_cuisines = [item for sublist in cluster_df['cuisine'].dropna() for item in sublist]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Average Rating", f"{avg_rating:.1f}/5")
    col2.metric("Average Cost", f"₹{avg_cost:.0f} for two")
    col3.metric("Restaurants", len(cluster_df))
    
    # Show top cuisines
    if all_cuisines:
        top_cuisines = pd.Series(all_cuisines).value_counts().head(5).index.tolist()
        st.write(f"**Popular Cuisines:** {', '.join(top_cuisines)}")

    # Show restaurants in the cluster with links
    st.subheader(f"Restaurants in this Profile")
    
    # Create display dataframe with clickable links
    display_df = cluster_df[['name', 'rating', 'rating_count', 'cost', 'cuisine']].copy()
    display_df['link'] = cluster_df['link']  # Add link column
    
    # Format columns
    display_df['cost'] = display_df['cost'].apply(lambda x: f"₹{x}")
    display_df['cuisine'] = display_df['cuisine'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    
    # Create clickable links
    def make_clickable(url, name):
        return f'<a target="_blank" href="{url}">{name}</a>'
    
    display_df['restaurant'] = display_df.apply(
        lambda x: make_clickable(x['link'], x['name']), 
        axis=1
    )
    
    # Display styled dataframe
    st.write(
        display_df[['restaurant', 'rating', 'rating_count', 'cost', 'cuisine']].to_html(
            escape=False, 
            index=False,
            formatters={
                'rating': '{:.1f}⭐'.format,
                'rating_count': lambda x: f"{x} reviews"
            }
        ),
        unsafe_allow_html=True
    )
    
    # Add some spacing
    st.write("")
    
    # Download button
    st.download_button(
        label="Download These Recommendations",
        data=cluster_df.to_csv(index=False).encode('utf-8'),
        file_name=f'swiggy_{selected_city}_{cluster_labels[selected_cluster]}.csv'.replace(" • ", "_"),
        mime='text/csv'
    )
    
    # Explanation of profiles
    st.subheader("About Restaurant Profiles")
    st.info("""
    **How profiles work:**
    - We group restaurants with similar characteristics like price range, ratings, and cuisine types
    - This helps you find places you'll love based on your preferences
    - Select different profiles to explore various dining experiences
    """)
    
else:
    st.warning(f"No restaurants found in {selected_city}")

# Add footer
st.markdown("---")
st.caption("Swiggy Restaurant Explorer • Find your next favorite meal!")