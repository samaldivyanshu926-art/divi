"""Interactive Plotly test-run dashboard.

Produces a single self-contained HTML file with linked time-history
subplots (thrust, EGT, corrected speed, fuel flow) and QA fail points
overlaid as markers — the kind of quick-look dashboard a test engineer
would open right after a run to decide whether the data is usable before
doing any deeper analysis.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..common.logging_config import get_logger

logger = get_logger(__name__)

_CHANNELS = [
    ("thrust_n", "Thrust [N]", "qa_thrust_n"),
    ("egt_k", "EGT [K]", "qa_egt_k"),
    ("rpm_percent_corrected", "Corrected Speed [% N1c]", "qa_rpm"),
    ("fuel_flow_corrected_kg_s", "Corrected Fuel Flow [kg/s]", None),
]


def build_dashboard(df: pd.DataFrame, output_path: Path, title: str = "JetX Test-Bed Run Dashboard") -> Path:
    """Build and save an interactive multi-panel HTML dashboard.

    Any row where ``qa_pass`` is False is marked with a red "x" on every
    panel at that timestamp, so a QA issue on one channel is visible in
    context of what every other channel was doing at the same instant.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig = make_subplots(
        rows=len(_CHANNELS),
        cols=1,
        shared_xaxes=True,
        subplot_titles=[label for _, label, _ in _CHANNELS],
        vertical_spacing=0.06,
    )

    qa_fail_mask = ~df["qa_pass"] if "qa_pass" in df.columns else pd.Series(False, index=df.index)

    for row_index, (column, label, _qa_prefix) in enumerate(_CHANNELS, start=1):
        fig.add_trace(
            go.Scatter(x=df["time_s"], y=df[column], mode="lines", name=label, line=dict(width=1.5)),
            row=row_index,
            col=1,
        )
        if qa_fail_mask.any():
            fig.add_trace(
                go.Scatter(
                    x=df.loc[qa_fail_mask, "time_s"],
                    y=df.loc[qa_fail_mask, column],
                    mode="markers",
                    marker=dict(color="red", symbol="x", size=7),
                    name="QA flag" if row_index == 1 else None,
                    showlegend=(row_index == 1),
                ),
                row=row_index,
                col=1,
            )
        fig.update_yaxes(title_text=label, row=row_index, col=1)

    fig.update_xaxes(title_text="Time [s]", row=len(_CHANNELS), col=1)
    fig.update_layout(
        title=title,
        height=220 * len(_CHANNELS),
        showlegend=True,
        template="plotly_white",
    )

    fig.write_html(str(output_path), include_plotlyjs="cdn")
    logger.info("Wrote interactive dashboard to %s", output_path)
    return output_path
