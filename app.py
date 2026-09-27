import streamlit as st
import pandas as pd

from utils.ai_extractor import extract_invoice_details
from utils.pricing import find_service_price, get_pricing_source
from utils.invoice import generate_invoice_pdf
from utils.database import (
    init_database,
    get_next_invoice_number,
    save_invoice,
    get_all_invoices,
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="InvoiceGen AI",
    page_icon="🧾",
    layout="wide"
)

# Create the SQLite database/tables if they do not exist.
init_database()


# ==================================================
# APPLICATION HEADER
# ==================================================

st.title("🧾 InvoiceGen AI")
st.write(
    "Turn a customer's natural-language request "
    "into a professional invoice using AI."
)


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

st.sidebar.title("📌 Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Dashboard",
        "🧾 New Invoice",
        "📋 Invoice History"
    ]
)

st.sidebar.divider()

st.sidebar.caption("💡 AI extracts the request.")
st.sidebar.caption("📊 Prices come only from the CSV database.")
st.sidebar.caption("👤 Human approval is required.")


# ==================================================
# DASHBOARD
# ==================================================

if page == "🏠 Dashboard":

    st.header("🏠 Dashboard")

    history = get_all_invoices()

    total_invoices = len(history)

    approved_invoices = sum(
        1 for invoice in history
        if invoice["status"] == "Approved"
    )

    pending_invoices = sum(
        1 for invoice in history
        if invoice["status"] == "Pending Review"
    )

    total_revenue = sum(
        invoice["total"]
        for invoice in history
        if invoice["status"] == "Approved"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📄 Total Invoices",
            total_invoices
        )

    with col2:
        st.metric(
            "✅ Approved",
            approved_invoices
        )

    with col3:
        st.metric(
            "⏳ Pending Review",
            pending_invoices
        )

    with col4:
        st.metric(
            "💰 Total Revenue",
            f"₹{total_revenue:,.2f}"
        )

    st.divider()

    st.subheader("📋 Recent Invoices")

    if history:

        recent_data = []

        for invoice in history:

            recent_data.append(
                {
                    "Invoice": invoice["invoice_number"],
                    "Customer": invoice["customer"],
                    "Amount": f"₹{invoice['total']:,.2f}",
                    "Status": invoice["status"],
                    "Created": invoice["created_at"]
                }
            )

        st.dataframe(
            pd.DataFrame(recent_data),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No invoices have been created yet."
        )

    st.divider()

    st.subheader("📊 Pricing Data Source")

    st.success(
        f"Prices are retrieved from: **{get_pricing_source()}**"
    )

    st.caption(
        "The AI does not generate or estimate missing prices."
    )


# ==================================================
# NEW INVOICE
# ==================================================

elif page == "🧾 New Invoice":

    st.header("🧾 Create New Invoice")

    st.write(
        "Enter the customer's requirement in natural language. "
        "Gemini AI will extract the invoice details."
    )

    # ==================================================
    # CUSTOMER REQUIREMENT
    # ==================================================

    st.subheader("📩 Customer Requirement")

    customer_message = st.text_area(
        "Enter the customer's request:",
        height=180,
        placeholder=(
            "Example: Hi, I'm Rahul from ABC Technologies. "
            "I need 3 website development packages and "
            "2 months of website maintenance. "
            "Please deliver within 15 days."
        )
    )

    # ==================================================
    # GENERATE INVOICE
    # ==================================================

    if st.button(
        "✨ Generate Invoice",
        type="primary"
    ):

        if not customer_message.strip():

            st.warning(
                "Please enter a customer message."
            )

        else:

            with st.spinner(
                "🤖 AI is extracting invoice details..."
            ):

                try:

                    result = extract_invoice_details(
                        customer_message
                    )

                    st.session_state["invoice_data"] = result
                    st.session_state["approved"] = False
                    st.session_state.pop("invoice_number", None)
                    st.session_state.pop("invoice_saved", None)

                    st.success(
                        "✅ Information extracted successfully!"
                    )

                except Exception as e:

                    st.error(
                        f"AI Error: {e}"
                    )

    # ==================================================
    # DISPLAY INVOICE REVIEW
    # ==================================================

    if "invoice_data" in st.session_state:

        result = st.session_state["invoice_data"]

        st.divider()

        st.header("📋 Invoice Review")

        st.caption(
            "Review and edit the AI-extracted information before approval."
        )

        # ==================================================
        # CUSTOMER DETAILS
        # ==================================================

        st.subheader("👤 Customer Details")

        col1, col2 = st.columns(2)

        with col1:

            customer_name = st.text_input(
                "Customer Name",
                value=result.get(
                    "customer_name",
                    ""
                )
            )

        with col2:

            email = st.text_input(
                "Email",
                value=result.get(
                    "email",
                    ""
                )
            )

        # ==================================================
        # INVOICE ITEMS
        # ==================================================

        st.subheader("🛒 Invoice Items")

        invoice_items = []

        all_prices_available = True

        for i, service in enumerate(
            result.get("services", [])
        ):

            original_service_name = service.get(
                "service_name",
                ""
            )

            quantity = int(
                service.get(
                    "quantity",
                    1
                )
            )

            col1, col2 = st.columns([4, 1])

            with col1:

                edited_service = st.text_input(
                    "Service",
                    value=original_service_name,
                    key=f"service_{i}"
                )

            with col2:

                edited_quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    value=quantity,
                    step=1,
                    key=f"quantity_{i}"
                )

            # --------------------------------------------------
            # PRICE LOOKUP
            # --------------------------------------------------

            price_result = find_service_price(
                edited_service
            )

            if price_result["found"]:

                unit_price = price_result["price"]

                matched_service = price_result["matched_service"]
                match_type = price_result["match_type"]
                source = price_result["source"]

                st.success(
                    f"✅ Verified Price: ₹{unit_price:,.2f}"
                )

                info_col1, info_col2, info_col3 = st.columns(3)

                with info_col1:
                    st.caption(
                        f"📊 Database Service: **{matched_service}**"
                    )

                with info_col2:
                    st.caption(
                        f"🔎 Match Type: **{match_type}**"
                    )

                with info_col3:
                    st.caption(
                        f"📁 Source: **{source}**"
                    )

            else:

                unit_price = 0.0

                all_prices_available = False

                st.error(
                    "⚠️ Price not found"
                )

                st.warning(
                    f"No verified price found for "
                    f"'{edited_service}'. "
                    "The system will NOT generate or estimate a price."
                )

                st.caption(
                    f"📁 Price Source: **{price_result['source']}**"
                )

            invoice_items.append(
                {
                    "service": edited_service,
                    "quantity": edited_quantity,
                    "unit_price": unit_price,
                    "price_found": price_result["found"],
                    "matched_service": price_result.get(
                        "matched_service"
                    ),
                    "match_type": price_result.get(
                        "match_type"
                    ),
                    "price_source": price_result.get(
                        "source"
                    )
                }
            )

        # ==================================================
        # NOTES
        # ==================================================

        st.subheader("📝 Notes")

        notes = st.text_area(
            "Invoice Notes",
            value=result.get(
                "notes",
                ""
            ),
            height=100
        )

        # ==================================================
        # CALCULATE TOTALS
        # ==================================================

        subtotal = 0.0

        for item in invoice_items:

            if item["price_found"]:

                subtotal += (
                    item["quantity"]
                    * item["unit_price"]
                )

        # ==================================================
        # GST RATE
        # ==================================================

        st.subheader("🧾 Tax Settings")

        gst_rate = st.number_input(
            "GST Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=18.0,
            step=1.0
        )

        gst_amount = (
            subtotal * gst_rate / 100
        )

        total = (
            subtotal + gst_amount
        )

        # ==================================================
        # INVOICE SUMMARY
        # ==================================================

        st.divider()

        st.subheader("💰 Invoice Summary")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Subtotal",
                f"₹{subtotal:,.2f}"
            )

        with col2:

            st.metric(
                f"GST ({gst_rate:g}%)",
                f"₹{gst_amount:,.2f}"
            )

        with col3:

            st.metric(
                "Total",
                f"₹{total:,.2f}"
            )

        # ==================================================
        # INVOICE PREVIEW
        # ==================================================

        st.divider()

        st.subheader("👀 Invoice Preview")

        st.markdown(
            f"""
            ### 🧾 INVOICEGEN AI

            **Customer:** {customer_name}

            **Email:** {email}

            ---
            """
        )

        preview_data = []

        for item in invoice_items:

            if item["price_found"]:

                amount = (
                    item["quantity"]
                    * item["unit_price"]
                )

                preview_data.append(
                    {
                        "Service": item["service"],
                        "Database Match": (
                            item["matched_service"]
                            or "-"
                        ),
                        "Match Type": (
                            item["match_type"]
                            or "-"
                        ),
                        "Quantity": item["quantity"],
                        "Unit Price": (
                            f"₹{item['unit_price']:,.2f}"
                        ),
                        "Amount": f"₹{amount:,.2f}"
                    }
                )

            else:

                preview_data.append(
                    {
                        "Service": item["service"],
                        "Database Match": "Not Found",
                        "Match Type": "Not Found",
                        "Quantity": item["quantity"],
                        "Unit Price": "Price Missing",
                        "Amount": "Review Required"
                    }
                )

        preview_df = pd.DataFrame(
            preview_data
        )

        st.dataframe(
            preview_df,
            use_container_width=True,
            hide_index=True
        )

        preview_col1, preview_col2 = st.columns(
            [3, 1]
        )

        with preview_col2:

            st.write(
                f"**Subtotal:** ₹{subtotal:,.2f}"
            )

            st.write(
                f"**GST ({gst_rate:g}%):** "
                f"₹{gst_amount:,.2f}"
            )

            st.markdown(
                f"### **Total: ₹{total:,.2f}**"
            )

        st.write(
            f"**Notes:** {notes}"
        )

        # ==================================================
        # APPROVAL SECTION
        # ==================================================

        st.divider()

        if not all_prices_available:

            st.warning(
                "⚠️ Invoice cannot be approved yet. "
                "Please resolve all missing prices."
            )

        else:

            st.success(
                "✅ All invoice items have verified prices."
            )

            if st.button(
                "✅ Approve Invoice",
                type="primary"
            ):

                try:

                    invoice_number = get_next_invoice_number()

                    save_invoice(
                        invoice_number=invoice_number,
                        customer=customer_name,
                        email=email,
                        invoice_items=invoice_items,
                        subtotal=subtotal,
                        gst_rate=gst_rate,
                        gst_amount=gst_amount,
                        total=total,
                        notes=notes,
                        status="Approved"
                    )

                    st.session_state["approved"] = True
                    st.session_state["invoice_number"] = invoice_number
                    st.session_state["invoice_saved"] = True

                    st.success(
                        f"🎉 Invoice {invoice_number} approved and saved!"
                    )

                except Exception as e:

                    st.error(
                        f"Could not save invoice: {e}"
                    )

        # ==================================================
        # APPROVED INVOICE
        # ==================================================

        if st.session_state.get(
            "approved",
            False
        ):

            st.divider()

            st.header("✅ Invoice Approved")

            invoice_number = st.session_state.get(
                "invoice_number",
                "INV"
            )

            st.write(
                f"**Invoice Number:** {invoice_number}"
            )

            st.write(
                f"**Customer:** {customer_name}"
            )

            st.write(
                f"**Email:** {email}"
            )

            st.write(
                f"**Total Amount:** ₹{total:,.2f}"
            )

            st.success(
                "The invoice has been approved, "
                "saved to invoice history, and is ready for export."
            )

            # ==================================================
            # GENERATE PDF
            # ==================================================

            try:

                pdf_data = generate_invoice_pdf(
                    customer_name=customer_name,
                    email=email,
                    invoice_items=invoice_items,
                    subtotal=subtotal,
                    gst_rate=gst_rate,
                    gst_amount=gst_amount,
                    total=total,
                    notes=notes,
                    invoice_number=invoice_number
                )

                st.download_button(
                    label="📄 Download Invoice PDF",
                    data=pdf_data,
                    file_name=f"{invoice_number}.pdf",
                    mime="application/pdf"
                )

            except Exception as e:

                st.error(
                    f"PDF generation error: {e}"
                )


# ==================================================
# INVOICE HISTORY
# ==================================================

elif page == "📋 Invoice History":

    st.header("📋 Invoice History")

    history = get_all_invoices()

    if not history:

        st.info(
            "No saved invoices yet."
        )

    else:

        for invoice in reversed(history):

            with st.expander(
                f"{invoice['invoice_number']} — "
                f"{invoice['customer']} — "
                f"₹{invoice['total']:,.2f}"
            ):

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(
                        f"**Customer:** {invoice['customer']}"
                    )
                    st.write(
                        f"**Email:** {invoice['email']}"
                    )

                with col2:
                    st.write(
                        f"**Status:** {invoice['status']}"
                    )
                    st.write(
                        f"**Created:** {invoice['created_at']}"
                    )

                with col3:
                    st.write(
                        f"**Subtotal:** "
                        f"₹{invoice['subtotal']:,.2f}"
                    )
                    st.write(
                        f"**GST ({invoice['gst_rate']:g}%):** "
                        f"₹{invoice['gst_amount']:,.2f}"
                    )
                    st.write(
                        f"**Total:** "
                        f"₹{invoice['total']:,.2f}"
                    )

                st.markdown("**Items:**")

                history_items = []

                for item in invoice["items"]:

                    history_items.append(
                        {
                            "Service": item["service"],
                            "Quantity": item["quantity"],
                            "Unit Price": (
                                f"₹{item['unit_price']:,.2f}"
                            ),
                            "Price Verified": (
                                "Yes"
                                if item["price_found"]
                                else "No"
                            )
                        }
                    )

                st.dataframe(
                    pd.DataFrame(history_items),
                    use_container_width=True,
                    hide_index=True
                )

                if invoice["notes"]:

                    st.write(
                        f"**Notes:** {invoice['notes']}"
                    )
