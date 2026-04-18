"""EatWise PCOS — Streamlit UI."""
import os

import streamlit as st
from dotenv import load_dotenv

from discovery import find_places
from nutrition_ai import analyze_image, analyze_text
from phenotype import run_quiz
from scorer import score_food

load_dotenv()
st.set_page_config(page_title="EatWise PCOS", layout="wide")
for k, v in [("phenotype", "insulin_resistant"), ("last_score", None)]:
    if k not in st.session_state:
        st.session_state[k] = v
st.title("EatWise")
with st.sidebar:
    st.markdown("### Phenotype quiz")
    run_quiz()
ph = st.session_state["phenotype"]
ts, td = st.tabs(["Scan", "Discovery"])

with ts:
    mode = st.radio("Input", ["Label photo", "Dish name"], horizontal=True)
    if mode == "Label photo":
        fu, cam = st.file_uploader("Upload", type=["jpg", "jpeg", "png"]), st.camera_input("Camera")
        go = st.button("Analyze label")
        if go:
            raw = fu.getvalue() if fu else (cam.getvalue() if cam else None)
            if not raw:
                st.warning("Add an image.")
            else:
                mime = "image/png" if fu and fu.type == "image/png" else "image/jpeg"
                with st.spinner("Mistral vision…"):
                    try:
                        st.session_state["last_score"] = score_food(ph, analyze_image(raw, mime))
                    except Exception as e:
                        st.error(str(e))
    else:
        dish = st.text_input("Dish")
        if st.button("Analyze dish") and dish:
            with st.spinner("Mistral text…"):
                try:
                    st.session_state["last_score"] = score_food(ph, analyze_text(dish))
                except Exception as e:
                    st.error(str(e))
    r = st.session_state.get("last_score")
    if r:
        with st.container(border=True):
            st.subheader(r["verdict"].upper())
            st.metric("Score", r["score"])
            st.write(r["reason"])
            if r.get("flagged_ingredients"):
                st.caption("Flags: " + ", ".join(r["flagged_ingredients"]))
            if r.get("swap"):
                st.info(r["swap"])

with td:
    zc = st.text_input("Zip", max_chars=10)
    mx = st.slider("Max $ tier", 1, 4, 2)
    if st.button("Find places") and zc:
        if not os.environ.get("YELP_API_KEY"):
            st.error("Set YELP_API_KEY.")
        else:
            with st.spinner("Yelp…"):
                try:
                    rows = find_places(zc, mx, ph)
                    if not rows:
                        st.warning("No matches—try another zip/tier.")
                    for row in rows:
                        with st.container(border=True):
                            nm, pr = row["name"], row.get("price") or "—"
                            st.write(f"**{nm}** ({pr}) ★{row.get('rating')}")
                            st.caption(", ".join(row.get("categories") or []))
                            st.link_button("Yelp", row["url"])
                except Exception as e:
                    st.error(str(e))
