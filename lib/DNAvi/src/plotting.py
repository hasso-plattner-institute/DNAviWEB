"""

Plotting functions for electropherogram analysis


Author: Anja Hess


Date: 2025-AUG-06

"""
import logging
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.ticker import LogLocator, NullFormatter, ScalarFormatter
from src.constants import PALETTE, ALTERNATE_FORMAT
from matplotlib.patches import Patch
import warnings; warnings.filterwarnings("ignore")
import plotly.express as px
import plotly.graph_objects as go


def _write_html(fig, path):
    fig.update_layout(template="plotly_white")
    fig.write_html(path, include_plotlyjs="cdn")
    del fig


def _format_log_xaxis(ax):
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0,)))
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())


def _color_with_alpha(color, alpha):
    r, g, b, _ = to_rgba(color)
    return f"rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, {alpha})"


def _apply_line_layout(fig, title, x_label, y_label, lower_xlim=None,
                       upper_xlim=None, window=None):
    fig.update_traces(opacity=0.7, connectgaps=True)
    if not x_label:
        x_label = "Size [bp]"
    if not y_label:
        y_label = "Normalized fluorescent units"
    fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label,
                      autosize=True,
                      margin=dict(t=90, r=360, b=75, l=80),
                      showlegend=True,
                      legend=dict(orientation="v", x=1.02, y=1,
                                  xanchor="left", yanchor="top",
                                  bgcolor="rgba(255,255,255,0.9)",
                                  bordercolor="#d0d0d0", borderwidth=1))
    fig.update_xaxes(type="log", dtick=1, tick0=1)
    if window:
        fig.update_xaxes(range=[np.log10(window[0]), np.log10(window[1])])
    elif lower_xlim and upper_xlim:
        fig.update_xaxes(range=[np.log10(lower_xlim), np.log10(upper_xlim)])
    return fig


def _aggregate_for_lineplot(df, x, y, hue=None, style=None, estimator="mean"):
    if estimator is None:
        return df.copy()
    group_cols = [x]
    if hue is not None:
        group_cols.append(hue)
    if style is not None and style not in group_cols:
        group_cols.append(style)
    if estimator == "mean":
        return df.groupby(group_cols, as_index=False)[y].mean()
    if estimator == "median":
        return df.groupby(group_cols, as_index=False)[y].median()
    return df.groupby(group_cols, as_index=False)[y].mean()


def _plotly_line(df, x, y, title, x_label, y_label, output_path, hue=None,
                 units=None, style=None, estimator="mean", lower_xlim=None,
                 window=None):
    if estimator == "mean" and units is None and style is None:
        fig = go.Figure()
        group_cols = [x] if hue is None else [hue, x]
        stats = (
            df.groupby(group_cols, dropna=False)[y]
            .agg(mean="mean", std="std", count="count")
            .reset_index()
            .sort_values(group_cols)
        )
        stats["sem"] = stats["std"].fillna(0) / np.sqrt(stats["count"].clip(lower=1))
        stats["ci"] = 1.96 * stats["sem"]
        stats["lower"] = stats["mean"] - stats["ci"]
        stats["upper"] = stats["mean"] + stats["ci"]

        if hue is None:
            grouped_stats = [("Mean", stats, PALETTE[0])]
        else:
            grouped_stats = [
                (str(group_name), group_stats, PALETTE[i % len(PALETTE)])
                for i, (group_name, group_stats) in enumerate(stats.groupby(hue, dropna=False))
            ]

        for group_name, group_stats, color in grouped_stats:
            fig.add_trace(go.Scatter(
                x=group_stats[x], y=group_stats["upper"],
                mode="lines", line=dict(width=0),
                hoverinfo="skip", showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=group_stats[x], y=group_stats["lower"],
                mode="lines", line=dict(width=0),
                fill="tonexty", fillcolor=_color_with_alpha(color, 0.22),
                hoverinfo="skip", showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=group_stats[x], y=group_stats["mean"],
                mode="lines", line=dict(color=color, width=2),
                name=group_name
            ))

        upper_xlim = stats[x].max() if x in stats else None
        fig = _apply_line_layout(fig, title, x_label, y_label, lower_xlim,
                                 upper_xlim, window)
        _write_html(fig, output_path)
        return

    plot_df = _aggregate_for_lineplot(df, x, y, hue=hue, style=style,
                                      estimator=estimator)
    line_group = units
    if line_group is None and hue is not None:
        line_group = hue
    fig = px.line(plot_df, x=x, y=y, color=hue, line_dash=style,
                  line_group=line_group, title=title,
                  color_discrete_sequence=PALETTE)
    upper_xlim = plot_df[x].max() if x in plot_df else None
    fig = _apply_line_layout(fig, title, x_label, y_label, lower_xlim,
                             upper_xlim, window)
    _write_html(fig, output_path)

def gridplot(df, x, y, save_dir="", title="", y_label="", x_label="",
             cols_not_to_plot=["bp_pos", "normalized_fluorescent_units"],
             ):
    """

    Generate line plot for DNA fragment sizes with masking option for marker peaks

    :param df: pandas.DataFrame
    :param x: str, the plot's x variable
    :param y: str, the plot's y variable
    :param save_dir: str, path to save the figure
    :param title: str, title of the figure
    :param y_label: str, y label of the figure
    :param x_label: str, x label of the figure
    :param cols_not_to_plot: list of columns to exclude from plot to get categorical vars
    :return: plot is generated and saved to disk.
    """

    #####################################################################
    # All in one plot
    #####################################################################
    sns.lineplot(data=df, x=x, y=y, alpha=.7)
    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.title(f"{title}")

    # Log scale
    plt.xscale('log')
    _format_log_xaxis(plt.gca())
    plt.tight_layout()
    plt.savefig(f"{save_dir}{title}_summary.pdf", bbox_inches='tight')
    plt.savefig(f"{save_dir}{title}_summary.{ALTERNATE_FORMAT}", bbox_inches='tight')
    plt.close()
    _plotly_line(df, x, y, title=f"{title}", x_label=x_label,
                 y_label=y_label, output_path=f"{save_dir}{title}_summary.html")
    #####################################################################
    # By category
    #####################################################################
    cat_vars = [c for c in df.columns if c not in cols_not_to_plot]
    for col in cat_vars:
        #################################################################
        # Clustermap
        #################################################################
        # In case marker is in reduce to one entry per sample
        df["sample-bp"] = df[x].astype(str) + "_" + df["sample"].astype(str)
        prep_df = df.drop_duplicates(subset=["sample-bp"])
        del prep_df["sample-bp"]

        # Now ready to be transformed to wide
        if col == "sample":
            # Allows to plot clustermap even when no group data is provided
            wide_df = prep_df.pivot(index=col, columns=x,
                                    values=y).reset_index()
        else:
            wide_df = prep_df.pivot(index=["sample", col], columns=x,
                               values=y).reset_index()
        required_colors = round(int(len(wide_df[col].unique())/5))
        if required_colors <= 5:
            required_colors = 2
        lut = dict(zip(wide_df[col].unique(), PALETTE)) #sns.color_palette(palette='colorblind')*required_colors
        row_colors = wide_df[col].map(lut)

        sns.clustermap(wide_df.drop(columns=["sample", col]),
                       rasterized=True, row_cluster=True,
                       cmap="YlGnBu",yticklabels=False,xticklabels=False,
                       col_cluster=False, row_colors=row_colors)
        handles = [Patch(facecolor=lut[name]) for name in lut]
        plt.legend(handles, lut, title=col,
                   bbox_to_anchor=(1, 1),
                   bbox_transform=plt.gcf().transFigure, loc='upper right')
        plt.tight_layout()
        plt.savefig(f"{save_dir}cluster_by_{col}.pdf", bbox_inches="tight")
        plt.savefig(f"{save_dir}cluster_by_{col}.{ALTERNATE_FORMAT}", bbox_inches="tight")
        plt.close()
        #################################################################
        # Overview by condition
        #################################################################
        print(f"--- Plotting by {col}")
        hue = col
        sns.lineplot(data=df, x=x, y=y, alpha=.7,
                     palette=PALETTE[:len(df[hue].unique())],
                     hue=hue)
        # Add labels
        plt.ylabel(y_label)
        plt.xlabel(x_label)
        plt.title(f"{title} by {col}")
        plt.xscale('log')
        _format_log_xaxis(plt.gca())
        plt.tight_layout()
        plt.savefig(f"{save_dir}{title}_by_{col}.pdf", bbox_inches='tight')
        plt.savefig(f"{save_dir}{title}_by_{col}.{ALTERNATE_FORMAT}",
                    bbox_inches='tight')
        plt.close()

        ###################################################################
        # Interactive version
        ###################################################################
        _plotly_line(df, x, y, hue=col, title=f"{title} by {col}",
                     x_label=x_label, y_label=y_label,
                     output_path=f"{save_dir}{title}_by_{col}.html")
    #####################################################################
    # 2. Plot
    #####################################################################
    print("--- Sample grid plot")
    hue="sample"
    g = sns.FacetGrid(df, col=hue, hue=hue, col_wrap=3, palette=PALETTE)
    g.map(sns.lineplot, x, y, alpha=.7)
    g.add_legend(loc='center left', bbox_to_anchor=(1, 0.5))
    # Add labels
    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.suptitle(f"{title}")
    plt.xscale('log')
    for ax in g.axes.flat:
        _format_log_xaxis(ax)
    plt.tight_layout()
    plt.savefig(f"{save_dir}{title}.pdf", bbox_inches="tight")
    plt.savefig(f"{save_dir}{title}.{ALTERNATE_FORMAT}", bbox_inches="tight")
    plt.close()
    fig = px.line(df, x=x, y=y, color=hue, facet_col=hue, facet_col_wrap=3,
                  title=f"{title}", color_discrete_sequence=PALETTE,
                  facet_row_spacing=0.16)
    n_facets = df[hue].nunique()
    n_rows = int(np.ceil(n_facets / 3))
    fig.update_layout(height=max(650, n_rows * 360))
    fig = _apply_line_layout(fig, f"{title}", x_label, y_label,
                             upper_xlim=df[x].max())
    fig.update_xaxes(title_text=x_label or "Size [bp]")
    fig.update_yaxes(title_text=y_label or "Normalized fluorescent units")
    _write_html(fig, f"{save_dir}{title}.html")
    # END OF FUNCTION


def p2stars(p):
    """
    Add asterisk based on p-value
    :param p: float, the p-value
    :return: str
    """
    if p > 0.05:
        return "ns"
    if p < 0.001:
        return '***'
    elif p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    # END OF FUNCTION


def stats_plot(path_to_df, cols_not_to_plot=None, region_id="region_id",
               y="value", cut=False):
    """
    Plot statistical results
    :param path_to_df: str
    :param cols_not_to_plot: list of columns to exclude from plot
    :return: plots statistics in same directory as input dataframe
    """
    df = pd.read_csv(path_to_df, index_col=0)
    sns.set_context("paper")
    #####################################################################
    # Remove peaks where all values are 0
    #####################################################################
    cat_counts = df.groupby([region_id])[y].sum()

    peaks_without_vals = cat_counts[cat_counts == 0].index.tolist()
    if peaks_without_vals:
        logging.info(f"--- Not plotting {peaks_without_vals}")
    df = df[~df[region_id].isin(peaks_without_vals)]
    #####################################################################
    # 1. Plot grid based on every available metric in peak_id
    #####################################################################
    for categorical_var in (["sample"] +  [e for e in df.columns if
                             e not in cols_not_to_plot]):
        plot_df = df.copy()
        print(f"--- Plotting by {categorical_var}")
        #################################################################
        # If possible, get the p value, anno stars
        #################################################################
        possible_stats_dir = (path_to_df.rsplit("/", 1)[0] +
                              f"/group_statistics_by_{categorical_var}.csv")

        if os.path.exists(possible_stats_dir):
            stats_info = pd.read_csv(possible_stats_dir, index_col=0
                                     ).round({'p_value': 3})
            stats_dict = pd.Series(stats_info.p_value.values,
                                   index=stats_info.peak_name).to_dict()
            plot_df["p_val"] = plot_df[region_id].map(stats_dict)
            plot_df["stars"] = plot_df["p_val"].apply(p2stars)
            plot_df[region_id] = (plot_df[region_id].astype(str) + " \n p=" +
                             plot_df["p_val"].astype(str)) + " (" + plot_df["stars"] + ")"
        # Check all peaks are there
        peak_ids = plot_df[region_id].value_counts().index.tolist()
        if not peak_ids:
            print(f"No peaks {categorical_var}")
            continue
        #################################################################
        # Create the grid plot
        #################################################################
        if categorical_var == "sample":
            g = sns.FacetGrid(plot_df, col=region_id, col_wrap=4, hue=categorical_var,
                              sharex=True, sharey=False, palette=PALETTE,
                              height=4.8, aspect=1.45)
            g.map(sns.barplot, categorical_var, y, palette=PALETTE,
                  )
        else:
            g = sns.FacetGrid(plot_df, col=region_id, col_wrap=3, hue=categorical_var,
                              sharex=True, sharey=False, palette=PALETTE,
                              height=6.5, aspect=1.05)
            if cut:
                g.map(sns.violinplot, categorical_var, y, inner_kws=dict(box_width=5, whis_width=2, color="black"),
                      edgecolor="black", alpha=.7, cut=0)
            else:
                g.map(sns.violinplot, categorical_var, y, inner_kws=dict(box_width=5, whis_width=2, color="black"),
                      edgecolor="black", alpha=.7)
            g.map(sns.stripplot, categorical_var, y, color="white", linewidth=1, edgecolor="black")
        if categorical_var == "sample":
            plt.subplots_adjust(hspace=0.6, wspace=1.1)
        else:
            plt.subplots_adjust(hspace=0.25, wspace=1.5)
        # Rotate x-axis labels
        for ax in g.axes.flat:
            plt.setp(ax.get_xticklabels(), rotation=90, visible=True)
            plt.setp(ax.get_yticklabels(), visible=True)
            ax.tick_params(axis="both", which="both",
                           labelbottom=True, labelleft=True)
        plt.savefig(path_to_df.replace(".csv", f"_{categorical_var}.pdf"), bbox_inches="tight")
        plt.savefig(path_to_df.replace(".csv", f"_{categorical_var}.{ALTERNATE_FORMAT}"), bbox_inches="tight")
        plt.close()

        #################################################################
        # Interactive version
        #################################################################
        if categorical_var == "sample":
            n_facets = plot_df[region_id].nunique()
            n_rows = int(np.ceil(n_facets / 2))
            row_spacing = 0.08 if n_rows <= 2 else min(0.03, 0.22 / (n_rows - 1))
            plot_df[categorical_var] = plot_df[categorical_var].astype(str)
            sample_labels = plot_df[categorical_var].drop_duplicates().tolist()
            fig = px.bar(plot_df, x=categorical_var, y=y,
                facet_col=region_id, facet_col_wrap=2,
                barmode="group", facet_row_spacing=row_spacing,
                facet_col_spacing=0.12)
            fig.update_traces(width=0.8, marker_color="#006400",
                              marker_line_color="black", marker_line_width=1)
            fig.update_layout(height=max(1200, n_rows * 900), width=1800,
                              margin=dict(t=80, r=60, b=130, l=70),
                              showlegend=False)
            fig.update_xaxes(tickmode="array", tickvals=sample_labels,
                             ticktext=sample_labels)
            fig.for_each_annotation(lambda annotation: annotation.update(yshift=10))
        else:
            violin_span = "hard" if cut else None
            fig = px.violin(plot_df, x=categorical_var, y=y, color=categorical_var,
                facet_col=region_id, facet_col_wrap=3, color_discrete_sequence=PALETTE,
                points="all", box=True, violinmode="group",
                facet_row_spacing=0.025, facet_col_spacing=0.045)

            if violin_span is not None:
                fig.update_traces(spanmode=violin_span)
            fig.update_traces(jitter=0.15, pointpos=0)
            n_facets = plot_df[region_id].nunique()
            n_rows = int(np.ceil(n_facets / 3))
            fig.update_layout(height=max(1050, n_rows * 700), width=1300,
                              margin=dict(t=80, r=40, b=80, l=70),
                              showlegend=False)
            fig.for_each_annotation(lambda annotation: annotation.update(yshift=14))
        fig.update_xaxes(tickangle=90)
        fig.update_xaxes(showticklabels=True, showline=True, linecolor="black",
                         linewidth=2, ticks="outside", tickcolor="black",
                         mirror=True)
        fig.update_yaxes(showticklabels=True, showline=True, linecolor="black",
                         linewidth=2, ticks="outside", tickcolor="black",
                         mirror=True, gridcolor="#d0d0d0", nticks=14,
                         zeroline=True, zerolinecolor="black",
                         zerolinewidth=1)
        # Force unmatching:
        fig.for_each_yaxis(lambda ax: ax.update(matches=None,
                                                autorange=True))
        _write_html(fig, path_to_df.replace(".csv", f"_{categorical_var}.html"))
    plt.close()
    # END OF FUNCTION




def peakplot(array, peaks, ladder_id, ref, i, qc_save_dir, y_label="",x_label="",
             size_values=""):
    """

    Plot the peaks detected in a DNA size profile

    :param array: np.ndarray
    :param peaks: list of int
    :param ladder_id: str or int, name of the ladder
    :param ref: dtr, type of reference
    :param i: int, index of the ladder (potentially multiple)
    :param qc_save_dir: str, path to folder to save the figure to
    :param y_label: str, y label name
    :param x_label: str, x label name
    :return: plots are generated and saved to disk.
    """

    # Remove upper / right spine to improve aesthetics
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.top'] = False
    plt.plot(array)
    plt.plot(peaks, array[peaks], "x")
    # Add the annotated base-pair values if possible
    max_x = len(array) # relative val for label
    center_factor = max_x * 0.035 # labels look prettier when up
    if size_values:
        for i, (x, y) in enumerate(zip(peaks, array[peaks])):
            if type(x) != np.int64:
                real_pos = round(size_values[x])
            else:
                real_pos = size_values[i]
            plt.annotate(f"{round(real_pos,1)} bp", xy=(x-center_factor, y+0.04),
                         size=7)
    plt.plot(np.zeros_like(array), "--", color="gray")
    plt.title(ladder_id)
    plt.xlim(10 ^ 0, None)
    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.tight_layout()
    plt.savefig(f"{qc_save_dir}peaks_{i}_{ref}.pdf", bbox_inches="tight")
    plt.savefig(f"{qc_save_dir}peaks_{i}_{ref}.{ALTERNATE_FORMAT}", bbox_inches="tight")
    plt.close()

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=array, mode="lines", name=str(ladder_id)))
    fig.add_trace(go.Scatter(x=peaks, y=array[peaks], mode="markers",
                             marker_symbol="x", marker_size=9,
                             name="Peaks"))
    fig.add_trace(go.Scatter(y=np.zeros_like(array), mode="lines",
                             line=dict(color="gray", dash="dash"),
                             name="Baseline"))
    if size_values:
        annotations = []
        for peak_index, (x_pos, y_pos) in enumerate(zip(peaks, array[peaks])):
            if type(x_pos) != np.int64:
                real_pos = round(size_values[x_pos])
            else:
                real_pos = size_values[peak_index]
            annotations.append(dict(x=x_pos, y=y_pos + 0.04,
                                    text=f"{round(real_pos, 1)} bp",
                                    showarrow=False, font=dict(size=10)))
        fig.update_layout(annotations=annotations)
    fig.update_layout(title=str(ladder_id), xaxis_title=x_label,
                      yaxis_title=y_label)
    fig.update_xaxes(range=[1, len(array)])
    _write_html(fig, f"{qc_save_dir}peaks_{i}_{ref}.html")

    # END OF FUNCTION


def lineplot(df, x, y, save_dir="", title="", y_label="", x_label="",
             hue=None, units=None, plot_lower=False, estimator="mean",
             style=None, window=False):
    """

    Core line plot function for DNA fragment sizes

    :param df: pandas.DataFrame
    :param x: x variable
    :param y: y variable
    :param save_dir: str, path to save the figure
    :param title: str, title of the figure
    :param y_label: str, y label of the figure
    :param x_label: str, x label of the figure
    :param hue: str, optional to set hue parameter
    :param units: bool
    :param plot_lower: bool
    :param estimator: str, which estimator to use
    :param style: str, style of line plot
    :param window: bool or tuple for x axis limits
    :return: plots are generated and saved to disk.
    """

    #####################################################################
    # 1. Special settings
    #####################################################################
    if window:
        save_dir = save_dir + f"/window_{window[0]}-{window[1]}_bp/"
        os.makedirs(save_dir, exist_ok=True)
    if plot_lower:
        lower_xlim = 10 ^ 0
    else:
        lower_xlim = 40  # markers are < 40 bps exc. gDNA
    if units:
        estimator = None

    #####################################################################
    # 2. Plot
    #####################################################################
    fig, ax = plt.subplots()

    if hue is not None:
        n_cats = len(df[hue].unique())
        sns.lineplot(data=df, x=x, y=y, hue=hue,
                     palette=PALETTE[:n_cats], units=units,
                     estimator=estimator,
                     style=style)
    else:
        sns.lineplot(data=df, x=x, y=y, units=units,
                     estimator=estimator,
                     style=style)
    plt.title(f"{title}")
    plt.xscale('log')
    _format_log_xaxis(ax)
    ax.yaxis.set_major_formatter(ScalarFormatter())
    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.xlim(lower_xlim, None)
    if window:
        plt.xlim(window[0], window[1])
    plt.tight_layout()
    plt.savefig(f"{save_dir}{title}.pdf", bbox_inches="tight")
    plt.savefig(f"{save_dir}{title}.{ALTERNATE_FORMAT}", bbox_inches="tight")
    plt.close()
    _plotly_line(df, x, y, hue=hue, units=units, style=style,
                 estimator=estimator, title=f"{title}", x_label=x_label,
                 y_label=y_label, output_path=f"{save_dir}{title}.html",
                 lower_xlim=lower_xlim, window=window)
    # END OF FUNCTION


def ladderplot(df, ladder2type, qc_save_dir, y_label="", x_label=""):
    """

    Plot multiple ladders into one plot

    :param df: pandas.DataFrame
    :param ladder2type: dict
    :param qc_save_dir: str
    :param y_label: str, y label of the figure
    :param x_label: str, x label of the figure
    :return: plot generated and saved to the QC directory

    """

    fig, ax = plt.subplots()
    for i, ladder in enumerate([e for e in df.columns if "Ladder" in e and
                                                         "interpol" not in e]):
        sns.lineplot(data=df, x=f"{ladder}_interpol", y=ladder,
                     color=PALETTE[i], label=ladder2type[ladder])
        plt.title(f"All ladders, interpolated")
        plt.xscale('log')
        _format_log_xaxis(ax)
        ax.yaxis.set_major_formatter(ScalarFormatter())
    plt.xlim(10 ^ 0, None)
    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.tight_layout()
    plt.savefig(f"{qc_save_dir}peaks_all_interpolated.pdf", bbox_inches="tight")
    plt.savefig(f"{qc_save_dir}peaks_all_interpolated.{ALTERNATE_FORMAT}", bbox_inches="tight")
    plt.close()

    fig = go.Figure()
    for i, ladder in enumerate([e for e in df.columns if "Ladder" in e and
                                                         "interpol" not in e]):
        fig.add_trace(go.Scatter(x=df[f"{ladder}_interpol"], y=df[ladder],
                                 mode="lines", name=ladder2type[ladder],
                                 line=dict(color=PALETTE[i % len(PALETTE)])))
    max_bp = max([df[f"{ladder}_interpol"].max() for ladder in
                  [e for e in df.columns if "Ladder" in e and
                   "interpol" not in e]])
    fig = _apply_line_layout(fig, "All ladders, interpolated", x_label,
                             y_label, lower_xlim=10, upper_xlim=max_bp)
    _write_html(fig, f"{qc_save_dir}peaks_all_interpolated.html")
    # END OF FUNCTION