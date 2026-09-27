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


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="InvoiceAI",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATABASE
# =========================================================

init_database()


# =========================================================
# SESSION STATE
# =========================================================

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

if "approved" not in st.session_state:
    st.session_state.approved = False

if "invoice_number" not in st.session_state:
    st.session_state.invoice_number = None


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("🧾 InvoiceAI")

    st.caption("Smart AI-powered invoicing")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "➕ New Invoice",
            "🗂️ Invoice History",
        ],
    )

    st.divider()

    st.success("Pricing database connected")

    st.caption(
        "Prices are read from pricing.csv. "
        "AI never creates or estimates prices."
    )


# =========================================================
# DASHBOARD
# =========================================================

if page == "📊 Dashboard":

    invoices = get_all_invoices()

    total_invoices = len(invoices)

    approved_invoices = sum(
        1
        for invoice in invoices
        if invoice["status"] == "Approved"
    )

    total_revenue = sum(
        float(invoice["total"])
        for invoice in invoices
        if invoice["status"] == "Approved"
    )

    total_items = sum(
        len(invoice["items"])
        for invoice in invoices
    )

    st.title("📊 Dashboard")

    st.caption(
        "Overview of your AI-powered invoicing system."
    )

    st.divider()

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Invoices",
            total_invoices,
        )

    with col2:
        st.metric(
            "Approved",
            approved_invoices,
        )

    with col3:
        st.metric(
            "Revenue",
            f"₹{total_revenue:,.0f}",
        )

    with col4:
        st.metric(
            "Service Items",
            total_items,
        )

    st.divider()

    # -----------------------------------------------------
    # RECENT INVOICES + PRICING
    # -----------------------------------------------------

    left, right = st.columns([2, 1])

    with left:

        with st.container(border=True):

            st.subheader("🧾 Recent Invoices")

            st.caption(
                "Your latest approved invoices."
            )

            if invoices:

                rows = []

                for invoice in reversed(
                    invoices[-10:]
                ):

                    rows.append(
                        {
                            "Invoice":
                                invoice["invoice_number"],
                            "Customer":
                                invoice["customer"],
                            "Date":
                                invoice["created_at"],
                            "Status":
                                invoice["status"],
                            "Total":
                                f"₹{invoice['total']:,.2f}",
                        }
                    )

                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No invoices yet. "
                    "Create your first invoice "
                    "from the New Invoice page."
                )

    with right:

        with st.container(border=True):

            st.subheader("💰 Pricing Database")

            st.caption(
                "Current pricing source"
            )

            st.success("Connected")

            st.write(
                get_pricing_source()
            )

            st.caption(
                "Only verified prices are used."
            )

        with st.container(border=True):

            st.subheader("⚡ How It Works")

            st.write(
                "1. Customer sends a request"
            )

            st.write(
                "2. AI extracts the details"
            )

            st.write(
                "3. Services are matched"
            )

            st.write(
                "4. Prices are verified"
            )

            st.write(
                "5. Human approves"
            )

            st.write(
                "6. PDF invoice is generated"
            )


# =========================================================
# NEW INVOICE
# =========================================================

elif page == "➕ New Invoice":

    st.title("➕ Create New Invoice")

    st.caption(
        "Convert a natural-language customer request "
        "into a verified invoice."
    )

    st.divider()

    # =====================================================
    # AI REQUEST
    # =====================================================

    with st.container(border=True):

        st.subheader("✨ AI Invoice Assistant")

        st.caption(
            "Describe what the customer wants in normal "
            "language. AI will extract the customer, "
            "email, services, quantity and notes."
        )

        request_text = st.text_area(
            "Customer Requirement",
            placeholder=(
                "Example:\n\n"
                "Rahul from rahul@abc.com wants 3 website "
                "development packages and 2 website "
                "maintenance services. Delivery should "
                "be within 15 days."
            ),
            height=150,
        )

        if st.button(
            "✨ Extract Invoice Details",
            type="primary",
            use_container_width=True,
        ):

            if not request_text.strip():

                st.warning(
                    "Please enter a customer requirement."
                )

            else:

                with st.spinner(
                    "AI is extracting invoice details..."
                ):

                    try:

                        result = extract_invoice_details(
                            request_text
                        )

                        st.session_state.extracted_data = (
                            result
                        )

                        st.session_state.approved = False

                        st.session_state.invoice_number = (
                            None
                        )

                        st.success(
                            "AI extraction completed successfully."
                        )

                    except Exception as error:

                        st.error(
                            f"AI extraction failed: {error}"
                        )


    # =====================================================
    # SHOW EXTRACTED INFORMATION
    # =====================================================

    if st.session_state.extracted_data:

        data = st.session_state.extracted_data

        st.write("")

        # =================================================
        # CUSTOMER DETAILS
        # =================================================

        with st.container(border=True):

            st.subheader("👤 Customer Details")

            st.caption(
                "Review the information extracted by AI."
            )

            customer_col, email_col = st.columns(2)

            with customer_col:

                customer_name = st.text_input(
                    "Customer Name",
                    value=data.get(
                        "customer_name",
                        "",
                    ),
                )

            with email_col:

                email = st.text_input(
                    "Email",
                    value=data.get(
                        "email",
                        "",
                    ),
                )


        # =================================================
        # SERVICES
        # =================================================

        st.write("")

        with st.container(border=True):

            st.subheader(
                "🛒 Services & Price Verification"
            )

            st.caption(
                "Every service is checked against your "
                "pricing database. The system never "
                "fabricates missing prices."
            )

            services = data.get(
                "services",
                [],
            )

            invoice_items = []

            subtotal = 0.0

            all_prices_found = True

            if not services:

                st.warning(
                    "No services were extracted "
                    "from the customer request."
                )

            for index, item in enumerate(services):

                st.markdown(
                    f"### Service {index + 1}"
                )

                service_col, quantity_col = st.columns(
                    [4, 1]
                )

                with service_col:

                    service_name = st.text_input(
                        "Service Name",
                        value=item.get(
                            "service_name",
                            "",
                        ),
                        key=f"service_{index}",
                    )

                with quantity_col:

                    quantity = st.number_input(
                        "Quantity",
                        min_value=1,
                        value=int(
                            item.get(
                                "quantity",
                                1,
                            )
                        ),
                        step=1,
                        key=f"quantity_{index}",
                    )

                # -----------------------------------------
                # PRICE LOOKUP
                # -----------------------------------------

                price_result = find_service_price(
                    service_name
                )

                if price_result["found"]:

                    unit_price = float(
                        price_result["price"]
                    )

                    amount = (
                        unit_price * quantity
                    )

                    subtotal += amount

                    matched_service = (
                        price_result[
                            "matched_service"
                        ]
                    )

                    match_type = (
                        price_result[
                            "match_type"
                        ]
                    )

                    source = (
                        price_result[
                            "source"
                        ]
                    )

                    st.success(
                        f"✓ Price Verified — "
                        f"₹{unit_price:,.2f}"
                    )

                    info1, info2, info3 = st.columns(3)

                    with info1:

                        st.caption(
                            "Database Service"
                        )

                        st.write(
                            matched_service
                        )

                    with info2:

                        st.caption(
                            "Match Type"
                        )

                        st.write(
                            match_type
                        )

                    with info3:

                        st.caption(
                            "Price Source"
                        )

                        st.write(
                            source
                        )

                    st.info(
                        f"{quantity} × "
                        f"₹{unit_price:,.2f} = "
                        f"₹{amount:,.2f}"
                    )

                    invoice_items.append(
                        {
                            "service":
                                service_name,

                            "quantity":
                                quantity,

                            "unit_price":
                                unit_price,

                            "amount":
                                amount,

                            "price_found":
                                True,

                            "matched_service":
                                matched_service,

                            "match_type":
                                match_type,

                            "price_source":
                                source,
                        }
                    )

                else:

                    all_prices_found = False

                    st.error(
                        f"⚠ Price Not Found — "
                        f"{service_name}"
                    )

                    st.warning(
                        "No verified price exists for "
                        f"'{service_name}'. "
                        "The system will NOT invent "
                        "or estimate a price."
                    )

                    invoice_items.append(
                        {
                            "service":
                                service_name,

                            "quantity":
                                quantity,

                            "unit_price":
                                0,

                            "amount":
                                0,

                            "price_found":
                                False,

                            "matched_service":
                                None,

                            "match_type":
                                "Not Found",

                            "price_source":
                                price_result[
                                    "source"
                                ],
                        }
                    )


        # =================================================
        # NOTES
        # =================================================

        st.write("")

        with st.container(border=True):

            st.subheader("📝 Invoice Notes")

            notes = st.text_area(
                "Notes",
                value=data.get(
                    "notes",
                    "",
                ),
                placeholder=(
                    "Delivery timeline, payment terms, "
                    "additional instructions..."
                ),
                height=100,
                label_visibility="collapsed",
            )


        # =================================================
        # SETTINGS + SUMMARY
        # =================================================

        st.write("")

        settings_col, summary_col = st.columns(2)

        with settings_col:

            with st.container(border=True):

                st.subheader(
                    "⚙ Invoice Settings"
                )

                gst_rate = st.number_input(
                    "GST Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=18.0,
                    step=1.0,
                )

        gst_amount = (
            subtotal * gst_rate / 100
        )

        total = (
            subtotal + gst_amount
        )

        with summary_col:

            with st.container(border=True):

                st.subheader(
                    "💰 Invoice Summary"
                )

                summary1, summary2 = st.columns(2)

                with summary1:

                    st.write("Subtotal")

                    st.write(
                        f"GST ({gst_rate:.0f}%)"
                    )

                    st.markdown(
                        "**Total**"
                    )

                with summary2:

                    st.write(
                        f"₹{subtotal:,.2f}"
                    )

                    st.write(
                        f"₹{gst_amount:,.2f}"
                    )

                    st.markdown(
                        f"**₹{total:,.2f}**"
                    )


        # =================================================
        # PREVIEW
        # =================================================

        st.write("")

        with st.container(border=True):

            st.subheader(
                "👁 Invoice Preview"
            )

            st.caption(
                "Review the invoice before approval."
            )

            customer_preview, invoice_preview = (
                st.columns(2)
            )

            with customer_preview:

                st.write("**Bill To**")

                st.write(
                    customer_name
                )

                st.caption(
                    email
                )

            with invoice_preview:

                st.write(
                    "**Invoice Number**"
                )

                if st.session_state.invoice_number:

                    st.write(
                        st.session_state.invoice_number
                    )

                else:

                    st.caption(
                        "Generated after approval"
                    )

            st.divider()

            if invoice_items:

                preview_rows = []

                for item in invoice_items:

                    preview_rows.append(
                        {
                            "Service":
                                item["service"],

                            "Database Match":
                                item.get(
                                    "matched_service",
                                    "-"
                                ),

                            "Match Type":
                                item.get(
                                    "match_type",
                                    "-"
                                ),

                            "Quantity":
                                item["quantity"],

                            "Unit Price":
                                (
                                    f"₹{item['unit_price']:,.2f}"
                                    if item["price_found"]
                                    else "Not Found"
                                ),

                            "Amount":
                                (
                                    f"₹{item['amount']:,.2f}"
                                    if item["price_found"]
                                    else "-"
                                ),
                        }
                    )

                st.dataframe(
                    pd.DataFrame(
                        preview_rows
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            st.divider()

            total_col1, total_col2 = st.columns(2)

            with total_col1:

                st.write(
                    f"Subtotal: ₹{subtotal:,.2f}"
                )

                st.write(
                    f"GST ({gst_rate:.0f}%): "
                    f"₹{gst_amount:,.2f}"
                )

            with total_col2:

                st.metric(
                    "Total Amount",
                    f"₹{total:,.2f}",
                )


        # =================================================
        # APPROVAL
        # =================================================

        st.write("")

        with st.container(border=True):

            st.subheader(
                "👤 Human Review & Approval"
            )

            if all_prices_found and invoice_items:

                st.success(
                    "All service prices have been verified. "
                    "The invoice is ready for human approval."
                )

                if st.button(
                    "✓ Approve & Generate Invoice",
                    type="primary",
                    use_container_width=True,
                ):

                    invoice_number = (
                        get_next_invoice_number()
                    )

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
                        status="Approved",
                    )

                    st.session_state.approved = True

                    st.session_state.invoice_number = (
                        invoice_number
                    )

                    st.success(
                        f"Invoice {invoice_number} "
                        "approved and saved successfully."
                    )

            else:

                st.warning(
                    "Approval is disabled because one or "
                    "more services do not have a verified price."
                )


        # =================================================
        # PDF DOWNLOAD
        # =================================================

        if st.session_state.approved:

            st.write("")

            with st.container(border=True):

                st.subheader(
                    "📄 Final Invoice"
                )

                st.success(
                    f"Invoice "
                    f"{st.session_state.invoice_number} "
                    "is ready for download."
                )

                pdf_file = generate_invoice_pdf(
                    customer_name,
                    email,
                    invoice_items,
                    subtotal,
                    gst_rate,
                    gst_amount,
                    total,
                    notes,
                    invoice_number=(
                        st.session_state.invoice_number
                    ),
                )

                st.download_button(
                    "📄 Download PDF Invoice",
                    data=pdf_file,
                    file_name=(
                        f"{st.session_state.invoice_number}.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )


# =========================================================
# INVOICE HISTORY
# =========================================================

elif page == "🗂️ Invoice History":

    st.title("🗂️ Invoice History")

    st.caption(
        "Previously approved invoices stored "
        "in your SQLite database."
    )

    st.divider()

    invoices = get_all_invoices()

    if not invoices:

        st.info(
            "No invoices have been created yet."
        )

    else:

        for invoice in reversed(invoices):

            with st.container(border=True):

                header_col, total_col = st.columns(
                    [3, 1]
                )

                with header_col:

                    st.subheader(
                        f"🧾 {invoice['invoice_number']}"
                    )

                    st.caption(
                        f"{invoice['customer']} • "
                        f"{invoice['created_at']}"
                    )

                with total_col:

                    st.metric(
                        "Total",
                        f"₹{invoice['total']:,.2f}",
                    )

                st.divider()

                info1, info2, info3 = st.columns(3)

                with info1:

                    st.write("**Customer**")

                    st.write(
                        invoice["customer"]
                    )

                with info2:

                    st.write("**Email**")

                    st.write(
                        invoice["email"]
                    )

                with info3:

                    st.write("**Status**")

                    if invoice["status"] == "Approved":

                        st.success(
                            invoice["status"]
                        )

                    else:

                        st.warning(
                            invoice["status"]
                        )

                st.write("")

                rows = []

                for item in invoice["items"]:

                    amount = (
                        item["quantity"]
                        * item["unit_price"]
                    )

                    rows.append(
                        {
                            "Service":
                                item["service"],

                            "Quantity":
                                item["quantity"],

                            "Unit Price":
                                f"₹{item['unit_price']:,.2f}",

                            "Amount":
                                f"₹{amount:,.2f}",
                        }
                    )

                if rows:

                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                st.write(
                    f"**Subtotal:** "
                    f"₹{invoice['subtotal']:,.2f}"
                )

                st.write(
                    f"**GST ({invoice['gst_rate']:.0f}%):** "
                    f"₹{invoice['gst_amount']:,.2f}"
                )

                st.markdown(
                    f"### Total: ₹{invoice['total']:,.2f}"
                )

                if invoice["notes"]:

                    st.caption(
                        f"Notes: {invoice['notes']}"
                    )