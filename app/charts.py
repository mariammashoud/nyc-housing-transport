"""Interactive figures for the team's ten research questions and dashboard context."""
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


def building_profile_figure(report):
    rows = report.building_profiles
    if rows.empty:
        return empty_figure("No paired building profiles and positive serious-crash counts in this selection.")
    summary = report.profile_summary
    figure = go.Figure(go.Box(
        x=rows["building_profile_group"], y=rows["injuries_per_crash"],
        name="ZIP-year distribution", boxpoints="all", jitter=.35, pointpos=0,
        marker={"color": TEAL, "opacity": .4, "size": 4}, line={"color": TEAL},
        customdata=rows[["zip_code", "year", "avg_proposed_stories",
                         "severe_injuries_total", "crash_count"]].to_numpy(),
        hovertemplate="ZIP %{customdata[0]} / %{customdata[1]}<br>"
                      "Reported mean proposed stories: %{customdata[2]:.2f}<br>"
                      "People seriously injured: %{customdata[3]:,.0f}<br>"
                      "Recorded serious crashes: %{customdata[4]:,.0f}<br>"
                      "Injuries per crash: %{y:.2f}<extra></extra>",
    ))
    figure.add_scatter(
        x=list(QUARTILES), y=summary["pooled_injuries_per_crash"], mode="markers",
        name="Pooled injury/crash ratio", marker={"color": ORANGE, "symbol": "diamond", "size": 11},
        customdata=summary[["zip_years", "severe_injuries", "recorded_crashes"]].to_numpy(),
        hovertemplate="%{x}<br>ZIP-years: %{customdata[0]:,.0f}<br>"
                      "People seriously injured: %{customdata[1]:,.0f}<br>"
                      "Recorded serious crashes: %{customdata[2]:,.0f}<br>Pooled ratio: %{y:.2f}<extra></extra>",
    )
    tick_labels = [
        label.replace(" / ", "<br>") + (
            "<br>no paired rows" if pd.isna(summary.loc[label, "zip_years"])
            else f"<br>n={int(summary.loc[label, 'zip_years'])}"
        )
        for label in QUARTILES
    ]
    figure.update_xaxes(type="category", categoryorder="array", categoryarray=list(QUARTILES),
                       tickmode="array", tickvals=list(QUARTILES), ticktext=tick_labels,
                       title_text="Annual NYC reported proposed-story profile")
    figure.update_yaxes(title_text="Seriously injured people / serious crash", rangemode="tozero")
    style(figure, 470)
    figure.update_layout(margin={"b": 110}, legend={"y": -.3})
    return figure


def fatal_share_figure(report):
    summary = report.fatal_share
    if summary["fatal_crash_share"].notna().sum() == 0:
        return empty_figure("No recorded crashes with known fatal-crash status in housing-covered ZIPs.")
    figure = go.Figure(go.Bar(
        x=list(QUARTILES), y=summary["fatal_crash_share"] * 100, marker_color=ORANGE,
        customdata=summary[["fatal_crash_count", "crash_count"]].to_numpy(),
        hovertemplate="%{x}<br>Fatal crashes: %{customdata[0]:,.0f}<br>"
                      "Recorded serious crashes: %{customdata[1]:,.0f}<br>"
                      "Fatal-crash share: %{y:.1f}%<extra></extra>",
    ))
    figure.update_xaxes(title_text=f"Annual NYC {HOUSING_METRICS[report.selection.housing_metric].lower()} groups")
    figure.update_yaxes(title_text="Fatal crashes / recorded serious crashes (%)", rangemode="tozero")
    return style(figure, 430)


def nighttime_figure(report):
    rows = report.rows[report.rows["has_housing_data"]]
    summary = rows.groupby(["borough", "housing_quartile"])[
        ["night_crash_count", "crashes_with_known_time"]
    ].sum(min_count=1)
    share = summary["night_crash_count"].div(summary["crashes_with_known_time"].replace(0, np.nan))
    if share.notna().sum() == 0:
        return empty_figure("No known-time crashes to calculate nighttime shares in this selection.")
    matrix = share.unstack().reindex(index=report.selection.boroughs, columns=QUARTILES) * 100
    figure = go.Figure(go.Heatmap(
        x=list(QUARTILES), y=[b.title() for b in matrix.index], z=matrix.to_numpy(),
        colorscale="Blues", zmin=0, zmax=100, colorbar={"title": "Nighttime<br>share (%)"},
        hovertemplate="%{y}<br>%{x}<br>Nighttime share: %{z:.1f}%<extra></extra>",
    ))
    figure.update_xaxes(title_text=f"Annual NYC {HOUSING_METRICS[report.selection.housing_metric].lower()} groups")
    figure.update_yaxes(title_text="Borough")
    return style(figure, 410)


def changes_figure(report):
    years = sorted(report.selection.years)
    if len(years) < 2:
        return empty_figure("Select at least two years to compare endpoint changes.")
    h, t = report.selection.housing_metric, report.selection.transport_metric
    rows = report.rows[report.rows["has_housing_data"] & report.rows["zip_code"].isin(report.crash_covered_zips)]
    first = rows[rows["year"].eq(years[0])][["zip_code", "borough", h, t]]
    last = rows[rows["year"].eq(years[-1])][["zip_code", h, t]]
    paired = first.merge(last, on="zip_code", suffixes=("_first", "_last"), validate="one_to_one")
    if paired.empty:
        return empty_figure("No crash-covered ZIPs with known housing at both selected endpoints.")
    paired["housing_change"] = paired[f"{h}_last"] - paired[f"{h}_first"]
    paired["transport_change"] = paired[f"{t}_last"] - paired[f"{t}_first"]
    figure = px.scatter(
        paired, x="housing_change", y="transport_change", color="borough",
        color_discrete_map=COLORS, hover_data=["zip_code"],
        labels={"housing_change": f"Change in {HOUSING_METRICS[h].lower()}",
                "transport_change": f"Change in {TRANSPORT_METRICS[t].lower()}", "borough": "Borough"},
    )
    figure.add_hline(y=0, line_color="#89949d")
    figure.add_vline(x=0, line_color="#89949d")
    figure.update_layout(title={"text": f"{len(paired)} ZIPs / {years[-1]} minus {years[0]}", "font": {"size": 14}})
    return style(figure, 430)


def lagged_figure(report):
    h, t = report.selection.housing_metric, report.selection.transport_metric
    current = report.rows[
        report.rows["has_housing_data"] & report.rows["zip_code"].isin(report.crash_covered_zips)
    ][["zip_code", "year", h]].copy()
    following = report.rows[["zip_code", "year", t]].rename(columns={t: "next_transport"})
    following["year"] = following["year"] - 1
    paired = current.merge(following, on=["zip_code", "year"], validate="one_to_one")
    if paired.empty:
        return empty_figure("Select consecutive years with housing coverage for a one-year-lag comparison.")
    figure = make_subplots(rows=2, cols=1, vertical_spacing=.22,
                           subplot_titles=("Pooled ZIP-years", "Within-ZIP deviations from own mean"))
    for row, x, y in [
        (1, paired[h], paired["next_transport"]),
        (2, paired[h] - paired.groupby("zip_code")[h].transform("mean"),
         paired["next_transport"] - paired.groupby("zip_code")["next_transport"].transform("mean")),
    ]:
        figure.add_trace(go.Scatter(
            x=x, y=y, mode="markers", marker={"color": TEAL, "opacity": .6, "size": 7},
            customdata=paired[["zip_code", "year"]].to_numpy(),
            hovertemplate="ZIP %{customdata[0]}<br>Filing year %{customdata[1]}<br>x: %{x}<br>y: %{y}<extra></extra>",
        ), row=row, col=1)
        prefix = "" if row == 1 else "Deviation: "
        figure.update_xaxes(title_text=prefix + HOUSING_METRICS[h], row=row, col=1)
        figure.update_yaxes(title_text=prefix + "next-year " + TRANSPORT_METRICS[t].lower(), row=row, col=1)
    figure.update_layout(showlegend=False)
    return style(figure, 680)


def development_mix_figure(report):
    summary = report.development_mix
    if summary["new_building_share"].notna().sum() == 0:
        return empty_figure("No positive filing totals in housing-covered ZIPs to compare development mix.")
    figure = go.Figure()
    for share, count, label, color in [
        ("new_building_share", "new_construction_filings", "New-building filings", TEAL),
        ("other_filing_share", "other_filings", "Other application filings", "#b7c8ca"),
    ]:
        figure.add_bar(
            x=summary.index, y=summary[share] * 100, name=label, marker_color=color,
            customdata=summary[[count, "filing_count"]].to_numpy(),
            hovertemplate="%{x}<br>%{fullData.name}: %{customdata[0]:,.0f}<br>"
                          "All filings: %{customdata[1]:,.0f}<br>Share: %{y:.1f}%<extra></extra>",
        )
    figure.update_layout(barmode="stack")
    figure.update_xaxes(title_text="Annual NYC serious-crash volume group")
    figure.update_yaxes(title_text="Share of application filings (%)", range=[0, 100])
    return style(figure, 430)


def unit_reporting_figure(report):
    summary = report.unit_reporting
    if summary["missing_unit_share"].notna().sum() == 0:
        return empty_figure("No first-observed jobs with known reporting counts in this selection.")
    years = sorted(report.selection.years)
    matrix = summary["missing_unit_share"].unstack().reindex(
        index=report.selection.boroughs, columns=years,
    ) * 100
    missing = summary["jobs_missing_units"].unstack().reindex(index=matrix.index, columns=years)
    total = summary["unique_job_count"].unstack().reindex(index=matrix.index, columns=years)
    figure = go.Figure(go.Heatmap(
        x=[str(y) for y in years], y=[b.title() for b in matrix.index], z=matrix.to_numpy(),
        customdata=np.stack([missing.to_numpy(), total.to_numpy()], axis=-1),
        colorscale="Oranges", zmin=0, zmax=100, colorbar={"title": "Incomplete<br>unit pairs (%)"},
        hovertemplate="%{y}<br>Cohort year %{x}<br>Jobs missing a complete unit pair: %{customdata[0]:,.0f}<br>"
                      "First-observed jobs: %{customdata[1]:,.0f}<br>Incomplete share: %{z:.1f}%<extra></extra>",
    ))
    figure.update_xaxes(type="category", title_text="First-observed job year")
    figure.update_yaxes(title_text="Borough")
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
    figure.update_layout(barmode="group", title={"text": "Where are the events concentrated?", "font": {"size": 14}})
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
    figure.update_layout(title={"text": "Recurring high activity (up to 20 ZIPs)", "font": {"size": 14}})
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
        "building-profile": building_profile_figure(report), "fatal-share": fatal_share_figure(report),
        "nighttime": nighttime_figure(report), "changes": changes_figure(report),
        "lagged": lagged_figure(report), "development-mix": development_mix_figure(report),
        "unit-reporting": unit_reporting_figure(report),
        "relationship": scatter_figure(report), "concentration": concentration_figure(report),
        "trend": trend_figure(report), "recurrence": recurrence_figure(report),
        "map": map_figure(report),
    }
