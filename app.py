# app.py
import streamlit as st
from agent_logic import app_engine # Import the engine we just built

# 1. Page Config
st.set_page_config(page_title="ChemE Goldmine", page_icon="⚗️", layout="wide")

# 2. The Header
st.title("⚗️ The Ultimate ChemE Resource Generator")
st.markdown("""
*Built for High-Precision Engineering Studies.* This tool researches **trusted academic sources** to build a complete chapter for you.
""")

# 3. User Input
topic = st.text_input("Enter Topic (e.g., 'Distillation Columns', 'Fluid Catalytic Cracking')", value="")

# 4. The "Go" Button
if st.button("Generate Chapter Resource"):
    if not topic:
        st.error("Please enter a topic!")
    else:
        # Create a status container
        status = st.status("Initializing Agent...", expanded=True)
        
        # Run the Agent
        try:
            status.write("🧠 Planner: Structuring the chapter...")
            inputs = {"topic": topic}
            
            # This executes the workflow we built in agent_logic.py
            result = app_engine.invoke(inputs)
            
            status.write("✅ Complete! Rendering data...")
            status.update(label="Generation Successful", state="complete", expanded=False)
            
            # 5. Display the Output
            st.divider()
            st.markdown(f"# 📘 Comprehensive Notes: {topic}")
            st.markdown(result['final_content'])
            
            # 6. Download Button
            st.download_button(
                label="📥 Download Notes as Markdown",
                data=result['final_content'],
                file_name=f"{topic}_Goldmine_Notes.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            status.update(label="Error Occurred", state="error")
            st.error(f"An error occurred: {e}")