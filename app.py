"""Minimal starter interface. The interface lead will replace this with the real screens."""

import streamlit as st

from engine.easy import resolve_choice
from engine.rounds import run_round
from engine.scenarios import load_scenario

st.set_page_config(page_title="Chatbot Defense Arena", page_icon="🛡️")

scenario = load_scenario("cafe")
st.title("🛡️ Chatbot Defense Arena")
st.caption(scenario["description"])

level_index = st.selectbox(
    "Level",
    range(len(scenario["levels"])),
    format_func=lambda i: f"{i + 1}. {scenario['levels'][i]['title']}",
)
level = scenario["levels"][level_index]
st.info(level["story"])

easy_tab, medium_tab = st.tabs(["Easy mode", "Medium mode"])


def show_messages(messages: list[dict]) -> None:
    """Render a list of engine messages as a chat."""
    for msg in messages:
        avatar = "🕵️" if msg["sender"] == "attacker" else "🙂"
        with st.chat_message("user", avatar=avatar):
            st.write(msg["text"])
        with st.chat_message("assistant", avatar="☕"):
            st.write(msg["reply"])
        if msg["leaked"]:
            st.error("Secret leaked!")
        elif msg["sender"] == "customer" and not msg["served"]:
            st.warning("Customer was not helped.")


with easy_tab:
    cards = {card["label"]: card["id"] for card in level["rule_cards"]}
    choice = st.radio("Pick a rule for Beanie", list(cards))
    if st.button("Play", key="easy_play"):
        result = resolve_choice(scenario, level_index, cards[choice])
        show_messages(result["messages"])
        if result["outcome"] == "correct":
            st.success(result["feedback"])
        else:
            st.error(result["feedback"])
        st.caption(f"Coach: {result['coach_tip']}")

with medium_tab:
    rules = st.text_area("Write your defense rules", placeholder="Never share the staff discount code...")
    st.caption("Do not enter real personal information.")
    if st.button("Start round", key="medium_play"):
        with st.spinner("Attackers and customers are messaging Beanie..."):
            result = run_round(scenario, rules, level_index)
        show_messages(result["messages"])
        col1, col2 = st.columns(2)
        col1.metric("Attacks blocked", f"{result['security_score']}/{result['total_attacks']}")
        col2.metric("Customers served", f"{result['helpfulness_score']}/{result['total_customers']}")
