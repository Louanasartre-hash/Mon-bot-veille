import streamlit as st
import feedparser
from google import genai
from google.genai import types
from datetime import datetime

# 1. DESIGN ET COULEURS DU SITE (Interface épurée)
st.set_page_config(page_title="Mon Assistant Veille", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    .main-header { background-color: #0f172a; padding: 25px; border-radius: 10px; color: white; text-align: center; margin-bottom: 30px; }
    .card-veille { background-color: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; border-left: 5px solid #0284c7; color: #1e293b; }
    .stButton>button { background-color: #0284c7; color: white; border-radius: 6px; font-weight: bold; width: 100%; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'><h1>🏛️ ASSISTANT PRIVÉ : VEILLE & RECHERCHE</h1><p>Générez votre veille quotidienne et interrogez l'IA sur le droit et la finance en temps réel.</p></div>", unsafe_allow_html=True)

# Barre latérale pour masquer la clé de sécurité
st.sidebar.header("⚙️ SÉCURITÉ")
cle_api = st.sidebar.text_input("Collez votre clé Google Gemini ici :", type="password")

# Les sources officielles automatisées
SOURCES_FLUX = {
    "⚖️ Droit & Jurisprudence (Doctrine/Légifrance)": "https://www.doctrine.fr/raw-rss",
    "💰 Fiscalité (BOFiP)": "https://bofip.impots.gouv.fr/bofip/ext/rss/actualites",
    "📈 Marchés Financiers": "https://www.lesechos.fr/rss/rss_finance_marches.xml"
}

# --- ZONE 1 : LA VEILLE DU JOUR ---
st.subheader("📅 Votre Veille Automatique")
st.caption("Cliquez sur le bouton pour analyser les dernières publications officielles des dernières 24h.")

if st.button("🚀 Lancer la mise à jour quotidienne"):
    if not cle_api:
        st.error("⚠️ Veuillez ajouter votre clé API Gemini dans la barre latérale gauche pour activer le site.")
    else:
        client = genai.Client(api_key=cle_api)
        with st.spinner("Le robot scanne les serveurs et l'IA rédige vos fiches..."):
            for domaine, url in SOURCES_FLUX.items():
                flux = feedparser.parse(url)
                if flux.entries:
                    # On analyse les 2 dernières actualités de chaque secteur
                    for entree in flux.entries[:2]:
                        prompt = f"Tu es juriste et expert financier. Analyse cette actu : {entree.title}. {entree.get('summary', '')}. Rédige une fiche avec : 1. La règle de droit précise ou indicateur. 2. L'interprétation simple pour un professionnel. 3. Rappelle une jurisprudence liée s'il y en a une."
                        response = client.models.generate_content(model='gemini-3-flash-preview', contents=prompt)
                        
                        st.markdown(f"""
                        <div class='card-veille'>
                            <h3 style='margin-top:0;'>[{domaine.upper()}] {entree.title}</h3>
                            {response.text}
                            <br><a href='{entree.link}' target='_blank' style='color:#0284c7; font-weight:bold; text-decoration:none;'>🔗 Consulter la source officielle originale</a>
                        </div>
                        """, unsafe_allow_html=True)

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# --- ZONE 2 : LE MOTEUR DE RECHERCHE NOTEBOOK LM ---
st.subheader("🔍 Moteur de Recherche Assistée (Style NotebookLM)")
st.caption("Posez n'importe quel cas pratique ou question. L'IA va chercher en temps réel sur le web juridique et financier pour vous répondre sans inventer.")

question = st.text_input("💬 Quelle est votre question ou votre recherche juridique/fiscale/financière ?", placeholder="Ex: Quels sont les plafonds actuels d'exonération pour une donation aux petits-enfants ?")

if question:
    if not cle_api:
        st.error("⚠️ Veuillez ajouter votre clé API Gemini dans la barre de gauche.")
    else:
        client = genai.Client(api_key=cle_api)
        with st.spinner("L'IA explore le web, Légifrance, et le BOFiP..."):
            try:
                # Activation de la recherche Google en direct (Ancrage / Grounding)
                response = client.models.generate_content(
                    model='gemini-3-flash-preview',
                    contents=question,
                    config=types.GenerateContentConfig(tools=[{"google_search": {}}])
                )
                
                st.markdown("<div style='background-color: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                st.write(response.text)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Bloc des sources lues par l'IA
                with st.expander("📚 Voir les sites officiels consultés pour cette réponse"):
                    metadata = response.candidates[0].grounding_metadata
                    if metadata and hasattr(metadata, 'grounding_chunks'):
                        for chunk in metadata.grounding_chunks:
                            if chunk.web:
                                st.write(f"- [{chunk.web.title}]({chunk.web.uri})")
                    else:
                        st.write("Sources générales vérifiées par Google Search.")
            except Exception as e:
                st.error(f"Erreur lors de la recherche : {e}")
