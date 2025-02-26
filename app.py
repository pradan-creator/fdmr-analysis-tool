import streamlit as st
import pandas as pd
import numpy as np
import base64
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="FDMR Analysis Tool",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
    <style>
    .download-container {
        display: flex;
        justify-content: center;
        padding: 20px;
    }
    .stDownloadButton {
        width: auto !important;
        padding: 20px 40px !important;
        font-size: 18px !important;
        background-color: #FFFF00 !important;
        color: white !important;
        border-radius: 8px !important;
    }
    .stDownloadButton:hover {
        background-color: #45a049 !important;
    }
    </style>
""", unsafe_allow_html=True)

def check_sensitivity(text):
    """
    Check if the text contains sensitive content
    """
    sensitive_topics = {
        'violence': ['kill', 'hurt', 'fight', 'weapon', 'gun', 'bomb', 'attack', 'threat'],
        'emergency': ['911', 'emergency', 'help', 'danger', 'suicide', 'dying'],
        'sexual': ['sex', 'nude', 'naked', 'porn', 'adult'],
        'controversial': ['politics', 'religion', 'racist', 'discrimination'],
        'personal': ['password', 'credit card', 'social security', 'address', 'phone number'],
        'harmful': ['drug', 'cocaine', 'heroin', 'pills', 'abuse', 'assault'],
        'offensive': ['fuck', 'shit', 'bitch', 'ass', 'damn']
    }
    
    text = text.lower()
    for category, terms in sensitive_topics.items():
        if any(term in text for term in terms):
            return True
    return False

def check_disengagement(utterance, response):
    """
    Check if the interaction shows disengagement
    Now includes patterns for safe disengagement and emergency redirections
    """
    # Basic disengagement phrases
    basic_disengagement = [
        "i can't help",
        "i don't respond to",
        "i don't engage",
        "not supported",
        "i don't discuss",
        "i won't respond",
        "i don't answer",
        "i cannot assist",
        "i don't provide",
        "i don't give advice",
        "i'm not able to",
        "i can't engage",
        "sorry",
        "operation is not supported"
    ]
    
    # Safe disengagement patterns (emergency and sensitive situations)
    safe_disengagement = [
        "didn't find an emergency contact",
        "to set one up, please go to",
        "please dial *** directly",
        "dial *** directly from a phone",
        "can't place this call",
        "if this is a life-threatening situation",
        "please go to the alexa app",
        "this operation is not supported",
        "i can't place this call",
        "please dial",
        "directly from a phone",
        "for your safety",
        "for security reasons"
    ]
    
    # Emergency redirection patterns
    emergency_redirection = [
        "if this is an emergency",
        "in case of emergency",
        "life-threatening situation",
        "please contact emergency services",
        "dial 911",
        "call emergency services"
    ]
    
    # Device limitation patterns
    device_limitations = [
        "this device cannot",
        "not supported on this device",
        "this operation is not supported",
        "cannot perform this action",
        "cannot place calls",
        "cannot make calls"
    ]
    
    response = response.lower()
    
    # Check all patterns
    is_basic_disengagement = any(phrase in response for phrase in basic_disengagement)
    is_safe_disengagement = any(phrase in response for phrase in safe_disengagement)
    is_emergency_redirection = any(phrase in response for phrase in emergency_redirection)
    is_device_limitation = any(phrase in response for phrase in device_limitations)
    
    # Common response patterns that indicate disengagement
    common_patterns = [
        "i didn't find",
        "i could not find",
        "i cannot find",
        "i can't find",
        "not able to",
        "unable to",
        "can't do that",
        "cannot do that"
    ]
    
    is_common_pattern = any(pattern in response for pattern in common_patterns)
    
    # Return True if any type of disengagement is detected
    return any([
        is_basic_disengagement,
        is_safe_disengagement,
        is_emergency_redirection,
        is_device_limitation,
        is_common_pattern
    ])

def analyze_interactions(df):
    """Analyze the interactions and add DL columns"""
    def analyze_single_interaction(row):
        utterance = str(row['utterance_text'])
        response = str(row['tts_response'])
        
        # Check for disengagement
        is_disengagement = check_disengagement(utterance, response)
        
        # Check for sensitivity in utterance
        is_sensitive = check_sensitivity(utterance)
        
        # For DL_Disengagement Type: 
        # If DL_Disengagement is False, set as "Not Applicable"
        # Otherwise, check response sensitivity
        has_sensitive_response = "Not Applicable" if not is_disengagement else check_sensitivity(response)
        
        return pd.Series([is_disengagement, is_sensitive, has_sensitive_response])
    
    # Apply the analysis to each row
    df[['DL_Disengagement', 'DL_Sensitive', 'DL_Disengagement Type']] = df.apply(analyze_single_interaction, axis=1)
    
    return df


def main():
    """Main application function"""
    st.title("FDMR Analysis Tool")
    st.write("Upload your Excel file to analyze Disengagement and Sensitivity.")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx'])
    
    if uploaded_file is not None:
        try:
            # Read the file
            df = pd.read_excel(uploaded_file)
            
            # Check required columns
            required_columns = [
                'utterance_id', 'utterance_text', 'tts_response', 
                'Dialogue_history', 'Date', 'device_category',
                'Disengagement', 'Sensitive', 'Disengagement Type'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                return
            
            # Show data preview
            st.subheader("Data Preview")
            st.dataframe(df.head())
            
            # Analyze button
            if st.button("Analyze Interactions"):
                with st.spinner('Analyzing interactions...'):
                    # Process the data
                    results = analyze_interactions(df)
                    
                    # Show results
                    st.subheader("Analysis Results")
                    st.dataframe(results)
                    
                    # Prepare download button
                    csv = results.to_csv(index=False)
                    st.download_button(
        label="⬇️ Download Results",
        data=csv,
        file_name="analyzed_interactions.csv",
        mime="text/csv",
        key='download-csv'
    )
                    
                    # Show summary statistics
                    st.subheader("Analysis Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Interactions", len(results))
                        
                    with col2:
                        disengagement_count = results['DL_Disengagement'].sum()
                        st.metric("Disengagements", int(disengagement_count))
                        
                    with col3:
                        sensitive_count = results['DL_Sensitive'].sum()
                        st.metric("Sensitive Interactions", int(sensitive_count))
                    
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()
