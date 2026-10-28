import sqlite3
import pandas as pd
import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Affectation PFE - Univ Blida 1", page_icon="🎓", layout="wide"
)

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("pfe_lots_blida.db")
    cursor = conn.cursor()

    # Sujets / Enseignants avec une capacité en nombre d'étudiants (ex: 12 étudiants)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sujets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            categorie TEXT NOT NULL,
            enseignant TEXT NOT NULL,
            capacite_etudiants INTEGER NOT NULL
        )
    """)

    # Vœux individuels des étudiants
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etudiants_voeux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_prenom TEXT UNIQUE NOT NULL,
            email TEXT,
            choix_1 TEXT NOT NULL,
            choix_2 TEXT NOT NULL,
            choix_3 TEXT NOT NULL,
            sujet_affecte_id INTEGER,
            FOREIGN KEY(sujet_affecte_id) REFERENCES sujets(id)
        )
    """)
    conn.commit()
    conn.close()


init_db()

# --- TAXONOMIE DES THÉMATIQUES ---
CATEGORIES = [
    "Intelligence Artificielle & Data Science",
    "Grands Modèles de Langage (LLM) & RAG",
    "Ingénierie des Connaissances & Ontologies",
    "Génie Logiciel & Applications Web/Mobiles",
    "Systèmes de Gestion d'Entreprise (ERP / Odoo)",
    "Cybersécurité, Réseaux & Cloud",
    "Internet des Objets (IoT) & Robotique",
    "Bases de Données & Business Intelligence",
]

# --- NAVIGATION ---
st.sidebar.title("🎓 PFE - Blida 1")
role = st.sidebar.selectbox(
    "Espace :",
    [
        "Accueil",
        "1. Étudiant (Formulaire de Vœux)",
        "2. Enseignant (Proposer un Sujet)",
        "3. Administration (Affectation par Lots)",
    ],
)

# ==========================================
# 0. ACCUEIL
# ==========================================
if role == "Accueil":
    st.title("Système de Répartition des PFE par Enseignant")
    st.markdown("""
    Bienvenue sur la plateforme de gestion des PFE du département d'informatique.
    
    ### 📌 Fonctionnement :
    1. **Étudiants :** Remplissent individuellement leur fiche de vœux (choix de domaines).
    2. **Enseignants :** Proposent un thème et définissent leur capacité d'accueil en nombre d'étudiants (ex: 12 étudiants).
    3. **Administration :** L'algorithme répartit les étudiants de façon équitable chez les enseignants selon leurs préférences. Les trinômes seront ensuite formés en présentiel avec chaque enseignant.
    """)

# ==========================================
# 1. ESPACE ÉTUDIANT
# ==========================================
elif role == "1. Étudiant (Formulaire de Vœux)":
    st.subheader("📝 Fiche de Vœux Individuelle")
    st.info(
        "Remplissez ce formulaire pour indiquer vos domaines de préférence pour le PFE."
    )

    with st.form("form_etudiant_voeux"):
        nom_prenom = st.text_input(
            "Nom et Prénom (ex: Mohamed Benali)"
        )
        email = st.text_input("Email universitaire (@univ-blida.dz)")

        st.markdown("### 🎯 Classement de vos thématiques préférées")
        c1 = st.selectbox("1er Choix de Domaine", CATEGORIES, index=0)
        c2 = st.selectbox("2ème Choix de Domaine", CATEGORIES, index=1)
        c3 = st.selectbox("3ème Choix de Domaine", CATEGORIES, index=2)

        submit = st.form_submit_button("Soumettre mes vœux")

        if submit:
            if not nom_prenom:
                st.error("Veuillez entrer votre nom et prénom.")
            elif c1 == c2 or c1 == c3 or c2 == c3:
                st.error(
                    "Veuillez sélectionner 3 domaines différents pour vos choix."
                )
            else:
                try:
                    conn = sqlite3.connect("pfe_lots_blida.db")
                    conn.execute(
                        "INSERT INTO etudiants_voeux (nom_prenom, email, choix_1, choix_2, choix_3) VALUES (?, ?, ?, ?, ?)",
                        (nom_prenom, email, c1, c2, c3),
                    )
                    conn.commit()
                    conn.close()
                    st.success(
                        "Vos vœux ont été enregistrés avec succès !"
                    )
                except sqlite3.IntegrityError:
                    st.error(
                        "Un enregistrement avec ce nom existe déjà dans la base."
                    )

# ==========================================
# 2. ESPACE ENSEIGNANT
# ==========================================
elif role == "2. Enseignant (Proposer un Sujet)":
    st.subheader("👨‍🏫 Espace Enseignant - Proposition de Thème")

    with st.form("form_ens"):
        nom_ens = st.text_input("Nom de l'Enseignant (ex: Dr. Khelifi)")
        titre = st.text_input("Intitulé du Sujet ou de la Thématique globale")
        cat = st.selectbox("Domaine associé", CATEGORIES)
        capacite_etudiants = st.number_input(
            "Nombre maximum d'étudiants à prendre en charge (ex: 12)",
            min_value=1,
            max_value=30,
            value=12,
        )

        if st.form_submit_button("Publier le sujet"):
            if not nom_ens or not titre:
                st.error("Veuillez remplir tous les champs obligatoires.")
            else:
                conn = sqlite3.connect("pfe_lots_blida.db")
                conn.execute(
                    "INSERT INTO sujets (titre, categorie, enseignant, capacite_etudiants) VALUES (?, ?, ?, ?)",
                    (titre, cat, nom_ens, capacite_etudiants),
                )
                conn.commit()
                conn.close()
                st.success("Sujet et capacité enregistrés avec succès !")

# ==========================================
# 3. ESPACE ADMINISTRATION
# ==========================================
elif role == "3. Administration (Affectation par Lots)":
    st.subheader(
        "⚙️ Répartition des étudiants par Enseignant (Lots d'étudiants)"
    )

    conn = sqlite3.connect("pfe_lots_blida.db")
    df_etudiants = pd.read_sql("SELECT * FROM etudiants_voeux", conn)
    df_sujets = pd.read_sql("SELECT * FROM sujets", conn)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Étudiants Inscrits", len(df_etudiants))
    with col2:
        total_places = (
            df_sujets["capacite_etudiants"].sum()
            if not df_sujets.empty
            else 0
        )
        st.metric("Capacité Totale d'Accueil (Étudiants)", total_places)

    st.markdown("---")
    if st.button("🚀 Lancer l'affectation automatique des étudiants"):
        if df_etudiants.empty or df_sujets.empty:
            st.warning(
                "Il faut des étudiants inscrits et des sujets d'enseignants pour lancer l'affectation."
            )
        else:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE etudiants_voeux SET sujet_affecte_id = NULL"
            )

            # Charger les capacités restantes de chaque sujet (en nombre d'étudiants)
            sujets_dict = {}
            for _, row in df_sujets.iterrows():
                sujets_dict[row["id"]] = {
                    "titre": row["titre"],
                    "enseignant": row["enseignant"],
                    "categorie": row["categorie"],
                    "capacite": row["capacite_etudiants"],
                }

            etudiants = df_etudiants.to_dict("records")
            affectes_count = 0

            # Fonction pour trouver un sujet disponible selon un domaine
            def trouver_sujet_par_domaine(domaine):
                for s_id, s_info in sujets_dict.items():
                    if (
                        s_info["categorie"] == domaine
                        and s_info["capacite"] > 0
                    ):
                        return s_id
                return None

            def trouver_premier_sujet_dispo():
                for s_id, s_info in sujets_dict.items():
                    if s_info["capacite"] > 0:
                        return s_id
                return None

            # 1er tour : Essayer de satisfaire le 1er choix
            for etud in etudiants:
                s_id = trouver_sujet_par_domaine(etud["choix_1"])
                if not s_id:
                    s_id = trouver_sujet_par_domaine(etud["choix_2"])
                if not s_id:
                    s_id = trouver_sujet_par_domaine(etud["choix_3"])
                if not s_id:
                    s_id = trouver_premier_sujet_dispo()

                if s_id:
                    cursor.execute(
                        "UPDATE etudiants_voeux SET sujet_affecte_id = ? WHERE id = ?",
                        (s_id, etud["id"]),
                    )
                    sujets_dict[s_id]["capacite"] -= 1
                    affectes_count += 1

            conn.commit()
            st.success(
                f"Affectation terminée ! {affectes_count} étudiants ont été assignés à un enseignant."
            )
            st.rerun()

    st.markdown("---")
    st.subheader(
        "📊 Liste des étudiants par Enseignant (Prêt pour la répartition en trinômes en présentiel)"
    )

    df_res = pd.read_sql(
        """
        SELECT e.nom_prenom AS 'Étudiant', e.email AS 'Email', 
               s.enseignant AS 'Enseignant Assigné', s.titre AS 'Thème / Cadre', s.categorie AS 'Domaine'
        FROM etudiants_voeux e
        LEFT JOIN sujets s ON e.sujet_affecte_id = s.id
    """,
        conn,
    )
    st.dataframe(df_res, use_container_width=True)

    if not df_res.empty:
        csv = df_res.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Télécharger la répartition complète (CSV)",
            data=csv,
            file_name="Repartition_Etudiants_Enseignants_Blida.csv",
            mime="text/csv",
        )

    conn.close()
