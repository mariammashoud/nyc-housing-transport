"""Plotly figures shared by the dashboard and Member 5 notebook."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.data import HOUSING_METRICS, TRANSPORT_METRICS, QUARTILES

COLORS = {"BRONX": "#165f73", "BROOKLYN": "#df7653", "MANHATTAN": "#7560a3",
          "QUEENS": "#4c8b69", "STATEN ISLAND": "#ad812d"}
TEAL = "#187a73"
ORANGE = "#df7653"


def style(figure, height=380):
    figure.update_layout(
        template="plotly_white", height=height,
        font={"family": "Segoe UI, Arial, sans-serif", "color": "#253847", "size": 12},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 60, "r": 30, "t": 55, "b": 65},
        legend={"orientation": "h", "y": -0.22, "x": 0},
        hoverlabel={"bgcolor": "white"},
    )
    figure.update_xaxes(gridcolor="#e8ecec", zeroline=False)
    figure.update_yaxes(gridcolor="#e8ecec", zeroline=False)
    return figure


def empty_figure(message):
    figure = go.Figure()
    figure.add_annotation(text=message, x=.5, y=.5, xref="paper", yref="paper", showarrow=False,
                          font={"size": 14}, align="center")
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return style(figure, 300)


def scatter_figure(report):
    h, t = report.selection.housing_metric, report.selection.transport_metric
    rows = report.rows.dropna(subset=[h, t])
    if rows.empty:
        return empty_figure("No paired housing / transportation measures in this selection.")
    figure = px.scatter(
        rows, x=h, y=t, color="borough", color_discrete_map=COLORS,
        hover_data={"zip_code": True, "year": True, "has_crash_data": True,
                    "approximate_zip_filings": True},
        labels={h: HOUSING_METRICS[h], t: TRANSPORT_METRICS[t], "borough": "Borough"},
    )
    figure.update_traces(marker={"size": 8, "opacity": .65, "line": {"width": .5, "color": "white"}})
    figure.update_layout(title={"text": "Each point is one ZIP code in one year", "font": {"size": 14}})
    return style(figure, 430)


def concentration_figure(report):
    if not report.coverage["known_housing_rows"]:
        return empty_figure("Housing coverage is unknown; activity groups cannot be assigned.")
    summary = report.concentration
    label = TRANSPORT_METRICS[report.selection.transport_metric]
    figure = go.Figure()
    figure.add_bar(x=list(QUARTILES), y=summary["record_share"] * 100,
                   name="Share of selected ZIP-years", marker_color="#b7c8ca")
    figure.add_bar(x=list(QUARTILES), y=summary["event_share"] * 100,
                   name=f"Share of {label.lower()}", marker_color=TEAL)
    figure.update_layout(barmode="group", title={"text": "RQ1 / Where are the events concentrated?", "font": {"size": 14}})
    figure.update_xaxes(title_text=f"Annual NYC {HOUSING_METRICS[report.selection.housing_metric].lower()} groups")
    figure.update_yaxes(title_text="Share of the known-housing selection (%)", range=[0, 105])
    if summary["event_share"].isna().all():
        figure.add_annotation(text="No selected events: event shares are undefined.", x=.5, y=1.1,
                              xref="paper", yref="paper", showarrow=False)
    return style(figure, 410)


def trend_figure(report):
    h, t = report.selection.housing_metric, report.selection.transport_metric
    annual = report.rows.groupby("year")[[h, t]].sum(min_count=1).reindex(sorted(report.selection.years))
    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.18,
                           subplot_titles=(HOUSING_METRICS[h], TRANSPORT_METRICS[t]))
    for row, metric, color in [(1, h, TEAL), (2, t, ORANGE)]:
        figure.add_trace(go.Scatter(x=annual.index, y=annual[metric], mode="lines+markers",
                                   line={"color": color, "width": 3},
                                   name=HOUSING_METRICS.get(metric, TRANSPORT_METRICS.get(metric))),
                         row=row, col=1)
        figure.update_yaxes(title_text="Count", row=row, col=1, rangemode="tozero")
    figure.update_xaxes(tickvals=sorted(report.selection.years), title_text="Year", row=2, col=1)
    figure.update_layout(showlegend=False, hovermode="x unified")
    return style(figure, 440)


def recurrence_figure(report):
    if report.recurrence.empty:
        return empty_figure("No housing-covered ZIPs for the recurring-activity comparison.")
    chosen = report.recurrence.head(20)
    years = sorted(report.selection.years)
    rows = report.rows[report.rows["zip_code"].isin(chosen["zip_code"])]
    matrix = rows.pivot(index="zip_code", columns="year", values="joint_high")
    matrix = matrix.reindex(index=chosen["zip_code"], columns=years).astype("Float64")
    z = [[None if pd.isna(value) else float(value) for value in row] for row in matrix.to_numpy()]
    statuses = [["Unknown / no row" if value is None else "Both high" if value else "Not both high"
                 for value in row] for row in z]
    figure = go.Figure(go.Heatmap(
        z=z, x=[str(y) for y in years], y=chosen["zip_code"].tolist(),
        zmin=0, zmax=1, colorscale=[[0, "#e5edeb"], [.499, "#e5edeb"], [.5, TEAL], [1, TEAL]],
        customdata=statuses, xgap=5, ygap=4,
        hovertemplate="ZIP %{y}<br>Year %{x}<br>%{customdata}<extra></extra>",
        colorbar={"tickvals": [0, 1], "ticktext": ["Not both high", "Both high"], "len": .6},
    ))
    figure.update_layout(title={"text": "RQ2 / Recurring high activity (up to 20 ZIPs)", "font": {"size": 14}})
    figure.update_xaxes(type="category", title_text="Selected year")
    figure.update_yaxes(type="category", autorange="reversed", title_text="ZIP code", tickmode="array",
                       tickvals=chosen["zip_code"].tolist())
    return style(figure, max(330, 100 + len(chosen) * 24))


def map_figure(report):
    h, t = report.selection.housing_metric, report.selection.transport_metric
    mapped = report.rows[report.rows["zip_latitude"].notna()]
    if mapped.empty:
        return empty_figure("No source coordinates for this selection. Records remain in other charts.")
    grouped = mapped.groupby(["zip_code", "borough"]).agg(
        latitude=("zip_latitude", "first"), longitude=("zip_longitude", "first"),
        housing=(h, lambda s: s.sum(min_count=1)), transport=(t, lambda s: s.sum(min_count=1)),
    ).reset_index()
    maximum = grouped["transport"].max()
    sizes = 7 + 22 * np.sqrt(grouped["transport"] / maximum) if maximum > 0 else pd.Series(7, index=grouped.index)
    figure = go.Figure()
    for known in [True, False]:
        mask = grouped["housing"].notna() if known else grouped["housing"].isna()
        group = grouped[mask]
        if group.empty:
            continue
        marker = {"size": sizes[mask], "opacity": .8}
        if known:
            marker.update(color=group["housing"], colorscale=[[0, "#9cd7cf"], [1, "#145e59"]],
                          showscale=True, colorbar={"title": "Housing<br>count", "thickness": 12})
        else:
            marker["color"] = "#89949d"
        custom = [[row.zip_code, row.borough.title(),
                   "Unknown" if pd.isna(row.housing) else f"{row.housing:,.0f}", f"{row.transport:,.0f}"]
                  for row in group.itertuples()]
        figure.add_trace(go.Scattermap(
            lat=group["latitude"], lon=group["longitude"], mode="markers", marker=marker,
            customdata=custom, name="Housing known" if known else "Housing unknown",
            hovertemplate="ZIP %{customdata[0]} / %{customdata[1]}<br>"
                          + HOUSING_METRICS[h] + ": %{customdata[2]}<br>"
                          + TRANSPORT_METRICS[t] + ": %{customdata[3]}<extra></extra>",
        ))
    figure.update_layout(map={"style": "carto-positron", "center": {"lat": 40.71, "lon": -73.94}, "zoom": 9},
                         showlegend=False)
    style(figure, 440)
    figure.update_layout(margin={"l": 0, "r": 0, "t": 8, "b": 0})
    return figure


def report_figures(report):
    return {
        "relationship": scatter_figure(report), "concentration": concentration_figure(report),
        "trend": trend_figure(report), "recurrence": recurrence_figure(report),
        "map": map_figure(report),
    }
