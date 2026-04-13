"""GIX Purchase Request Helper — Streamlit companion to the GIX tooling suite.

This module implements the purchase request workflow UI. Project layout:
``wayfinder_app.py`` is the primary campus resource wayfinder; optional CSV or
other inputs may live under ``data/``. Requires Python 3.12+.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Plotly bar colors (project visualization standard).
CHART_COLOR_PALETTE: list[str] = ["#1f77b4", "#ff7f0e", "#2ca02c"]

REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
    ("team_number", "Team Number"),
    ("cfo_name", "CFO Name"),
    ("provider", "Provider/Supplier"),
    ("quantity", "Quantity"),
    ("item_name", "Item Name"),
    ("price", "Price"),
    ("purchase_link", "Purchase Link"),
    ("instructor_approval", "Instructor Approval"),
)

_APP_STYLES_CSS = """
    <style>
    .block-container { padding-top: 1.25rem; padding-bottom: 2rem; max-width: 920px; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border: 1px solid #e5e9ef !important;
        border-radius: 16px !important;
        padding: 1.25rem 1.5rem 1.5rem !important;
        box-shadow:
            0 4px 6px -1px rgba(15, 23, 42, 0.06),
            0 12px 28px -6px rgba(15, 23, 42, 0.1);
    }
    [data-testid="stVerticalBlockBorderWrapper"] label p { font-weight: 500; }
    button[data-testid="baseButton-primary"] {
        background-color: #28a745 !important;
        border-color: #1e7e34 !important;
        color: #ffffff !important;
    }
    button[data-testid="baseButton-primary"]:hover {
        background-color: #218838 !important;
        border-color: #1c7430 !important;
        color: #ffffff !important;
    }
    .app-hero {
        background: linear-gradient(135deg, #071a33 0%, #0c2340 40%, #153a5f 100%);
        color: #ffffff;
        padding: 2.35rem 1.85rem;
        border-radius: 16px;
        margin-bottom: 1.75rem;
        box-shadow: 0 10px 40px rgba(7, 26, 51, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .app-hero h1 {
        color: #ffffff !important;
        margin: 0 !important;
        font-size: clamp(1.45rem, 4vw, 2rem) !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        line-height: 1.2 !important;
    }
    .app-hero .hero-subtitle {
        color: rgba(255, 255, 255, 0.92) !important;
        margin: 0.85rem 0 0 0 !important;
        font-size: 1.05rem !important;
        line-height: 1.6 !important;
        font-weight: 400 !important;
    }
    </style>
"""

st.set_page_config(
    page_title="GIX Purchase Request Helper",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_app_styles() -> None:
    """Inject custom CSS for layout, hero, form card, and primary button."""
    st.markdown(_APP_STYLES_CSS, unsafe_allow_html=True)


def mean_median_stdev(values: Sequence[float | int]) -> dict[str, float]:
    """Compute mean, median, and sample standard deviation.

    Args:
        values: Sequence of numeric values (at least one).

    Returns:
        Dictionary with keys ``mean``, ``median``, and ``stdev``.
        For a single value, ``stdev`` is ``0.0`` (no spread).

    Raises:
        ValueError: If ``values`` is empty.
    """
    if not values:
        raise ValueError("values must contain at least one number.")
    data = [float(x) for x in values]
    mean_v = statistics.fmean(data)
    median_v = statistics.median(data)
    stdev_v = 0.0 if len(data) < 2 else statistics.stdev(data)
    return {"mean": mean_v, "median": median_v, "stdev": stdev_v}


def _is_blank(value: str | None) -> bool:
    """Return True if value is None or only whitespace.

    Args:
        value: Raw string from a widget or payload.

    Returns:
        True when the value should be treated as missing.
    """
    return value is None or not str(value).strip()


def _parse_quantity(raw: str) -> tuple[int | None, str | None]:
    """Parse quantity as a positive integer.

    Args:
        raw: User-entered quantity string.

    Returns:
        Parsed integer and error message; one of the tuple entries is None.
    """
    s = raw.strip()
    if _is_blank(s):
        return None, "Quantity is required."
    try:
        q = int(s)
    except ValueError:
        return None, "Quantity must be a whole number."
    if q < 1:
        return None, "Quantity must be at least 1."
    return q, None


def _parse_price(raw: str) -> tuple[float | None, str | None]:
    """Parse price as a positive float (USD).

    Args:
        raw: User-entered price, may include $ or commas.

    Returns:
        Rounded price and error message; one entry is None.
    """
    s = raw.strip().replace("$", "").replace(",", "")
    if _is_blank(s):
        return None, "Price is required."
    try:
        p = float(s)
    except ValueError:
        return None, "Price must be a valid number (e.g. 19.99)."
    if p <= 0:
        return None, "Price must be greater than zero."
    return round(p, 2), None


def _validate_url(raw: str) -> tuple[str | None, str | None]:
    """Validate an http(s) purchase URL.

    Args:
        raw: User-entered URL string.

    Returns:
        Normalized URL or None, and optional error message.
    """
    s = raw.strip()
    if _is_blank(s):
        return None, "Purchase Link is required."
    parsed = urlparse(s)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None, "Purchase Link should be a full URL starting with http:// or https://."
    return s, None


def validate_submission(data: dict[str, Any]) -> list[str]:
    """Validate a purchase request payload.

    Args:
        data: Field keys mapped to raw string values from the form.

    Returns:
        Human-readable issues; empty list when the payload is valid.
    """
    issues: list[str] = []
    for key, label in REQUIRED_FIELDS:
        if key in ("quantity", "price", "purchase_link"):
            continue
        if _is_blank(str(data.get(key, "") or "")):
            issues.append(f"{label} is missing.")
    q, q_err = _parse_quantity(str(data.get("quantity", "")))
    if q_err:
        issues.append(q_err)
    p, p_err = _parse_price(str(data.get("price", "")))
    if p_err:
        issues.append(p_err)
    _, u_err = _validate_url(str(data.get("purchase_link", "")))
    if u_err:
        issues.append(u_err)
    return issues


def format_currency(amount: float) -> str:
    """Format a number as USD currency.

    Args:
        amount: Numeric dollar amount.

    Returns:
        String like ``$1,234.56``.
    """
    return f"${amount:,.2f}"


@st.cache_data
def prepare_supplier_bar_data(
    sorted_pairs: tuple[tuple[str, int], ...],
) -> tuple[list[str], list[int], list[str]]:
    """Prepare bar chart series from sorted (supplier, count) pairs.

    Args:
        sorted_pairs: Suppliers sorted by count descending by the caller.

    Returns:
        Parallel lists: supplier names, counts, and bar colors.
    """
    palette = tuple(CHART_COLOR_PALETTE)
    suppliers = [p[0] for p in sorted_pairs]
    counts_ = [p[1] for p in sorted_pairs]
    bar_colors = [palette[i % len(palette)] for i in range(len(suppliers))]
    return suppliers, counts_, bar_colors


def _apply_supplier_chart_layout(fig: go.Figure) -> None:
    """Apply shared layout for the supplier requests bar chart.

    Args:
        fig: Plotly figure to mutate in place.
    """
    fig.update_layout(
        template="plotly_white",
        title=dict(text="Requests by Supplier", font=dict(size=18)),
        xaxis_title="Supplier names",
        yaxis_title="Number of Requests",
        showlegend=False,
        margin=dict(t=56, b=56, l=56, r=32),
        plot_bgcolor="#fafafa",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#e8e8e8", zeroline=False),
    )


def build_supplier_requests_figure(
    suppliers: list[str], counts_: list[int], bar_colors: list[str]
) -> go.Figure:
    """Build a Plotly bar chart of request counts per supplier.

    Args:
        suppliers: Supplier labels (x-axis).
        counts_: Request counts (y-axis).
        bar_colors: Per-bar fill colors from ``CHART_COLOR_PALETTE``.

    Returns:
        Configured Plotly figure.
    """
    fig = go.Figure(
        data=[
            go.Bar(
                x=suppliers,
                y=counts_,
                marker_color=bar_colors,
                hovertemplate="<b>%{x}</b><br>Requests: %{y:d}<extra></extra>",
            )
        ]
    )
    _apply_supplier_chart_layout(fig)
    return fig


def required_fields_completion_ratio() -> float:
    """Fraction of required widgets (excluding Notes) that are non-blank.

    Returns:
        Value between 0.0 and 1.0 for the progress indicator.
    """
    keys = (
        "pf_team",
        "pf_cfo",
        "pf_provider",
        "pf_qty",
        "pf_item",
        "pf_price",
        "pf_link",
        "pf_instr",
    )
    filled = sum(1 for k in keys if not _is_blank(st.session_state.get(k)))
    return filled / len(keys)


def init_session_state() -> None:
    """Initialize session keys used by the purchase workflow."""
    if "last_submission" not in st.session_state:
        st.session_state.last_submission = None
    if "supplier_request_counts" not in st.session_state:
        st.session_state.supplier_request_counts = {}
    if "purchase_request_history" not in st.session_state:
        st.session_state.purchase_request_history = []


def render_sidebar_guidelines() -> None:
    """Render submission tips in the sidebar."""
    with st.sidebar:
        st.subheader("Submission Guidelines")
        st.markdown(
            """
- Fill in **every required field** (everything except Notes): team number, CFO full name, supplier, quantity, item, price, purchase URL, and instructor approval.
- Use a **full product link** (`https://…`) to the exact item and a **valid USD price** (for example `24.50`).
- In **Instructor Approval**, state **who** approved and **how** (email, Canvas, or in person) so the coordinator can verify your request.
            """
        )


def render_hero_banner() -> None:
    """Render the top hero with title and subtitle."""
    st.markdown(
        """
    <div class="app-hero">
        <h1>GIX Purchase Request Helper</h1>
        <p class="hero-subtitle">Complete every field so your request is ready on the first try—less back-and-forth with the Program Coordinator.</p>
    </div>
        """,
        unsafe_allow_html=True,
    )


def render_submission_metrics(history: list[dict[str, Any]]) -> None:
    """Show aggregate metrics when there is history.

    Args:
        history: List of stored purchase rows.
    """
    if not history:
        return
    total_value = sum(row["price"] for row in history)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total submissions", len(history))
    m2.metric("Unique suppliers", len(st.session_state.supplier_request_counts))
    m3.metric("Sum of line prices", format_currency(total_value))


def render_supplier_chart(counts: dict[str, int]) -> None:
    """Render the Plotly supplier bar chart or an info placeholder.

    Args:
        counts: Running totals per supplier name.
    """
    st.subheader("Requests by Supplier")
    if not counts:
        st.info("No data to display yet.")
        return
    try:
        sorted_pairs = tuple(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower())))
        suppliers, n_requests, bar_colors = prepare_supplier_bar_data(sorted_pairs)
        fig = build_supplier_requests_figure(suppliers, n_requests, bar_colors)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
        )
    except Exception as exc:
        st.error("Unable to render the supplier chart. Please refresh and try again.")
        st.caption(str(exc))


def build_history_dataframe(history: list[dict[str, Any]]) -> tuple[pd.DataFrame, bytes]:
    """Build sorted display frame and UTF-8 CSV bytes from history rows.

    Args:
        history: Raw history dicts from session state.

    Returns:
        Sorted dataframe and encoded CSV for download.

    Raises:
        Exception: Propagated if pandas processing fails.
    """
    hist_df = pd.DataFrame(history)
    rename_map = {
        "team_number": "Team Number",
        "cfo_name": "CFO Name",
        "supplier": "Supplier",
        "item_name": "Item Name",
        "price": "Price",
        "submission_time": "Submission Time",
    }
    hist_df = hist_df.rename(columns=rename_map)
    cols = [
        "Team Number",
        "CFO Name",
        "Supplier",
        "Item Name",
        "Price",
        "Submission Time",
    ]
    hist_df = hist_df[cols].sort_values("Submission Time", ascending=False)
    csv_bytes = hist_df.to_csv(index=False).encode("utf-8")
    return hist_df, csv_bytes


def render_submission_log(history: list[dict[str, Any]]) -> None:
    """Render CSV download and dataframe for submission history.

    Args:
        history: List of dict rows with keys matching stored purchases.
    """
    st.subheader("Submission log")
    if not history:
        st.info("No submissions yet.")
        return
    try:
        hist_df, csv_bytes = build_history_dataframe(history)
    except Exception as exc:
        st.error("Could not prepare the submission table for display.")
        st.caption(str(exc))
        return

    st.download_button(
        label="Download purchase_requests.csv",
        data=csv_bytes,
        file_name="purchase_requests.csv",
        mime="text/csv",
        type="secondary",
        use_container_width=False,
    )
    st.dataframe(
        hist_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Price": st.column_config.NumberColumn("Price", format="$%.2f", width="small"),
            "Submission Time": st.column_config.DatetimeColumn(
                "Submission Time", format="YYYY-MM-DD HH:mm", width="medium"
            ),
        },
    )


def render_latest_submission_summary() -> None:
    """Show a readable summary of the most recent successful submission."""
    s = st.session_state.last_submission
    if not s:
        return
    st.divider()
    st.subheader("Latest submission")
    line_items = [
        ("Team Number", s["team_number"]),
        ("CFO Name", s["cfo_name"]),
        ("Provider/Supplier", s["provider"]),
        ("Quantity", str(s["quantity"])),
        ("Item Name", s["item_name"]),
        ("Price", format_currency(s["price"])),
        ("Purchase Link", s["purchase_link"]),
        ("Instructor Approval", s["instructor_approval"]),
        ("Notes", s["notes"] if s["notes"] else "—"),
    ]
    st.markdown("---")
    for label, value in line_items:
        st.markdown(f"**{label}**  \n{value}")
    st.markdown("---")


def _widget_row_team_cfo() -> tuple[str, str]:
    """Render team number and CFO inputs."""
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        team = st.text_input("🔢 Team Number", placeholder="e.g. 7", key="pf_team")
    with c2:
        cfo = st.text_input("👤 CFO Name", placeholder="Full name of team CFO", key="pf_cfo")
    return team, cfo


def _widget_row_provider_qty() -> tuple[str, str]:
    """Render provider and quantity inputs."""
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        prov = st.text_input("🏪 Provider/Supplier", placeholder="Vendor or store name", key="pf_provider")
    with c2:
        qty = st.text_input("📊 Quantity", placeholder="Whole number, e.g. 3", key="pf_qty")
    return prov, qty


def _widget_row_item_price() -> tuple[str, str]:
    """Render item name and price inputs."""
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        item = st.text_input("📦 Item Name", placeholder="What you are buying", key="pf_item")
    with c2:
        pr = st.text_input("💵 Price (USD)", placeholder="e.g. 24.50", key="pf_price")
    return item, pr


def _widget_link_notes_approval() -> tuple[str, str, str]:
    """Render link, notes, and instructor approval fields."""
    pl = st.text_input("🔗 Purchase Link", placeholder="https://…", key="pf_link")
    nt = st.text_area(
        "📝 Notes",
        placeholder="Optional: specs, shipping constraints, justification, etc.",
        height=96,
        key="pf_notes",
    )
    inst = st.text_input(
        "✅ Instructor Approval",
        placeholder="e.g. Approved by Dr. Lee via email on 4/5/26",
        help="Briefly state who approved and how (email, Canvas, in-person, etc.).",
        key="pf_instr",
    )
    return pl, nt, inst


def render_purchase_form_card() -> tuple[bool, dict[str, Any]]:
    """Draw the bordered form and return submit flag plus field payload.

    Returns:
        Tuple of (whether submit was clicked, payload dict for validation).
    """
    with st.container(border=True):
        team_number, cfo_name = _widget_row_team_cfo()
        provider, quantity = _widget_row_provider_qty()
        item_name, price = _widget_row_item_price()
        purchase_link, notes, instructor_approval = _widget_link_notes_approval()
        submitted = st.button("Submit purchase request", type="primary", use_container_width=True)
    payload: dict[str, Any] = {
        "team_number": team_number,
        "cfo_name": cfo_name,
        "provider": provider,
        "quantity": quantity,
        "item_name": item_name,
        "price": price,
        "purchase_link": purchase_link,
        "notes": notes,
        "instructor_approval": instructor_approval,
    }
    return submitted, payload


def _show_submission_validation_errors(issues: list[str], notes: str) -> None:
    """Display validation failures and clear last submission."""
    st.session_state.last_submission = None
    st.warning("Some required information is missing or invalid. Please fix the items below.")
    for msg in issues:
        st.markdown(f"- {msg}")
    if not _is_blank(notes):
        st.caption(
            "Notes were saved in the form — you do not need to re-type them after fixing other fields."
        )


def _trimmed_payload_fields(payload: dict[str, Any]) -> tuple[str, str, str, str]:
    """Return stripped team, CFO, item, and instructor strings."""
    team = str(payload.get("team_number", "")).strip()
    cfo = str(payload.get("cfo_name", "")).strip()
    item = str(payload.get("item_name", "")).strip()
    instr = str(payload.get("instructor_approval", "")).strip()
    return team, cfo, item, instr


def persist_successful_purchase(
    payload: dict[str, Any],
    notes: str,
    qty_int: int,
    price_f: float,
    link_ok: str,
    prov_key: str,
) -> None:
    """Write counts, history row, and last submission after validation passes."""
    team, cfo, item, instr = _trimmed_payload_fields(payload)
    st.session_state.supplier_request_counts[prov_key] = (
        st.session_state.supplier_request_counts.get(prov_key, 0) + 1
    )
    st.session_state.purchase_request_history.append(
        {
            "team_number": team,
            "cfo_name": cfo,
            "supplier": prov_key,
            "item_name": item,
            "price": price_f,
            "submission_time": datetime.now(),
        }
    )
    st.session_state.last_submission = {
        "team_number": team,
        "cfo_name": cfo,
        "provider": prov_key,
        "quantity": qty_int,
        "item_name": item,
        "price": price_f,
        "purchase_link": link_ok,
        "notes": notes.strip() if not _is_blank(notes) else None,
        "instructor_approval": instr,
    }
    st.success("Your purchase request has been submitted successfully!")


def handle_purchase_submission(payload: dict[str, Any]) -> None:
    """Validate payload and update session state or show field errors.

    Args:
        payload: Raw strings from purchase widgets.
    """
    issues = validate_submission(payload)
    notes = str(payload.get("notes", ""))
    if issues:
        _show_submission_validation_errors(issues, notes)
        return
    qty_int, _ = _parse_quantity(str(payload.get("quantity", "")))
    price_f, _ = _parse_price(str(payload.get("price", "")))
    link_ok, _ = _validate_url(str(payload.get("purchase_link", "")))
    prov_key = str(payload.get("provider", "")).strip()
    if qty_int is None or price_f is None or link_ok is None:
        st.error("Something went wrong while saving your request. Please try again.")
        return
    persist_successful_purchase(payload, notes, qty_int, price_f, link_ok, prov_key)


def main() -> None:
    """Drive the Streamlit purchase request UI."""
    inject_app_styles()
    render_sidebar_guidelines()
    render_hero_banner()
    init_session_state()
    st.subheader("Purchase request")
    st.caption("All fields are required except **Notes**.")
    completion = required_fields_completion_ratio()
    st.progress(completion, text=f"{int(round(completion * 100))}% complete")
    submitted, payload = render_purchase_form_card()
    if submitted:
        handle_purchase_submission(payload)
    st.divider()
    history: list[dict[str, Any]] = st.session_state.purchase_request_history
    render_submission_metrics(history)
    render_supplier_chart(st.session_state.supplier_request_counts)
    render_submission_log(history)
    render_latest_submission_summary()


if __name__ == "__main__":
    main()
