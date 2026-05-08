import xlsxwriter
import os
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import openpyxl
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
import matplotlib.animation as animation
import matplotlib.patches as mpatches
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# --- 1. CONFIGURATIONS DE VITESSE (À laisser en haut) ---
mpl.style.use('fast')  # Active les optimisations de rendu
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['agg.path.chunksize'] = 10000

# Tentative d'utilisation du moteur ultra-rapide TkAgg
try:
    mpl.use('TkAgg')
except:
    pass

# --- 2. CODE SOURCE ---
"""
╔══════════════════════════════════════════════════════════════╗
║          🛒 AUTOMATISATION DES VENTES — E-COMMERCE           ║
║               Projet de Fin d'Année — Logiciels              ║
╚══════════════════════════════════════════════════════════════╝

Auteur : Mariem Saffar, Mouna Belhiba, Chawk Mejri
"""
# ─────────────────────────────────────────────
#  ⚙️  IMPORTING LIBRARIES
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
#  ⚙️  CONSTANTES GLOBALES
# ─────────────────────────────────────────────
TAUX_TVA = 0.20
FICHIER_ENTREE = "ventes.csv"
FICHIER_SORTIE = "resultats_final.csv"

# ─────────────────────────────────────────────
#  🎨  PALETTE "TERMINAL ACID"
# ─────────────────────────────────────────────
FOND = "#0D0D0D"
FOND_CARTE = "#141414"
GRILLE = "#1F1F1F"
VERT_ACID = "#AAFF00"
CYAN_ELEC = "#00F5D4"
ORANGE_FEU = "#FF6B00"
ROSE_CHOC = "#FF2D78"
BLANC_DOUX = "#E8E8E8"
GRIS_MED = "#666666"
PALETTE_PIE = [VERT_ACID, CYAN_ELEC, ORANGE_FEU, ROSE_CHOC,
               "#9B5DE5", "#F4D35E", "#EE4266"]
FRAMES = 45


# ─────────────────────────────────────────────
#  🔧  UTILITAIRES
# ─────────────────────────────────────────────
def _style_ax(ax):
    """Applique le fond et les couleurs d'axes sur tous les panneaux."""
    ax.set_facecolor(FOND_CARTE)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRILLE)
    ax.tick_params(colors=GRIS_MED)
    ax.xaxis.label.set_color(GRIS_MED)
    ax.yaxis.label.set_color(GRIS_MED)


def _titre(ax, texte):
    """Titre de panneau avec barre colorée à gauche."""
    ax.set_title(texte, color=BLANC_DOUX, fontsize=11,
                 fontweight="bold", loc="left", pad=10,
                 fontfamily="monospace")


# ─────────────────────────────────────────────
#  📊  GRAPHIQUE 1 — Histogramme animé CA Net
# ─────────────────────────────────────────────
def _graphique_histogramme(ax, df, valeur_max):
    _style_ax(ax)
    _titre(ax, "▌ Distribution  CA Net")

    counts, edges = np.histogram(df["CA_Net"], bins=min(len(df), 50))
    couleurs = [VERT_ACID if i == counts.argmax() else "#2A2A2A"
                for i in range(len(counts))]

    bars = ax.bar(
        edges[:-1], np.zeros(len(counts)),
        width=np.diff(edges),
        color=couleurs,
        edgecolor=FOND, linewidth=0.4, align="edge"
    )

    ax.set_ylim(0, counts.max() * 1.18)
    ax.axvline(valeur_max, color=ORANGE_FEU, linewidth=1.5,
               linestyle="--", label=f"Max : {valeur_max:,.0f} €",
               alpha=0.9)

    cmap = LinearSegmentedColormap.from_list(
        "acid", ["#1A1A1A", CYAN_ELEC], N=len(counts)
    )
    for i, bar in enumerate(bars):
        if couleurs[i] != VERT_ACID:
            bar.set_color(cmap(i / len(counts)))

    ax.set_xlabel("Montant (€)")
    ax.set_ylabel("Nombre de ventes")
    ax.legend(facecolor=FOND, labelcolor=ORANGE_FEU, fontsize=8,
              framealpha=0.6)
    ax.grid(axis="y", color=GRILLE, linewidth=0.5, alpha=0.6)

    def animate(frame):
        progress = (frame + 1) / FRAMES
        for bar, h in zip(bars, counts):
            bar.set_height(h * progress)
        return bars

    return animation.FuncAnimation(
        ax.get_figure(), animate,
        frames=FRAMES, interval=25, blit=True, repeat=False
    )


# ─────────────────────────────────────────────
#  📊  GRAPHIQUE 2 — Donut CA par Remise
# ─────────────────────────────────────────────
def _graphique_donut(ax, df):
    _titre(ax, "▌ CA Net  par  Remise")

    repartition = df.groupby("Remise")["CA_Net"].sum()
    wedges, texts, autotexts = ax.pie(
        repartition,
        labels=[f"{int(r)} %" for r in repartition.index],
        autopct="%1.1f%%",
        startangle=110,
        colors=PALETTE_PIE[: len(repartition)],
        wedgeprops={"edgecolor": FOND, "linewidth": 2, "width": 0.52},
        pctdistance=0.76
    )
    for t in texts:
        t.set_color(GRIS_MED)
        t.set_fontsize(8)
        t.set_fontfamily("monospace")
    for at in autotexts:
        at.set_color(FOND)
        at.set_fontweight("bold")
        at.set_fontsize(7.5)

    part_dom = repartition.idxmax()
    pct_dom = repartition.max() / repartition.sum() * 100
    ax.text(0, 0.12, f"{pct_dom:.1f}%",
            ha="center", va="center", fontsize=19,
            fontweight="bold", color=VERT_ACID,
            transform=ax.transAxes)
    ax.text(0, -0.04, f"remise {int(part_dom)}%",
            ha="center", va="center", fontsize=8,
            color=GRIS_MED, transform=ax.transAxes,
            fontfamily="monospace")


# ─────────────────────────────────────────────
#  📊  GRAPHIQUE 3 — Carte Meilleur Produit
# ─────────────────────────────────────────────
def _graphique_carte(ax, id_prod, valeur_max, prix, qte, remise):
    _style_ax(ax)
    _titre(ax, "▌ Produit  le  Plus  Rentable")
    ax.axis("off")

    rect = mpatches.FancyBboxPatch(
        (0.08, 0.52), 0.84, 0.38,
        boxstyle="round,pad=0.03",
        linewidth=1.5,
        edgecolor=VERT_ACID,
        facecolor="#0F1A00",
        transform=ax.transAxes, zorder=2
    )
    ax.add_patch(rect)

    ax.text(0.50, 0.83, "ID PRODUIT",
            ha="center", va="center", fontsize=8,
            color=GRIS_MED, transform=ax.transAxes,
            fontfamily="monospace")
    ax.text(0.50, 0.67, f"# {int(id_prod)}",
            ha="center", va="center", fontsize=30,
            fontweight="bold", color=VERT_ACID,
            transform=ax.transAxes, fontfamily="monospace")

    infos = [
        ("CA Net", f"{valeur_max:,.2f} €"),
        ("Prix", f"{prix:.2f} €"),
        ("Quantité", f"{int(qte)} unités"),
        ("Remise", f"{int(remise)} %"),
    ]
    for i, (label, valeur) in enumerate(infos):
        y = 0.46 - i * 0.105
        ax.text(0.14, y, label,
                ha="left", va="center", fontsize=8.5,
                color=GRIS_MED, transform=ax.transAxes,
                fontfamily="monospace")
        ax.text(0.88, y, valeur,
                ha="right", va="center", fontsize=8.5,
                fontweight="bold", color=BLANC_DOUX,
                transform=ax.transAxes)
        ax.plot([0.12, 0.88], [y - 0.040, y - 0.040],
                color=GRILLE, linewidth=0.6,
                transform=ax.transAxes)

    ax_sp = ax.inset_axes([0.08, 0.02, 0.84, 0.13])
    sx = np.linspace(0, 1, 40)
    sy = np.cumsum(np.random.randn(40) * 0.4) + np.linspace(0, 2, 40)
    ax_sp.plot(sx, sy, color=CYAN_ELEC, linewidth=1.6, alpha=0.9)
    ax_sp.fill_between(sx, sy, sy.min(), alpha=0.12, color=CYAN_ELEC)
    ax_sp.axis("off")
    ax_sp.set_facecolor(FOND_CARTE)
    ax.text(0.50, 0.025, "tendance simulée",
            ha="center", fontsize=7, color=CYAN_ELEC,
            transform=ax.transAxes, fontfamily="monospace")


# ─────────────────────────────────────────────
#  📊  GRAPHIQUE 4 — Bullet Chart Top 10
# ─────────────────────────────────────────────
def _graphique_top10(ax, df, valeur_max):
    _style_ax(ax)
    _titre(ax, "▌ Top 10  Produits  — Bullet  Chart")

    top10 = df.nlargest(10, "CA_Net")[["ID", "CA_Net"]].reset_index(drop=True)
    labels = [f"#{int(p)}" for p in top10["ID"]]
    valeurs = top10["CA_Net"].values
    ca_max = df["CA_Net"].max()
    y_pos = list(range(len(top10) - 1, -1, -1))
    couleurs = [VERT_ACID, CYAN_ELEC, ORANGE_FEU] + [ROSE_CHOC] * 7

    for i in y_pos:
        ax.barh(i, ca_max, color="#191919", height=0.60, zorder=1)

    bullet_bars = []
    for i, (val, col) in enumerate(zip(valeurs, couleurs)):
        idx = len(top10) - 1 - i
        b = ax.barh(idx, 0, color=col, height=0.60, alpha=0.88, zorder=2)
        bullet_bars.append((b, val))
        ax.text(ca_max * 1.02, idx, f"{val:,.0f} €",
                va="center", color=BLANC_DOUX, fontsize=7.5,
                fontfamily="monospace")

    ref_line = ax.axvline(0, color=VERT_ACID, linewidth=1.2,
                          linestyle=":", zorder=3, alpha=0.75)

    def animate(frame):
        progress = min((frame + 1) / FRAMES, 1.0)
        for b, target in bullet_bars:
            b[0].set_width(target * progress)
        ref_line.set_xdata([valeur_max * progress] * 2)
        return [b[0] for b, _ in bullet_bars] + [ref_line]

    ani = animation.FuncAnimation(
        ax.get_figure(), animate,
        frames=FRAMES, interval=25, blit=True, repeat=False
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=BLANC_DOUX, fontsize=8.5,
                       fontfamily="monospace")
    ax.set_xlabel("CA Net (€)")
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, ca_max * 1.22)
    ax.grid(axis="x", color=GRILLE, linewidth=0.5, alpha=0.6)

    legende = [
        mpatches.Patch(color=VERT_ACID, label="🥇 1er"),
        mpatches.Patch(color=CYAN_ELEC, label="🥈 2e"),
        mpatches.Patch(color=ORANGE_FEU, label="🥉 3e"),
        mpatches.Patch(color=ROSE_CHOC, label="Top 10"),
    ]
    ax.legend(handles=legende, facecolor=FOND, labelcolor=BLANC_DOUX,
              fontsize=7.5, loc="lower right", framealpha=0.5)

    return ani


# ══════════════════════════════════════════════
#  BONUS — Exporter Excel formaté
# ══════════════════════════════════════════════
def exporter_excel(resultats: list[dict],
                   chemin: str = "resultats_final.xlsx") -> None:
    df = pd.DataFrame(resultats)

    with pd.ExcelWriter(chemin, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Résultats Ventes", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Résultats Ventes"]

        header_fmt = workbook.add_format({
            "bold": True, "bg_color": "#1F4E79",
            "font_color": "#FFFFFF", "align": "center", "border": 1
        })
        pair_fmt = workbook.add_format({
            "bg_color": "#D6E4F0", "align": "center", "border": 1
        })
        impair_fmt = workbook.add_format({
            "bg_color": "#FFFFFF", "align": "center", "border": 1
        })

        for col_idx, col_name in enumerate(df.columns):
            worksheet.write(0, col_idx, col_name, header_fmt)

        for row_idx, row in enumerate(df.itertuples(index=False), 1):
            fmt = pair_fmt if row_idx % 2 == 0 else impair_fmt
            for col_idx, val in enumerate(row):
                worksheet.write(row_idx, col_idx, val, fmt)

        for col_idx, col_name in enumerate(df.columns):
            max_len = max(
                df[col_name].astype(str).map(len).max(),
                len(col_name)
            ) + 2
            worksheet.set_column(col_idx, col_idx, max_len)

    print(f"✅  Excel formaté sauvegardé dans '{chemin}'.\n")


# ─────────────────────────────────────────────
#  🚀  FONCTION PRINCIPALE
# ─────────────────────────────────────────────
def lancer_analyse_performante():
    print("╔════════════════════════════════════════════════════════╗")
    print("║          🚀 DÉMARRAGE DU MOTEUR D'ANALYSE              ║")
    print("╚════════════════════════════════════════════════════════╝")

    try:
        saisie = input("\nNombre de ventes à générer (ex: 100, 1000000) : ").replace(" ", "")
        n = int(saisie)
    except ValueError:
        print("❌ Erreur : veuillez entrer un entier valide.")
        return

    start = time.time()

    try:
        print(f"\n⏳ Génération de {n:,} lignes…")
        df = pd.DataFrame({
            "ID": np.arange(1001, 1001 + n),
            "Prix": np.round(np.random.uniform(5.0, 500.0, n), 2),
            "Quantite": np.random.randint(1, 51, n),
            "Remise": np.random.choice([0, 5, 10, 15, 20, 25, 30], n),
        })

        df.to_csv(FICHIER_ENTREE, index=False)
        print(f"📁 '{FICHIER_ENTREE}' généré.")
        df = pd.read_csv(FICHIER_ENTREE)

        df["CA_Brut"] = df["Prix"] * df["Quantite"]
        df["CA_Net"] = df["CA_Brut"] * (1 - df["Remise"] / 100)
        df["TVA"] = df["CA_Net"] * TAUX_TVA
        df["CA_TTC"] = df["CA_Net"] + df["TVA"]
        df = df.sort_values(by="CA_Net", ascending=True)

        print("\n" + "═" * 65)
        print(f"📊 RAPPORT — {n:,} TRANSACTIONS")
        print("-" * 65)

        cols = ["ID", "Prix", "Quantite", "Remise", "CA_Net", "CA_TTC"]
        if n <= 20:
            print(df[cols].to_string(index=False))
        else:
            print("Aperçu (5 premières lignes) :")
            print(df[cols].head(5).to_string(index=False))
            print(f"\n… [ {n:,} lignes traitées ] …")

        print("-" * 65)

        ca_total = df["CA_TTC"].sum()
        idx_max = df["CA_Net"].idxmax()
        id_meilleur = df.loc[idx_max, "ID"]
        valeur_max = df["CA_Net"].max()
        prix_meilleur = df.loc[idx_max, "Prix"]
        qte_meilleur = df.loc[idx_max, "Quantite"]
        remise_meilleur = df.loc[idx_max, "Remise"]

        print(f"💰 CA TOTAL (TTC)              : {ca_total:,.2f} €")
        print(f"🏆 MEILLEURE VENTE (NET)       : {valeur_max:,.2f} €")
        print(f"🥇 ID — PLUS GROS BÉNÉFICE    : {id_meilleur}")
        print("═" * 65)

        if n <= 2_000_000:
            df.to_csv(FICHIER_SORTIE, index=False)
            if n <= 1_000_000:
                resultats_dict = df.to_dict(orient="records")
                exporter_excel(resultats_dict)
            print(f"💾 Résultats exportés dans '{FICHIER_SORTIE}'")
        else:
            print("⚠️  Volume > 2M : export CSV désactivé.")

        # ─────────────────────────────────────────────────────────
        # --- 3. VOS TRACÉS — 4 panneaux animés
        # ─────────────────────────────────────────────────────────
        if n > 1:
            print("\n📊 Rendu des graphiques…")

            fig = plt.figure(figsize=(22, 10), facecolor=FOND)
            fig.suptitle(
                f"TABLEAU DE BORD  //  {n:,} TRANSACTIONS",
                fontsize=14, fontweight="bold",
                color=VERT_ACID, y=0.98,
                fontfamily="monospace"
            )

            gs = GridSpec(2, 2, figure=fig,
                          hspace=0.42, wspace=0.32,
                          left=0.06, right=0.97,
                          top=0.93, bottom=0.08)

            ax1 = fig.add_subplot(gs[0, 0])
            ax2 = fig.add_subplot(gs[0, 1])
            ax3 = fig.add_subplot(gs[1, 0])
            ax4 = fig.add_subplot(gs[1, 1])

            fig.add_artist(
                plt.Line2D([0.06, 0.97], [0.955, 0.955],
                           transform=fig.transFigure,
                           color=VERT_ACID, linewidth=0.8, alpha=0.5)
            )

            ani1 = _graphique_histogramme(ax1, df, valeur_max)
            _graphique_donut(ax2, df)
            _graphique_carte(ax3, id_meilleur, valeur_max,
                             prix_meilleur, qte_meilleur, remise_meilleur)
            ani4 = _graphique_top10(ax4, df, valeur_max)

            print(f"✅ Terminé en {time.time() - start:.4f} s")
            print("💡 INFO : Fermez la fenêtre du graphique pour ouvrir le fichier Excel.")

            # --- 4. EXÉCUTION ---
            plt.show()

            if n <= 1_000_000:
                print("💡 Ouverture automatique du tableau Excel...")
                os.startfile("resultats_final.xlsx")
        else:
            print(f"✅ Terminé en {time.time() - start:.4f} s")

        print("✨ Analyse terminée avec succès !\n")

    except MemoryError:
        print("\n❌ Mémoire insuffisante pour ce volume de données.")


# --- 4. EXÉCUTION ---
if __name__ == "__main__":
    lancer_analyse_performante()