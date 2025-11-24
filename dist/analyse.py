import json 
from collections import defaultdict
import re 
from urllib.parse import unquote

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration du style des graphiques
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Liste des fichiers à combiner
files = ["result_cleaned_dom.json", "Roy.json", "valere.json", "result_domlado.json"]

# Dictionnaire pour stocker les données combinées
combined_data = {}

# Charger chaque fichier et ajouter son contenu au dictionnaire
for file in files:
    try:
        with open(file, "r") as f:
            data = json.load(f)
            combined_data.update(data)
        print(f"✅ Fichier chargé: {file}")
    except FileNotFoundError:
        print(f"⚠️ Fichier non trouvé: {file}")
    except json.JSONDecodeError:
        print(f"⚠️ Erreur de lecture JSON: {file}")


def analyser_suspicious_tokens(data):
    """Analyse et agrège les informations sur les jetons suspects."""
    token_stats = defaultdict(lambda: {"count": 0, "total_risk_score": 0})

    for browser, sites in data.items():
        for url, url_data in sites.items():
            if "suspicious_tokens" in url_data and url_data["suspicious_tokens"]["count"] > 0:
                for token in url_data["suspicious_tokens"]["items"]:
                    token_key = (
                        token.get("category", "N/A"),
                        token.get("type", "N/A"),
                        token.get("subtype", "N/A")
                    )
                    token_stats[token_key]["count"] += 1
                    token_stats[token_key]["total_risk_score"] += token.get("risk_score", 0)
    
    for key, values in token_stats.items():
        if values["count"] > 0:
            values["avg_risk_score"] = values["total_risk_score"] / values["count"]
        else:
            values["avg_risk_score"] = 0

    return dict(sorted(token_stats.items(), key=lambda item: item[1]["count"], reverse=True))


def extraire_tracker_et_site(url):
    """Extrait le tracker et le site visité selon différents formats d'URL"""
    
    if url.startswith("_https://") and "^0https://" in url:
        match = re.match(r'_https://([^/^]+).*?\^0https://(.+?)(?:/|$)', url)
        if match:
            return (match.group(2), match.group(1))
    
    if url.startswith("https+++") and "^partitionKey=" in url:
        match = re.match(r'https\+\+\+([^/^]+).*?\^partitionKey=%28https%2C([^%\)]+)%29', url)
        if match:
            return (match.group(2), match.group(1))
    
    if url.startswith("META:https://") and "^0https://" in url:
        match = re.match(r'META:https://([^/^]+).*?\^0https://(.+?)(?:/|$)', url)
        if match:
            return (match.group(2), match.group(1))
    
    if url.startswith("https+++") and "^0https://" in url:
        match = re.match(r'https\+\+\+(.+?)\^0https://(.+?)(?:/|$)', url)
        if match:
            site_part = match.group(1).replace("+", "/")
            tracker_domain = match.group(2)
            site_match = re.search(r'([^/]+\.[^/]+?)(?:/|$)', site_part)
            if site_match:
                return (site_match.group(1), tracker_domain)
    
    if url.startswith("METAACCESS:https:") and "^0https://" in url:
        match = re.match(r'METAACCESS:https://([^/^]+).*?\^0https://(.+?)(?:/|$)', url)
        if match:
            return (match.group(2), match.group(1))
    
    return None


def analyser_trackers(data):
    """Analyse les trackers pour chaque navigateur/utilisateur"""
    resultats_par_browser = {}
    
    for browser, sites in data.items():
        domain_pairs = defaultdict(lambda: {"count": 0})
        sites_avec_trackers = set()
        sites_sans_trackers = set()
        total_sites = 0
        trackers_par_site = defaultdict(set)
        
        for url, url_data in sites.items():
            total_sites += 1
            result = extraire_tracker_et_site(url)
            
            if result:
                site_visite, tracker_domain = result
                domain_pairs[(site_visite, tracker_domain)]["count"] += 1
                sites_avec_trackers.add(site_visite)
                trackers_par_site[site_visite].add(tracker_domain)
            else:
                sites_sans_trackers.add(url)
        
        nb_sites_avec_trackers = len(sites_avec_trackers)
        pourcentage_trackers = (nb_sites_avec_trackers / total_sites * 100) if total_sites > 0 else 0
        
        top_trackers = sorted(domain_pairs.items(), key=lambda x: x[1]["count"], reverse=True)
        tous_trackers = set()
        for trackers in trackers_par_site.values():
            tous_trackers.update(trackers)
        
        resultats_par_browser[browser] = {
            "total_sites": total_sites,
            "sites_avec_trackers": nb_sites_avec_trackers,
            "sites_sans_trackers": len(sites_sans_trackers),
            "pourcentage_trackers": pourcentage_trackers,
            "nb_trackers_uniques": len(tous_trackers),
            "top_trackers": top_trackers,
            "domain_pairs": dict(domain_pairs),
            "trackers_par_site": dict(trackers_par_site)
        }
    
    return resultats_par_browser


def analyser_donnees_sites_sans_trackers(data):
    """Analyse les données collectées par les sites directement (non-trackers)."""
    pii_par_site = defaultdict(lambda: {"total_collectes": 0, "types_donnees": defaultdict(int)})
    for browser, sites in data.items():
        for url, url_data in sites.items():
            if extraire_tracker_et_site(url) is None:
                for data_key, values in url_data.items():
                    if isinstance(values, dict):
                        count = values.get("exact", 0) + values.get("variants", 0)
                        if data_key == "suspicious_tokens": 
                            count = values.get("count", 0)
                        if count > 0:
                            pii_par_site[url]["types_donnees"][data_key] += count
                            pii_par_site[url]["total_collectes"] += count
    return dict(sorted(pii_par_site.items(), key=lambda x: x[1]["total_collectes"], reverse=True))


def analyser_donnees_personnelles_trackers(data):
    """Analyse les données collectées par les trackers identifiés."""
    pii_par_tracker = defaultdict(lambda: {"total_collectes": 0, "types_donnees": defaultdict(int)})
    for browser, sites in data.items():
        for url, url_data in sites.items():
            result = extraire_tracker_et_site(url)
            if result:
                _site_visite, tracker_domain = result
                for data_key, values in url_data.items():
                    if isinstance(values, dict):
                        count = values.get("exact", 0) + values.get("variants", 0)
                        if data_key == "suspicious_tokens": 
                            count = values.get("count", 0)
                        if count > 0:
                            pii_par_tracker[tracker_domain]["types_donnees"][data_key] += count
                            pii_par_tracker[tracker_domain]["total_collectes"] += count
    return dict(sorted(pii_par_tracker.items(), key=lambda x: x[1]["total_collectes"], reverse=True))


def analyser_types_donnees_globales(data):
    """Comptabilise les types de données personnelles les plus trouvées."""
    types_donnees_count = defaultdict(int)
    
    for browser, sites in data.items():
        for url, url_data in sites.items():
            for data_key, values in url_data.items():
                if isinstance(values, dict):
                    count = values.get("exact", 0) + values.get("variants", 0)
                    if data_key == "suspicious_tokens":
                        count = values.get("count", 0)
                    if count > 0:
                        types_donnees_count[data_key] += count
    
    return dict(sorted(types_donnees_count.items(), key=lambda x: x[1], reverse=True))


def analyser_proportion_collecte(data):
    """Analyse la proportion des sites qui collectent des données personnelles."""
    stats = {
        'avec_trackers': {'collectent': 0, 'ne_collectent_pas': 0, 'total': 0},
        'sans_trackers': {'collectent': 0, 'ne_collectent_pas': 0, 'total': 0},
        'global': {'collectent': 0, 'ne_collectent_pas': 0, 'total': 0}
    }
    
    sites_vus = set()
    
    for browser, sites in data.items():
        for url, url_data in sites.items():
            if url in sites_vus:
                continue
            sites_vus.add(url)
            
            result = extraire_tracker_et_site(url)
            is_tracker = result is not None
            
            collecte_donnees = False
            for data_key, values in url_data.items():
                if isinstance(values, dict):
                    count = values.get("exact", 0) + values.get("variants", 0)
                    if data_key == "suspicious_tokens":
                        count = values.get("count", 0)
                    if count > 0:
                        collecte_donnees = True
                        break
            
            if is_tracker:
                stats['avec_trackers']['total'] += 1
                if collecte_donnees:
                    stats['avec_trackers']['collectent'] += 1
                else:
                    stats['avec_trackers']['ne_collectent_pas'] += 1
            else:
                stats['sans_trackers']['total'] += 1
                if collecte_donnees:
                    stats['sans_trackers']['collectent'] += 1
                else:
                    stats['sans_trackers']['ne_collectent_pas'] += 1
            
            stats['global']['total'] += 1
            if collecte_donnees:
                stats['global']['collectent'] += 1
            else:
                stats['global']['ne_collectent_pas'] += 1
    
    for category in stats:
        total = stats[category]['total']
        if total > 0:
            stats[category]['pct_collectent'] = (stats[category]['collectent'] / total) * 100
            stats[category]['pct_ne_collectent_pas'] = (stats[category]['ne_collectent_pas'] / total) * 100
        else:
            stats[category]['pct_collectent'] = 0
            stats[category]['pct_ne_collectent_pas'] = 0
    
    return stats


def analyser_types_donnees_par_navigateur(data):
    """Comptabilise les types de données personnelles par navigateur."""
    donnees_par_navigateur = defaultdict(lambda: defaultdict(int))
    
    for browser, sites in data.items():
        for url, url_data in sites.items():
            for data_key, values in url_data.items():
                if isinstance(values, dict):
                    count = values.get("exact", 0) + values.get("variants", 0)
                    if data_key == "suspicious_tokens":
                        count = values.get("count", 0)
                    if count > 0:
                        donnees_par_navigateur[browser][data_key] += count
    
    return dict(donnees_par_navigateur)


def graphique_suspicious_tokens(token_stats, top_n=15):
    """Crée plusieurs graphiques sur les jetons suspects."""
    df = creer_tableau_suspicious_tokens(token_stats)
    if df.empty:
        print("Aucun jeton suspect à afficher.")
        return None

    # Conversion numérique sécurisée
    df["Risk Score Moyen"] = pd.to_numeric(df["Risk Score Moyen"], errors="coerce")
    df["Occurrences"] = pd.to_numeric(df["Occurrences"], errors="coerce")
    df = df.dropna(subset=["Risk Score Moyen", "Occurrences"])

    # Regrouper par catégorie
    df_cat = df.groupby("Category").agg({
        "Occurrences": "sum",
        "Risk Score Moyen": "mean"
    }).reset_index().sort_values("Occurrences", ascending=False)

    top_cats = df_cat.head(top_n)

    # Figure combinée
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Analyse des Jetons Suspects (Suspicious Tokens)", fontsize=15, fontweight='bold')

    # Fréquence par catégorie
    sns.barplot(data=top_cats, y="Category", x="Occurrences", ax=axes[0], palette="flare")
    axes[0].set_title("Fréquence par catégorie", fontsize=13, fontweight='bold')
    axes[0].set_xlabel("Occurrences")
    axes[0].set_ylabel("Catégorie")
    for i, v in enumerate(top_cats["Occurrences"]):
        axes[0].text(v, i, f" {int(v)}", va="center", fontsize=9, fontweight="bold")

    # Score de risque moyen
    sns.barplot(data=top_cats, y="Category", x="Risk Score Moyen", ax=axes[1], palette="crest")
    axes[1].set_title("Score de risque moyen par catégorie", fontsize=13, fontweight='bold')
    axes[1].set_xlabel("Score de risque moyen")
    axes[1].set_ylabel("")
    for i, v in enumerate(top_cats["Risk Score Moyen"]):
        axes[1].text(v, i, f" {v:.1f}", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.show()

    # Graphique des sous-types
    df_sub = df.groupby(["Type", "Subtype"])["Occurrences"].sum().reset_index()
    df_sub = df_sub.sort_values("Occurrences", ascending=False).head(top_n)

    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_sub, y="Subtype", x="Occurrences", hue="Type", dodge=False, palette="husl")
    plt.title(f"Top {top_n} sous-types de jetons suspects", fontsize=14, fontweight="bold")
    plt.xlabel("Occurrences")
    plt.ylabel("Sous-type")
    plt.legend(title="Type", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()

    return fig


def graphique_types_donnees_globales(types_donnees, top_n=15):
    """Graphique des types de données les plus collectées."""
    top_types = dict(list(types_donnees.items())[:top_n])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    types = list(top_types.keys())
    counts = list(top_types.values())
    
    bars = ax.barh(types, counts, color=sns.color_palette("viridis", len(types)))
    ax.set_xlabel('Nombre d\'occurrences', fontsize=12, fontweight='bold')
    ax.set_title(f'Top {top_n} des types de données personnelles collectées', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.invert_yaxis()
    
    for i, (bar, count) in enumerate(zip(bars, counts)):
        ax.text(count, i, f' {count}', va='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    return fig


def graphique_donnees_par_navigateur(donnees_par_navigateur, top_types=10):
    """Graphique des types de données par navigateur."""
    types_count = defaultdict(int)
    for browser_data in donnees_par_navigateur.values():
        for dtype, count in browser_data.items():
            types_count[dtype] += count
    
    top_types_list = [dtype for dtype, _ in sorted(types_count.items(), 
                                                     key=lambda x: x[1], reverse=True)[:top_types]]
    
    df_data = []
    for browser, types in donnees_par_navigateur.items():
        for dtype in top_types_list:
            df_data.append({
                'Navigateur': browser,
                'Type de donnée': dtype,
                'Count': types.get(dtype, 0)
            })
    
    df = pd.DataFrame(df_data)
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    browsers = df['Navigateur'].unique()
    x = range(len(top_types_list))
    width = 0.8 / len(browsers)
    
    for i, browser in enumerate(browsers):
        browser_data = df[df['Navigateur'] == browser]
        counts = [browser_data[browser_data['Type de donnée'] == t]['Count'].values[0] 
                  if len(browser_data[browser_data['Type de donnée'] == t]) > 0 else 0 
                  for t in top_types_list]
        
        offset = (i - len(browsers)/2 + 0.5) * width
        ax.bar([xi + offset for xi in x], counts, width, label=browser)
    
    ax.set_xlabel('Type de donnée', fontsize=12, fontweight='bold')
    ax.set_ylabel('Nombre d\'occurrences', fontsize=12, fontweight='bold')
    ax.set_title(f'Top {top_types} des types de données par navigateur', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(top_types_list, rotation=45, ha='right')
    ax.legend(title='Navigateur', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    return fig


def graphique_trackers_vs_sites(resultats_pii_trackers, resultats_pii_sites, top_n=10):
    """Compare la collecte entre trackers et sites directs."""
    top_trackers = list(resultats_pii_trackers.items())[:top_n]
    top_sites = list(resultats_pii_sites.items())[:top_n]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    if top_trackers:
        trackers = [t[0][:30] for t in top_trackers]
        counts = [t[1]["total_collectes"] for t in top_trackers]
        ax1.barh(trackers, counts, color='coral')
        ax1.set_xlabel('Nombre de collectes', fontsize=11, fontweight='bold')
        ax1.set_title(f'Top {top_n} Trackers', fontsize=13, fontweight='bold')
        ax1.invert_yaxis()
        for i, count in enumerate(counts):
            ax1.text(count, i, f' {count}', va='center', fontsize=9)
    
    if top_sites:
        sites = [s[0][:30] for s in top_sites]
        counts = [s[1]["total_collectes"] for s in top_sites]
        ax2.barh(sites, counts, color='skyblue')
        ax2.set_xlabel('Nombre de collectes', fontsize=11, fontweight='bold')
        ax2.set_title(f'Top {top_n} Sites (sans tracker)', fontsize=13, fontweight='bold')
        ax2.invert_yaxis()
        for i, count in enumerate(counts):
            ax2.text(count, i, f' {count}', va='center', fontsize=9)
    
    plt.suptitle('Comparaison: Trackers vs Sites directs', 
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.show()
    return fig


def graphique_repartition_trackers_par_navigateur(resultats_trackers):
    """Graphique de la répartition des trackers par navigateur."""
    browsers = list(resultats_trackers.keys())
    nb_trackers = [resultats_trackers[b]["nb_trackers_uniques"] for b in browsers]
    sites_trackes = [resultats_trackers[b]["sites_avec_trackers"] for b in browsers]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1.bar(browsers, nb_trackers, color=sns.color_palette("muted", len(browsers)))
    ax1.set_ylabel('Nombre de trackers uniques', fontsize=11, fontweight='bold')
    ax1.set_title('Trackers uniques par navigateur', fontsize=13, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    for i, v in enumerate(nb_trackers):
        ax1.text(i, v, f' {v}', ha='center', va='bottom', fontweight='bold')
    
    ax2.bar(browsers, sites_trackes, color=sns.color_palette("pastel", len(browsers)))
    ax2.set_ylabel('Nombre de sites trackés', fontsize=11, fontweight='bold')
    ax2.set_title('Sites avec trackers par navigateur', fontsize=13, fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    for i, v in enumerate(sites_trackes):
        ax2.text(i, v, f' {v}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    return fig


def graphique_proportion_collecte(stats_proportion):
    """Visualise la proportion de collecte de données."""
    fig = plt.figure(figsize=(16, 6))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    colors_collecte = ['#ff7675', '#74b9ff']
    
    # Camembert Global
    ax1 = fig.add_subplot(gs[:, 0])
    labels_global = ['Collectent des données', 'Ne collectent pas']
    sizes_global = [stats_proportion['global']['collectent'], 
                    stats_proportion['global']['ne_collectent_pas']]
    explode = (0.05, 0)
    
    ax1.pie(sizes_global, explode=explode, labels=labels_global, colors=colors_collecte,
            autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
    ax1.set_title('Proportion GLOBALE\n(tous sites/trackers)', fontsize=13, fontweight='bold', pad=20)
    
    # Avec Trackers
    ax2 = fig.add_subplot(gs[0, 1])
    sizes_trackers = [stats_proportion['avec_trackers']['collectent'], 
                      stats_proportion['avec_trackers']['ne_collectent_pas']]
    
    ax2.pie(sizes_trackers, explode=explode, labels=labels_global, colors=colors_collecte,
            autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
    ax2.set_title('AVEC Trackers', fontsize=12, fontweight='bold', pad=15)
    
    # Sans Trackers
    ax3 = fig.add_subplot(gs[0, 2])
    sizes_sans = [stats_proportion['sans_trackers']['collectent'], 
                  stats_proportion['sans_trackers']['ne_collectent_pas']]
    
    ax3.pie(sizes_sans, explode=explode, labels=labels_global, colors=colors_collecte,
            autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
    ax3.set_title('SANS Trackers (sites directs)', fontsize=12, fontweight='bold', pad=15)
    
    # Graphique en barres
    ax4 = fig.add_subplot(gs[1, 1:])
    categories = ['Avec Trackers', 'Sans Trackers', 'GLOBAL']
    collectent = [stats_proportion['avec_trackers']['collectent'],
                  stats_proportion['sans_trackers']['collectent'],
                  stats_proportion['global']['collectent']]
    ne_collectent = [stats_proportion['avec_trackers']['ne_collectent_pas'],
                     stats_proportion['sans_trackers']['ne_collectent_pas'],
                     stats_proportion['global']['ne_collectent_pas']]
    
    x = range(len(categories))
    width = 0.35
    
    bars1 = ax4.bar([i - width/2 for i in x], collectent, width, label='Collectent des données', 
                    color=colors_collecte[0], alpha=0.8)
    bars2 = ax4.bar([i + width/2 for i in x], ne_collectent, width, label='Ne collectent pas', 
                    color=colors_collecte[1], alpha=0.8)
    
    ax4.set_ylabel('Nombre de sites/trackers', fontsize=11, fontweight='bold')
    ax4.set_title('Comparaison: Collecte de données personnelles', fontsize=12, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(categories, fontsize=11, fontweight='bold')
    ax4.legend(loc='upper right', fontsize=10)
    ax4.grid(axis='y', alpha=0.3)
    
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.suptitle('Analyse des Proportions de Collecte de Données Personnelles', 
                 fontsize=15, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    plt.show()
    return fig


# Fonctions de création de tableaux
def creer_tableau_suspicious_tokens(token_stats):
    data_tokens = []
    for (category, type, subtype), stats in token_stats.items():
        data_tokens.append({
            "Category": category,
            "Type": type,
            "Subtype": subtype,
            "Occurrences": stats["count"],
            "Risk Score Moyen": f"{stats['avg_risk_score']:.1f}"
        })
    return pd.DataFrame(data_tokens)


def creer_tableau_resume(resultats):
    data_resume = []
    for browser, stats in resultats.items():
        data_resume.append({
            "Utilisateur": browser, 
            "Sites visités": stats["total_sites"],
            "Sites trackés": stats["sites_avec_trackers"], 
            "% trackés": f"{stats['pourcentage_trackers']:.1f}%",
            "Trackers uniques": stats["nb_trackers_uniques"]
        })
    return pd.DataFrame(data_resume)


def creer_tableau_top_trackers(resultats, top_n=15):
    tracker_count = defaultdict(lambda: {"count": 0, "sites": set()})
    for browser_stats in resultats.values():
        for (site, tracker), info in browser_stats["top_trackers"]:
            tracker_count[tracker]["count"] += info["count"]
            tracker_count[tracker]["sites"].add(site)
            
    top_trackers = sorted(tracker_count.items(), key=lambda x: x[1]["count"], reverse=True)[:top_n]
    
    data_trackers = []
    for tracker, info in top_trackers:
        data_trackers.append({
            "Tracker": tracker, 
            "Utilisations totales": info["count"], 
            "Sites différents": len(info["sites"])
        })
        
    return pd.DataFrame(data_trackers)


def creer_tableau_collecte_pii_trackers(resultats_pii, top_n=15):
    data_pii = []
    for tracker, info in list(resultats_pii.items())[:top_n]:
        sorted_types = sorted(info["types_donnees"].items(), key=lambda x: x[1], reverse=True)
        types_str = ", ".join([f"{dtype}({count})" for dtype, count in sorted_types])
        data_pii.append({
            "Tracker": tracker, 
            "Total Collectes": info["total_collectes"],
            "Types de données collectées": types_str
        })
    return pd.DataFrame(data_pii)


def creer_tableau_collecte_sites_sans_trackers(resultats_pii_sites, top_n=15):
    data_pii = []
    for site, info in list(resultats_pii_sites.items())[:top_n]:
        sorted_types = sorted(info["types_donnees"].items(), key=lambda x: x[1], reverse=True)
        types_str = ", ".join([f"{dtype}({count})" for dtype, count in sorted_types])
        data_pii.append({
            "Site": site, 
            "Total Collectes": info["total_collectes"],
            "Types de données collectées": types_str
        })
    return pd.DataFrame(data_pii)


def creer_tableau_types_donnees_globales(types_donnees, top_n=20):
    """Tableau des types de données les plus collectées."""
    top_types = list(types_donnees.items())[:top_n]
    data = []
    for dtype, count in top_types:
        data.append({
            "Type de donnée": dtype,
            "Nombre d'occurrences": count
        })
    return pd.DataFrame(data)


def creer_tableau_types_donnees_par_navigateur(donnees_par_navigateur):
    """Tableau détaillé des types de données par navigateur."""
    all_data = []
    for browser, types in donnees_par_navigateur.items():
        for dtype, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            all_data.append({
                "Navigateur": browser,
                "Type de donnée": dtype,
                "Occurrences": count
            })
    return pd.DataFrame(all_data)


def analyser_sites_communs_entre_navigateurs(data):
    """Analyse les sites visités sur plusieurs navigateurs et leurs trackers."""
    
    # Dictionnaire : {site: {navigateur: [liste_trackers]}}
    sites_par_navigateur = defaultdict(lambda: defaultdict(set))
    
    # Collecter les sites et trackers par navigateur
    for browser, sites in data.items():
        for url, url_data in sites.items():
            result = extraire_tracker_et_site(url)
            
            if result:
                # Site avec tracker
                site_visite, tracker_domain = result
                sites_par_navigateur[site_visite][browser].add(tracker_domain)
            else:
                # Site sans tracker
                clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
                if "^" in clean_url:
                    clean_url = clean_url.split("^")[0]
                domain = clean_url.split("/")[0].split("?")[0]
                
                if domain and len(domain) > 2 and "." in domain:
                    # Ajouter le site même sans tracker
                    if browser not in sites_par_navigateur[domain]:
                        sites_par_navigateur[domain][browser] = set()
    
    # Filtrer les sites présents sur plusieurs navigateurs
    sites_communs = {}
    navigateurs_list = list(data.keys())
    
    for site, browsers_data in sites_par_navigateur.items():
        if len(browsers_data) >= 2:  # Site présent sur au moins 2 navigateurs
            sites_communs[site] = {}
            for browser in navigateurs_list:
                if browser in browsers_data:
                    sites_communs[site][browser] = {
                        "present": True,
                        "trackers": sorted(list(browsers_data[browser])),
                        "nb_trackers": len(browsers_data[browser])
                    }
                else:
                    sites_communs[site][browser] = {
                        "present": False,
                        "trackers": [],
                        "nb_trackers": 0
                    }
    
    # Trier par nombre de navigateurs où le site est présent
    sites_communs_sorted = dict(sorted(
        sites_communs.items(),
        key=lambda x: sum(1 for b in x[1].values() if b["present"]),
        reverse=True
    ))
    
    return sites_communs_sorted, navigateurs_list


def analyser_comparaison_navigateurs(data):
    """Analyse comparative détaillée entre navigateurs."""
    
    stats_comparaison = {
        "sites_uniquement_sur": defaultdict(set),  # Sites exclusifs à un navigateur
        "trackers_uniquement_sur": defaultdict(set),  # Trackers exclusifs
        "sites_tous_navigateurs": set(),  # Sites sur TOUS les navigateurs
        "trackers_tous_navigateurs": set()  # Trackers sur TOUS
    }
    
    # Collecter sites et trackers par navigateur
    sites_par_nav = defaultdict(set)
    trackers_par_nav = defaultdict(set)
    
    for browser, sites in data.items():
        for url, url_data in sites.items():
            result = extraire_tracker_et_site(url)
            
            if result:
                site_visite, tracker_domain = result
                sites_par_nav[browser].add(site_visite)
                trackers_par_nav[browser].add(tracker_domain)
            else:
                clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
                if "^" in clean_url:
                    clean_url = clean_url.split("^")[0]
                domain = clean_url.split("/")[0].split("?")[0]
                
                if domain and len(domain) > 2 and "." in domain:
                    sites_par_nav[browser].add(domain)
    
    navigateurs = list(data.keys())
    
    # Sites présents sur TOUS les navigateurs
    if navigateurs:
        sites_communs_tous = sites_par_nav[navigateurs[0]].copy()
        trackers_communs_tous = trackers_par_nav[navigateurs[0]].copy()
        
        for nav in navigateurs[1:]:
            sites_communs_tous &= sites_par_nav[nav]
            trackers_communs_tous &= trackers_par_nav[nav]
        
        stats_comparaison["sites_tous_navigateurs"] = sites_communs_tous
        stats_comparaison["trackers_tous_navigateurs"] = trackers_communs_tous
    
    # Sites/trackers exclusifs à chaque navigateur
    for nav in navigateurs:
        autres_navs = [n for n in navigateurs if n != nav]
        
        sites_autres = set()
        trackers_autres = set()
        
        for autre_nav in autres_navs:
            sites_autres |= sites_par_nav[autre_nav]
            trackers_autres |= trackers_par_nav[autre_nav]
        
        stats_comparaison["sites_uniquement_sur"][nav] = sites_par_nav[nav] - sites_autres
        stats_comparaison["trackers_uniquement_sur"][nav] = trackers_par_nav[nav] - trackers_autres
    
    return stats_comparaison, sites_par_nav, trackers_par_nav


def extraire_liste_sites_et_trackers(data):
    """Extrait la liste complète des sites et trackers."""
    sites_set = set()
    trackers_set = set()
    sites_details = {}  # Pour debug et vérification
    
    for browser, sites in data.items():
        for url, url_data in sites.items():
            result = extraire_tracker_et_site(url)
            
            if result:
                # URL avec tracker : on a le site visité ET le tracker
                site_visite, tracker_domain = result
                sites_set.add(site_visite)
                trackers_set.add(tracker_domain)
                
                # Stocker les détails pour debug
                if site_visite not in sites_details:
                    sites_details[site_visite] = {"type": "avec_tracker", "trackers": set()}
                sites_details[site_visite]["trackers"].add(tracker_domain)
            else:
                # URL sans tracker : c'est un site visité directement
                # Nettoyer l'URL pour extraire le domaine principal
                clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
                
                # Gérer les différents formats d'URL
                if "^" in clean_url:
                    clean_url = clean_url.split("^")[0]
                
                domain = clean_url.split("/")[0].split("?")[0]
                
                # Filtrer les domaines invalides ou vides
                if domain and len(domain) > 2 and "." in domain:
                    sites_set.add(domain)
                    if domain not in sites_details:
                        sites_details[domain] = {"type": "sans_tracker", "trackers": set()}
    
    # Convertir les trackers en liste pour les sites_details
    sites_details_serializable = {}
    for site, details in sites_details.items():
        sites_details_serializable[site] = {
            "type": details["type"],
            "trackers": sorted(list(details["trackers"]))
        }
    
    return sorted(list(sites_set)), sorted(list(trackers_set)), sites_details_serializable


def sauvegarder_sites_communs_json(sites_communs, navigateurs_list):
    """Sauvegarde l'analyse des sites communs en JSON."""
    
    # Préparer les données pour JSON
    output = {
        "metadata": {
            "total_sites_communs": len(sites_communs),
            "navigateurs_analyses": navigateurs_list,
            "date_analyse": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "sites": sites_communs
    }
    
    with open("sites_communs_navigateurs.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sites communs sauvegardés: sites_communs_navigateurs.json ({len(sites_communs)} sites)")


def creer_tableau_sites_communs(sites_communs, navigateurs_list, top_n=20):
    """Crée un tableau des sites communs entre navigateurs."""
    
    data_table = []
    for site, browsers_data in list(sites_communs.items())[:top_n]:
        row = {"Site": site}
        
        nb_navigateurs = sum(1 for b in browsers_data.values() if b["present"])
        row["Nb Navigateurs"] = nb_navigateurs
        
        for nav in navigateurs_list:
            if browsers_data[nav]["present"]:
                nb_track = browsers_data[nav]["nb_trackers"]
                row[nav] = f"✓ ({nb_track} tracker{'s' if nb_track > 1 else ''})"
            else:
                row[nav] = "✗"
        
        # Total trackers uniques sur tous les navigateurs
        all_trackers = set()
        for nav_data in browsers_data.values():
            if nav_data["present"]:
                all_trackers.update(nav_data["trackers"])
        row["Total Trackers"] = len(all_trackers)
        
        data_table.append(row)
    
    return pd.DataFrame(data_table)


def graphique_sites_communs_venn(sites_par_nav, trackers_par_nav):
    """Graphique de comparaison entre navigateurs."""
    
    navigateurs = list(sites_par_nav.keys())
    
    if len(navigateurs) < 2:
        print("⚠️ Pas assez de navigateurs pour créer un graphique comparatif")
        return None
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Graphique 1: Nombre de sites par navigateur
    nav_names = []
    sites_counts = []
    trackers_counts = []
    
    for nav in navigateurs:
        nav_names.append(nav)
        sites_counts.append(len(sites_par_nav[nav]))
        trackers_counts.append(len(trackers_par_nav[nav]))
    
    x = range(len(nav_names))
    width = 0.35
    
    bars1 = ax1.bar([i - width/2 for i in x], sites_counts, width, 
                    label='Sites uniques', color='#3498db', alpha=0.8)
    bars2 = ax1.bar([i + width/2 for i in x], trackers_counts, width,
                    label='Trackers uniques', color='#e74c3c', alpha=0.8)
    
    ax1.set_ylabel('Nombre', fontsize=12, fontweight='bold')
    ax1.set_title('Sites et Trackers par Navigateur', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(nav_names, fontsize=11, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    
    # Ajouter les valeurs sur les barres
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Graphique 2: Intersections
    if len(navigateurs) == 2:
        nav1, nav2 = navigateurs[0], navigateurs[1]
        
        sites_communs = len(sites_par_nav[nav1] & sites_par_nav[nav2])
        sites_nav1_only = len(sites_par_nav[nav1] - sites_par_nav[nav2])
        sites_nav2_only = len(sites_par_nav[nav2] - sites_par_nav[nav1])
        
        categories = [f'Uniquement\n{nav1}', 'Communs', f'Uniquement\n{nav2}']
        values = [sites_nav1_only, sites_communs, sites_nav2_only]
        colors = ['#3498db', '#2ecc71', '#e74c3c']
        
        bars = ax2.bar(categories, values, color=colors, alpha=0.8)
        ax2.set_ylabel('Nombre de sites', fontsize=12, fontweight='bold')
        ax2.set_title('Répartition des Sites entre Navigateurs', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        for bar, val in zip(bars, values):
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{val}\n({val/sum(values)*100:.1f}%)',
                        ha='center', va='bottom', fontsize=11, fontweight='bold')
    elif len(navigateurs) >= 3:
        # Pour 3+ navigateurs, afficher les intersections multiples
        intersections_data = []
        labels_data = []
        
        # Tous les navigateurs
        intersection_tous = set.intersection(*[sites_par_nav[nav] for nav in navigateurs])
        intersections_data.append(len(intersection_tous))
        labels_data.append(f'Tous ({len(navigateurs)})')
        
        # Paires de navigateurs
        for i in range(len(navigateurs)):
            for j in range(i+1, len(navigateurs)):
                nav1, nav2 = navigateurs[i], navigateurs[j]
                intersection_pair = sites_par_nav[nav1] & sites_par_nav[nav2]
                # Exclure ceux qui sont dans tous
                intersection_pair_only = intersection_pair - intersection_tous
                intersections_data.append(len(intersection_pair_only))
                labels_data.append(f'{nav1[:10]}\n&\n{nav2[:10]}')
        
        # Sites exclusifs
        for nav in navigateurs:
            autres = set.union(*[sites_par_nav[n] for n in navigateurs if n != nav])
            exclusifs = sites_par_nav[nav] - autres
            intersections_data.append(len(exclusifs))
            labels_data.append(f'Seul.\n{nav[:10]}')
        
        colors_multi = sns.color_palette("husl", len(intersections_data))
        bars = ax2.bar(range(len(labels_data)), intersections_data, color=colors_multi, alpha=0.8)
        ax2.set_ylabel('Nombre de sites', fontsize=12, fontweight='bold')
        ax2.set_title('Intersections entre Navigateurs', fontsize=14, fontweight='bold')
        ax2.set_xticks(range(len(labels_data)))
        ax2.set_xticklabels(labels_data, fontsize=9, rotation=0)
        ax2.grid(axis='y', alpha=0.3)
        
        for bar, val in zip(bars, intersections_data):
            if val > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., val,
                        f'{val}',
                        ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.suptitle('Analyse Comparative des Navigateurs', 
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.show()
    
    return fig


def graphique_heatmap_sites_communs(sites_communs, navigateurs_list, top_n=30):
    """Heatmap montrant les sites communs et leurs trackers par navigateur."""
    
    if len(sites_communs) == 0:
        print("⚠️ Pas de sites communs pour créer une heatmap")
        return None
    
    # Préparer les données pour la heatmap
    sites_top = list(sites_communs.keys())[:top_n]
    data_matrix = []
    
    for site in sites_top:
        row = []
        for nav in navigateurs_list:
            if sites_communs[site][nav]["present"]:
                row.append(sites_communs[site][nav]["nb_trackers"])
            else:
                row.append(0)
        data_matrix.append(row)
    
    # Créer la heatmap
    fig, ax = plt.subplots(figsize=(12, max(8, len(sites_top) * 0.3)))
    
    df_heatmap = pd.DataFrame(data_matrix, index=sites_top, columns=navigateurs_list)
    
    sns.heatmap(df_heatmap, annot=True, fmt='d', cmap='YlOrRd', 
                cbar_kws={'label': 'Nombre de trackers'}, 
                linewidths=0.5, linecolor='gray', ax=ax)
    
    ax.set_title(f'Heatmap: Nombre de Trackers par Site et Navigateur (Top {top_n})', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Navigateur', fontsize=12, fontweight='bold')
    ax.set_ylabel('Site', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    
    return fig
    """Analyse les sites visités sur plusieurs navigateurs et leurs trackers."""
    
    # Dictionnaire : {site: {navigateur: [liste_trackers]}}
    sites_par_navigateur = defaultdict(lambda: defaultdict(set))
    
    # Collecter les sites et trackers par navigateur
    for browser, sites in data.items():
        for url, url_data in sites.items():
            result = extraire_tracker_et_site(url)
            
            if result:
                # Site avec tracker
                site_visite, tracker_domain = result
                sites_par_navigateur[site_visite][browser].add(tracker_domain)
            else:
                # Site sans tracker
                clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
                if "^" in clean_url:
                    clean_url = clean_url.split("^")[0]
                domain = clean_url.split("/")[0].split("?")[0]
                
                if domain and len(domain) > 2 and "." in domain:
                    # Ajouter le site même sans tracker
                    if browser not in sites_par_navigateur[domain]:
                        sites_par_navigateur[domain][browser] = set()
    
    # Filtrer les sites présents sur plusieurs navigateurs
    sites_communs = {}
    navigateurs_list = list(data.keys())
    
    for site, browsers_data in sites_par_navigateur.items():
        if len(browsers_data) >= 2:  # Site présent sur au moins 2 navigateurs
            sites_communs[site] = {}
            for browser in navigateurs_list:
                if browser in browsers_data:
                    sites_communs[site][browser] = {
                        "present": True,
                        "trackers": sorted(list(browsers_data[browser])),
                        "nb_trackers": len(browsers_data[browser])
                    }
                else:
                    sites_communs[site][browser] = {
                        "present": False,
                        "trackers": [],
                        "nb_trackers": 0
                    }
    
    # Trier par nombre de navigateurs où le site est présent
    sites_communs_sorted = dict(sorted(
        sites_communs.items(),
        key=lambda x: sum(1 for b in x[1].values() if b["present"]),
        reverse=True
    ))
    
    return sites_communs_sorted, navigateurs_list


def analyser_comparaison_navigateurs(data):
    """Analyse comparative détaillée entre navigateurs."""
    
    stats_comparaison = {
        "sites_uniquement_sur": defaultdict(set),  # Sites exclusifs à un navigateur
        "trackers_uniquement_sur": defaultdict(set),  # Trackers exclusifs
        "sites_tous_navigateurs": set(),  # Sites sur TOUS les navigateurs
        "trackers_tous_navigateurs": set()  # Trackers sur TOUS
    }
    
    # Collecter sites et trackers par navigateur
    sites_par_nav = defaultdict(set)
    trackers_par_nav = defaultdict(set)
    
    for browser, sites in data.items():
        for url, url_data in sites.items():
            result = extraire_tracker_et_site(url)
            
            if result:
                site_visite, tracker_domain = result
                sites_par_nav[browser].add(site_visite)
                trackers_par_nav[browser].add(tracker_domain)
            else:
                clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
                if "^" in clean_url:
                    clean_url = clean_url.split("^")[0]
                domain = clean_url.split("/")[0].split("?")[0]
                
                if domain and len(domain) > 2 and "." in domain:
                    sites_par_nav[browser].add(domain)
    
    navigateurs = list(data.keys())
    
    # Sites présents sur TOUS les navigateurs
    if navigateurs:
        sites_communs_tous = sites_par_nav[navigateurs[0]].copy()
        trackers_communs_tous = trackers_par_nav[navigateurs[0]].copy()
        
        for nav in navigateurs[1:]:
            sites_communs_tous &= sites_par_nav[nav]
            trackers_communs_tous &= trackers_par_nav[nav]
        
        stats_comparaison["sites_tous_navigateurs"] = sites_communs_tous
        stats_comparaison["trackers_tous_navigateurs"] = trackers_communs_tous
    
    # Sites/trackers exclusifs à chaque navigateur
    for nav in navigateurs:
        autres_navs = [n for n in navigateurs if n != nav]
        
        sites_autres = set()
        trackers_autres = set()
        
        for autre_nav in autres_navs:
            sites_autres |= sites_par_nav[autre_nav]
            trackers_autres |= trackers_par_nav[autre_nav]
        
        stats_comparaison["sites_uniquement_sur"][nav] = sites_par_nav[nav] - sites_autres
        stats_comparaison["trackers_uniquement_sur"][nav] = trackers_par_nav[nav] - trackers_autres
    
    return stats_comparaison, sites_par_nav, trackers_par_nav


def sauvegarder_sites_communs_json(sites_communs, navigateurs_list):
    """Sauvegarde l'analyse des sites communs en JSON."""
    
    # Préparer les données pour JSON
    output = {
        "metadata": {
            "total_sites_communs": len(sites_communs),
            "navigateurs_analyses": navigateurs_list,
            "date_analyse": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "sites": sites_communs
    }
    
    with open("sites_communs_navigateurs.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sites communs sauvegardés: sites_communs_navigateurs.json ({len(sites_communs)} sites)")


def creer_tableau_sites_communs(sites_communs, navigateurs_list, top_n=20):
    """Crée un tableau des sites communs entre navigateurs."""
    
    data_table = []
    for site, browsers_data in list(sites_communs.items())[:top_n]:
        row = {"Site": site}
        
        nb_navigateurs = sum(1 for b in browsers_data.values() if b["present"])
        row["Nb Navigateurs"] = nb_navigateurs
        
        for nav in navigateurs_list:
            if browsers_data[nav]["present"]:
                nb_track = browsers_data[nav]["nb_trackers"]
                row[nav] = f"✓ ({nb_track} tracker{'s' if nb_track > 1 else ''})"
            else:
                row[nav] = "✗"
        
        # Total trackers uniques sur tous les navigateurs
        all_trackers = set()
        for nav_data in browsers_data.values():
            if nav_data["present"]:
                all_trackers.update(nav_data["trackers"])
        row["Total Trackers"] = len(all_trackers)
        
        data_table.append(row)
    
    return pd.DataFrame(data_table)


def graphique_sites_communs_venn(sites_par_nav, trackers_par_nav):
    """Graphique de comparaison entre navigateurs."""
    
    navigateurs = list(sites_par_nav.keys())
    
    if len(navigateurs) < 2:
        print("⚠️ Pas assez de navigateurs pour créer un graphique comparatif")
        return None
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Graphique 1: Nombre de sites par navigateur
    nav_names = []
    sites_counts = []
    trackers_counts = []
    
    for nav in navigateurs:
        nav_names.append(nav)
        sites_counts.append(len(sites_par_nav[nav]))
        trackers_counts.append(len(trackers_par_nav[nav]))
    
    x = range(len(nav_names))
    width = 0.35
    
    bars1 = ax1.bar([i - width/2 for i in x], sites_counts, width, 
                    label='Sites uniques', color='#3498db', alpha=0.8)
    bars2 = ax1.bar([i + width/2 for i in x], trackers_counts, width,
                    label='Trackers uniques', color='#e74c3c', alpha=0.8)
    
    ax1.set_ylabel('Nombre', fontsize=12, fontweight='bold')
    ax1.set_title('Sites et Trackers par Navigateur', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(nav_names, fontsize=11, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    
    # Ajouter les valeurs sur les barres
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Graphique 2: Intersections
    if len(navigateurs) == 2:
        nav1, nav2 = navigateurs[0], navigateurs[1]
        
        sites_communs = len(sites_par_nav[nav1] & sites_par_nav[nav2])
        sites_nav1_only = len(sites_par_nav[nav1] - sites_par_nav[nav2])
        sites_nav2_only = len(sites_par_nav[nav2] - sites_par_nav[nav1])
        
        categories = [f'Uniquement\n{nav1}', 'Communs', f'Uniquement\n{nav2}']
        values = [sites_nav1_only, sites_communs, sites_nav2_only]
        colors = ['#3498db', '#2ecc71', '#e74c3c']
        
        bars = ax2.bar(categories, values, color=colors, alpha=0.8)
        ax2.set_ylabel('Nombre de sites', fontsize=12, fontweight='bold')
        ax2.set_title('Répartition des Sites entre Navigateurs', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        for bar, val in zip(bars, values):
            ax2.text(bar.get_x() + bar.get_width()/2., val,
                    f'{val}\n({val/sum(values)*100:.1f}%)',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.suptitle('Analyse Comparative des Navigateurs', 
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.show()
    
    return fig
    """Extrait la liste complète des sites et trackers."""
    sites_set = set()
    trackers_set = set()
    sites_details = {}  # Pour debug et vérification
    
    for browser, sites in data.items():
        for url, url_data in sites.items():
            result = extraire_tracker_et_site(url)
            
            if result:
                # URL avec tracker : on a le site visité ET le tracker
                site_visite, tracker_domain = result
                sites_set.add(site_visite)
                trackers_set.add(tracker_domain)
                
                # Stocker les détails pour debug
                if site_visite not in sites_details:
                    sites_details[site_visite] = {"type": "avec_tracker", "trackers": set()}
                sites_details[site_visite]["trackers"].add(tracker_domain)
            else:
                # URL sans tracker : c'est un site visité directement
                # Nettoyer l'URL pour extraire le domaine principal
                clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
                
                # Gérer les différents formats d'URL
                if "^" in clean_url:
                    clean_url = clean_url.split("^")[0]
                
                domain = clean_url.split("/")[0].split("?")[0]
                
                # Filtrer les domaines invalides ou vides
                if domain and len(domain) > 2 and "." in domain:
                    sites_set.add(domain)
                    if domain not in sites_details:
                        sites_details[domain] = {"type": "sans_tracker", "trackers": set()}
    
    # Convertir les trackers en liste pour les sites_details
    sites_details_serializable = {}
    for site, details in sites_details.items():
        sites_details_serializable[site] = {
            "type": details["type"],
            "trackers": sorted(list(details["trackers"]))
        }
    
    return sorted(list(sites_set)), sorted(list(trackers_set)), sites_details_serializable


def sauvegarder_listes_json(sites_list, trackers_list, sites_details=None):
    """Sauvegarde les listes de sites et trackers en JSON."""
    
    # Sauvegarder la liste des sites
    sites_data = {
        "total": len(sites_list),
        "sites": sites_list
    }
    
    with open("liste_sites.json", "w", encoding="utf-8") as f:
        json.dump(sites_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Liste des sites sauvegardée: liste_sites.json ({len(sites_list)} sites)")
    
    # Sauvegarder la liste des trackers
    trackers_data = {
        "total": len(trackers_list),
        "trackers": trackers_list
    }
    
    with open("liste_trackers.json", "w", encoding="utf-8") as f:
        json.dump(trackers_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Liste des trackers sauvegardée: liste_trackers.json ({len(trackers_list)} trackers)")
    
    # Sauvegarder les détails (optionnel, pour analyse approfondie)
    if sites_details:
        with open("sites_details.json", "w", encoding="utf-8") as f:
            json.dump(sites_details, f, indent=2, ensure_ascii=False)
        print(f"✅ Détails des sites sauvegardés: sites_details.json")
        
        # Statistiques par type
        avec_tracker = sum(1 for d in sites_details.values() if d["type"] == "avec_tracker")
        sans_tracker = sum(1 for d in sites_details.values() if d["type"] == "sans_tracker")
        print(f"\n   📊 Répartition des sites:")
        print(f"      - Sites avec trackers: {avec_tracker}")
        print(f"      - Sites sans trackers: {sans_tracker}")


def afficher_rapport_complet_enrichi(data):
    """Génère et affiche un rapport complet avec tableaux ET graphiques."""
    
    print("="*100)
    print("RAPPORT D'ANALYSE ENRICHI DES TRACKERS WEB ET DES DONNÉES COLLECTÉES")
    print("="*100 + "\n")
    
    # Analyses
    resultats_trackers = analyser_trackers(data)
    resultats_pii_trackers = analyser_donnees_personnelles_trackers(data)
    resultats_pii_sites = analyser_donnees_sites_sans_trackers(data)
    resultats_tokens = analyser_suspicious_tokens(data)
    types_donnees_globales = analyser_types_donnees_globales(data)
    donnees_par_navigateur = analyser_types_donnees_par_navigateur(data)
    stats_proportion = analyser_proportion_collecte(data)
    
    # ===== SECTION 1: RÉCAPITULATIF =====
    print("📊 1. RÉCAPITULATIF PAR UTILISATEUR")
    print("-"*100)
    print(creer_tableau_resume(resultats_trackers).to_string(index=False), "\n")
    
    # Graphique répartition trackers
    graphique_repartition_trackers_par_navigateur(resultats_trackers)
    print("\n")
    
    # ===== SECTION 2: TOP TRACKERS =====
    print("🔍 2. TOP 15 DES TRACKERS LES PLUS UTILISÉS")
    print("-"*100)
    df_trackers = creer_tableau_top_trackers(resultats_trackers)
    print(df_trackers.to_string(index=False) if not df_trackers.empty else "Aucun tracker détecté.", "\n")
    
    # ===== SECTION 3: DONNÉES PERSONNELLES GLOBALES =====
    print("="*100)
    print("🔒 ANALYSE DES DONNÉES PERSONNELLES COLLECTÉES")
    print("="*100 + "\n")
    
    print("📈 3. TYPES DE DONNÉES PERSONNELLES LES PLUS COLLECTÉES (GLOBAL)")
    print("-"*100)
    df_types_globaux = creer_tableau_types_donnees_globales(types_donnees_globales, top_n=20)
    print(df_types_globaux.to_string(index=False), "\n")
    
    # Graphique types de données globales
    graphique_types_donnees_globales(types_donnees_globales, top_n=15)
    print("\n")
    
    # ===== SECTION 4: DONNÉES PAR NAVIGATEUR =====
    print("👥 4. TYPES DE DONNÉES COLLECTÉES PAR NAVIGATEUR")
    print("-"*100)
    df_types_nav = creer_tableau_types_donnees_par_navigateur(donnees_par_navigateur)
    print(df_types_nav.to_string(index=False), "\n")
    
    # Graphique données par navigateur
    graphique_donnees_par_navigateur(donnees_par_navigateur, top_types=10)
    print("\n")
    
    # ===== SECTION 5: TRACKERS VS SITES =====
    print("🕵️ 5. COLLECTE DE DONNÉES: TRACKERS vs SITES DIRECTS")
    print("-"*100)
    
    print("\n📍 Top Trackers collectant le plus de données:")
    if not resultats_pii_trackers:
        print("Aucune collecte par des trackers détectée.")
    else:
        df_pii_trackers = creer_tableau_collecte_pii_trackers(resultats_pii_trackers, top_n=10)
        print(df_pii_trackers.to_string(index=False))
    
    print("\n🌐 Top Sites (sans tracker) collectant le plus de données:")
    if not resultats_pii_sites:
        print("Aucune collecte par des sites directs détectée.")
    else:
        df_pii_sites = creer_tableau_collecte_sites_sans_trackers(resultats_pii_sites, top_n=10)
        print(df_pii_sites.to_string(index=False))
    
    print("\n")
    
    # Graphique comparatif
    graphique_trackers_vs_sites(resultats_pii_trackers, resultats_pii_sites, top_n=10)
    print("\n")
    
    # ===== SECTION 6: JETONS SUSPECTS =====
    print("="*100)
    print("🔍 6. ANALYSE DES JETONS SUSPECTS (SUSPICIOUS TOKENS)")
    print("="*100 + "\n")
    
    if not resultats_tokens:
        print("Aucun jeton suspect détecté.")
    else:
        df_tokens = creer_tableau_suspicious_tokens(resultats_tokens)
        print(df_tokens.to_string(index=False))
        print("\n")
        # Afficher les graphiques des tokens
        graphique_suspicious_tokens(resultats_tokens)
    print("\n")
    
    # ===== SECTION 7: PROPORTION DE COLLECTE =====
    print("="*100)
    print("📊 7. PROPORTION DE COLLECTE DE DONNÉES (GLOBAL ET PAR TRACKER)")
    print("="*100 + "\n")
    
    df_proportion = pd.DataFrame([
        {
            "Catégorie": "Avec Trackers",
            "Total": stats_proportion["avec_trackers"]["total"],
            "Collectent": stats_proportion["avec_trackers"]["collectent"],
            "Ne collectent pas": stats_proportion["avec_trackers"]["ne_collectent_pas"],
            "% Collectent": f"{stats_proportion['avec_trackers']['pct_collectent']:.1f}%"
        },
        {
            "Catégorie": "Sans Trackers",
            "Total": stats_proportion["sans_trackers"]["total"],
            "Collectent": stats_proportion["sans_trackers"]["collectent"],
            "Ne collectent pas": stats_proportion["sans_trackers"]["ne_collectent_pas"],
            "% Collectent": f"{stats_proportion['sans_trackers']['pct_collectent']:.1f}%"
        },
        {
            "Catégorie": "Global",
            "Total": stats_proportion["global"]["total"],
            "Collectent": stats_proportion["global"]["collectent"],
            "Ne collectent pas": stats_proportion["global"]["ne_collectent_pas"],
            "% Collectent": f"{stats_proportion['global']['pct_collectent']:.1f}%"
        }
    ])
    
    print(df_proportion.to_string(index=False), "\n")
    
    # Graphique des proportions
    graphique_proportion_collecte(stats_proportion)
    print("\n")
    
    # ===== SECTION 8: SITES COMMUNS ENTRE NAVIGATEURS =====
    print("="*100)
    print("🔄 8. ANALYSE DES SITES COMMUNS ENTRE NAVIGATEURS")
    print("="*100 + "\n")
    
    sites_communs, navigateurs_list = analyser_sites_communs_entre_navigateurs(data)
    stats_comp, sites_par_nav, trackers_par_nav = analyser_comparaison_navigateurs(data)
    
    if len(sites_communs) > 0:
        print(f"📊 Nombre de sites présents sur plusieurs navigateurs: {len(sites_communs)}\n")
        
        # Tableau des sites communs
        df_communs = creer_tableau_sites_communs(sites_communs, navigateurs_list, top_n=20)
        print("🔝 Top 20 des sites communs entre navigateurs:")
        print(df_communs.to_string(index=False))
        
        # Sauvegarder en JSON
        sauvegarder_sites_communs_json(sites_communs, navigateurs_list)
        
        # Statistiques détaillées
        print(f"\n📈 Statistiques de comparaison:")
        print(f"   Sites présents sur TOUS les navigateurs: {len(stats_comp['sites_tous_navigateurs'])}")
        print(f"   Trackers présents sur TOUS les navigateurs: {len(stats_comp['trackers_tous_navigateurs'])}")
        
        print(f"\n🎯 Sites/Trackers exclusifs par navigateur:")
        for nav in navigateurs_list:
            nb_sites_exclusifs = len(stats_comp['sites_uniquement_sur'][nav])
            nb_trackers_exclusifs = len(stats_comp['trackers_uniquement_sur'][nav])
            print(f"   • {nav}:")
            print(f"     - Sites exclusifs: {nb_sites_exclusifs}")
            print(f"     - Trackers exclusifs: {nb_trackers_exclusifs}")
        
        # Exemples de sites sur tous les navigateurs
        if len(stats_comp['sites_tous_navigateurs']) > 0:
            print(f"\n🌐 Exemples de sites sur TOUS les navigateurs ({len(stats_comp['sites_tous_navigateurs'])} au total):")
            for i, site in enumerate(sorted(list(stats_comp['sites_tous_navigateurs']))[:10], 1):
                trackers_info = []
                if site in sites_communs:
                    for nav in navigateurs_list:
                        if sites_communs[site][nav]["present"]:
                            nb = sites_communs[site][nav]["nb_trackers"]
                            trackers_info.append(f"{nav}:{nb}")
                tracker_str = " | ".join(trackers_info) if trackers_info else ""
                print(f"   {i}. {site} [{tracker_str}]")
        
        # Graphiques
        print("\n📊 Génération des graphiques comparatifs...")
        graphique_sites_communs_venn(sites_par_nav, trackers_par_nav)
        
        # Heatmap des sites communs
        print("\n🔥 Génération de la heatmap des trackers...")
        graphique_heatmap_sites_communs(sites_communs, navigateurs_list, top_n=30)
        
    else:
        print("⚠️ Aucun site commun trouvé entre les navigateurs.")
    
    print("\n")
    
    # ===== SECTION 9: EXPORT DES LISTES =====
    print("="*100)
    print("💾 9. EXPORT DES LISTES DE SITES ET TRACKERS")
    print("="*100 + "\n")
    
    sites_list, trackers_list, sites_details = extraire_liste_sites_et_trackers(data)
    sauvegarder_listes_json(sites_list, trackers_list, sites_details)
    
    print(f"\n📊 Statistiques finales:")
    print(f"   - Nombre total de sites uniques: {len(sites_list)}")
    print(f"   - Nombre total de trackers uniques: {len(trackers_list)}")
    if len(sites_list) > 0:
        print(f"   - Ratio trackers/sites: {len(trackers_list)/len(sites_list):.2f}")
    
    # Afficher quelques exemples
    print(f"\n📝 Exemples de sites (premiers 10):")
    for i, site in enumerate(sites_list[:10], 1):
        tracker_info = ""
        if site in sites_details:
            nb_trackers = len(sites_details[site]["trackers"])
            if nb_trackers > 0:
                tracker_info = f" ({nb_trackers} tracker{'s' if nb_trackers > 1 else ''})"
        print(f"   {i}. {site}{tracker_info}")
    
    print(f"\n🔍 Exemples de trackers (premiers 10):")
    for i, tracker in enumerate(trackers_list[:10], 1):
        print(f"   {i}. {tracker}")
    
    print("\n" + "="*100)
    print("✅ RAPPORT TERMINÉ")
    print("="*100)
    
    return {
        'resultats_trackers': resultats_trackers,
        'resultats_pii_trackers': resultats_pii_trackers,
        'resultats_pii_sites': resultats_pii_sites,
        'types_donnees_globales': types_donnees_globales,
        'donnees_par_navigateur': donnees_par_navigateur,
        'resultats_tokens': resultats_tokens,
        'stats_proportion': stats_proportion,
        'sites_list': sites_list,
        'trackers_list': trackers_list,
        'sites_communs': sites_communs,
        'stats_comparaison': stats_comp
    }


# ===== EXÉCUTION =====
if __name__ == "__main__":
    print("\n🚀 Démarrage de l'analyse...")
    print(f"📁 Nombre total d'entrées dans les données combinées: {sum(len(sites) for sites in combined_data.values())}")
    print(f"👥 Nombre de navigateurs/utilisateurs: {len(combined_data)}\n")
    
    # Lancer le rapport complet
    resultats = afficher_rapport_complet_enrichi(combined_data)