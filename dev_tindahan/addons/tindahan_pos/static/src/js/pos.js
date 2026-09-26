/** @odoo-module **/

import { Component, onWillStart, useState,onMounted,
    onWillUnmount, } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class TindahanPOS extends Component {

    static template = "tindahan_pos.POSScreen";

    setup() {

        this.state = useState({
            variants: [],
            products: [],
            cart: [],
            total: 0,
            search: "",
            activeVariant: null,

            
            cashInput: "",
            cash: "",
            change: 0,
            showPaymentModal: false,
            customer_name: "",

            session: null,

            openingCashInput: "",
            closingCashInput: "",
            showCashKeypad: false,

            showCloseDialog: false,
            showReport: false,
            report: null,

       
        });

        this.handlePaymentKeyboard =
            this.handlePaymentKeyboard.bind(this);

        onMounted(() => {
            window.addEventListener(
                "keydown",
                this.handlePaymentKeyboard
            );
        });

        onWillUnmount(() => {
            window.removeEventListener(
                "keydown",
                this.handlePaymentKeyboard
            );
        });

        onWillStart(async () => {
            await this.loadProducts();
            await this.loadSession(); // 🔥 important
        });
    }
    handlePaymentKeyboard(event) {
        if (
            !this.state.showPaymentModal &&
            !this.state.showCashKeypad
        ) {
            return;
        }

        // =========================
        // PAYMENT MODAL
        // =========================

        if (this.state.showPaymentModal) {

            if (/^[0-9]$/.test(event.key)) {
                this.pressKey(event.key);
                event.preventDefault();
                return;
            }

            if (
                event.key === "." ||
                event.key === "Decimal"
            ) {
                this.pressKey(".");
                event.preventDefault();
                return;
            }

            if (event.key === "Backspace") {
                this.pressKey("⌫");
                event.preventDefault();
                return;
            }

            if (event.key === "Enter") {
                this.confirmPayment();
                event.preventDefault();
                return;
            }

            if (event.key === "Escape") {
                this.closePaymentModal();
                event.preventDefault();
                return;
            }
        }


        // =========================
        // CASH COUNTED KEYPAD
        // =========================

        if (this.state.showCashKeypad) {

            if (/^[0-9]$/.test(event.key)) {
                this.pressClosingCashKey(event.key);
                event.preventDefault();
                return;
            }

            if (
                event.key === "." ||
                event.key === "Decimal"
            ) {
                this.pressClosingCashKey(".");
                event.preventDefault();
                return;
            }

            if (event.key === "Backspace") {
                this.pressClosingCashKey("⌫");
                event.preventDefault();
                return;
            }

            if (event.key === "Enter") {
                this.closeCashKeypad();
                event.preventDefault();
                return;
            }

            if (event.key === "Escape") {
                this.closeCashKeypad();
                event.preventDefault();
                return;
            }
        }
    }


    openPaymentModal() {
        if (!this.state.cart || !this.state.cart.length) {
            alert("Cart is empty.");
            return;
        }

        this.state.cash = 0;
        this.state.cashInput = 0;
        this.state.change = 0;
        this.state.showPaymentModal = true;
    }
    closePaymentModal() {
        this.state.showPaymentModal = false;
        this.state.cash = 0;
        this.state.cashInput = 0;
        this.state.change = 0;
    }
    clearPayment() {
        this.state.cash = 0;
        this.state.cashInput = 0;
        this.state.change = 0;
    }

    // ✅ MOVE THIS INSIDE
    pressKey(key) {
        let value = this.state.cashInput || "";

        if (key === "⌫") {
            value = value.slice(0, -1);
        }

        else if (key === ".") {
            // Only allow one decimal point
            if (!value.includes(".")) {
                value = value === "" ? "0." : value + ".";
            }
        }

        else if (/^[0-9]$/.test(key)) {
            // Avoid unnecessary leading zeros
            if (value === "0") {
                value = key;
            } else {
                value += key;
            }
        }

        this.state.cashInput = value;

        // Numeric value only for calculations
        const cash = parseFloat(value) || 0;

        this.state.cash = cash;

        this.state.change = Math.max(
            0,
            cash - (this.state.total || 0)
        );
    }

    openCashKeypad() {
        this.state.showCashKeypad = true;
    }

    closeCashKeypad() {
        this.state.showCashKeypad = false;
    }

    clearClosingCash() {
        this.state.closingCashInput = "";
    }
    pressClosingCashKey(key) {
        let value = String(
            this.state.closingCashInput || ""
        );

        if (key === "⌫") {
            value = value.slice(0, -1);
        }

        else if (key === ".") {
            // Only one decimal point
            if (!value.includes(".")) {
                value = value === ""
                    ? "0."
                    : value + ".";
            }
        }

        else {
            // Prevent unnecessary leading zeros
            if (value === "0") {
                value = key;
            } else {
                value += key;
            }
        }

        this.state.closingCashInput = value;
    }

    computeChange() {
        const cash = parseFloat(this.state.cash) || 0;
        const change = cash - this.state.total;

        this.state.change = change > 0 ? change : 0;
    }

    // =========================================================
    // LOAD PRODUCTS
    // =========================================================

    async loadProducts() {

        const products = await rpc(
            "/web/dataset/call_kw",
            {
                model: "tindahan_pos.product",
                method: "search_read",
                args: [
                    [],
                    [
                        "id",
                        "name",
                        "description",
                        "srp",
                        "variant_id",
                        "image",
                    ],
                ],
                kwargs: {},
            }
        );

        this.state.products = products;

        // Get unique variants
        const map = {};

        products.forEach(product => {
            if (!product.variant_id) return;

            const [id, name] = product.variant_id;

            if (!map[id]) {
                map[id] = { id, name, products: [] };
            }

            map[id].products.push(product);
        });

        this.state.variants = Object.values(map);
        // ✅ set default tab
        this.state.activeVariant = this.state.variants[0]?.id;
    }


    // =========================================================
    // ADD PRODUCT
    // =========================================================

    addProduct(product) {
        const cart = [...this.state.cart];

        const existing = cart.find(
            line => line.product_id === product.id
        );

        if (existing) {
            existing.quantity += 1;
        } else {
            cart.push({
                product_id: product.id,
                name: product.name,
                description: product.description,
                price: product.srp || 0,
                quantity: 1,
            });
        }
        setTimeout(() => {
            const cart = document.querySelector(".cart");
            if (cart) {
                cart.scrollTop = cart.scrollHeight;
            }
        });
        this.state.cart = cart;   // 🔥 trigger reactivity
        this.calculateTotal();
    }


    // =========================================================
    // INCREASE QUANTITY
    // =========================================================

    increaseQuantity(line) {
        line.quantity += 1;

        this.state.cart = [...this.state.cart]; // 🔥 force rerender
        this.calculateTotal();
    }


    // =========================================================
    // DECREASE QUANTITY
    // =========================================================

    decreaseQuantity(line) {

        if (line.quantity > 1) {

            line.quantity -= 1;

        } else {

            this.removeProduct(line);
        }

        this.calculateTotal();
    }


    // =========================================================
    // REMOVE PRODUCT
    // =========================================================

    removeProduct(line) {
        this.state.cart = this.state.cart.filter(
            l => l.product_id !== line.product_id
        );

        this.calculateTotal();
    }


    // =========================================================
    // CALCULATE TOTAL
    // =========================================================

    calculateTotal() {

        this.state.total = this.state.cart.reduce(
            (total, line) => {
                return total + (
                    line.price * line.quantity
                );
            },
            0
        );
    }


    // =========================================================
    // CLEAR CART
    // =========================================================

    clearCart() {
        this.state.cart = [];
        this.state.total = 0;
        this.state.cash = 0;
        this.state.change = 0;
        
    }


    // =========================================================
    // SAVE ORDER
    // =========================================================

    async saveOrder(cash, change) {

        if (!this.state.cart.length) {

            alert("Please add a product first.");

            return null;
        }

        const lines = this.state.cart.map(line => {

            return [
                0,
                0,
                {
                    product_id: line.product_id,
                    quantity: line.quantity,
                },
            ];

        });

        try {

            const order = await rpc(
                "/web/dataset/call_kw",
                {
                    model: "tindahan_pos.pos",

                    method: "create_pos_order",

                    args: [
                        {
                            customer_name:
                                this.state.customer_name ||
                                "Walk-in Customer",

                            cash: cash,

                            change: change,

                            line_ids: lines,
                            kitchen_status: "new",
                        },
                    ],

                    kwargs: {},
                }
            );

            console.log(
                "ORDER SENT TO KITCHEN:",
                order
            );

            return order;

        } catch (error) {

            console.error(
                "Failed to save order:",
                error
            );

            alert(
                "Failed to save order."
            );

            return null;
        }
    }



    async payOrder() {

        const cash = parseFloat(this.state.cash) || 0;

        if (!this.state.session) {
            alert("Please open POS first.");
            return;
        }

        if (!this.state.cart.length) {
            alert("No items in cart.");
            return;
        }

        if (cash < this.state.total) {
            alert("Insufficient cash.");
            return;
        }

        // Calculate change
        this.computeChange();

        const change = this.state.change;

        // -------------------------------------------------
        // SAVE RECEIPT DATA
        // -------------------------------------------------

        this.state.receipt = {
            order_name: "POS-" + Date.now(),

            customer_name:
                this.state.customer_name ||
                "Walk-in Customer",

            date: new Date().toLocaleString(),

            lines: this.state.cart.map(line => ({
                product_id: line.product_id,
                name: line.name,
                price: line.price,
                quantity: line.quantity,
            })),

            total: this.state.total,

            cash: cash,

            change: change,
        };

        // -------------------------------------------------
        // SAVE ORDER
        // -------------------------------------------------

        const order = await this.saveOrder(cash, change);

        if (!order) {
            return;
        }

        // Use actual Odoo order number
        this.state.receipt.order_name = order.name;

        // -------------------------------------------------
        // SHOW RECEIPT
        // -------------------------------------------------

        this.state.showReceipt = true;

        await new Promise(resolve =>
            setTimeout(resolve, 100)
        );

        window.print();

        // -------------------------------------------------
        // HIDE RECEIPT
        // -------------------------------------------------

        this.state.showReceipt = false;

        // -------------------------------------------------
        // RESET PAYMENT
        // -------------------------------------------------

        this.state.cash = "";
        this.state.change = 0;
        this.state.customer_name = "";

        // -------------------------------------------------
        // CLEAR CART
        // -------------------------------------------------

        this.clearCart();
    }


    async loadSession() {
        const sessions = await rpc("/web/dataset/call_kw", {
            model: "tindahan_pos.session",
            method: "search_read",
            args: [
                [['state', '=', 'open']],
                [
                    'id',
                    'name',
                    'opening_cash',
                    'total_sales'
                ]
            ],
            kwargs: {},
        });

        this.state.session = sessions[0] || null;
    }

    async call(model, method, args = []) {
        return rpc("/web/dataset/call_kw", {
            model,
            method,
            args,
            kwargs: {}, // always included
        });
    }
    async openSession() {

        const input = prompt(
            "Enter Opening Cash:"
        );

        if (input === null) {
            return;
        }

        const openingCash = parseFloat(input);

        if (isNaN(openingCash) || openingCash < 0) {
            alert("Please enter a valid opening cash amount.");
            return;
        }

        await this.call(
            "tindahan_pos.session",
            "create",
            [{
                name: "New Session",
                opening_cash: openingCash,
                state: "open",
            }]
        );

        await this.loadSession();

        alert(
            `POS opened with ${this.formatPrice(openingCash)}`
        );
    }

    // async closeSession() {
    //     if (!this.state.session) {
    //         alert("No active session.");
    //         return;
    //     }
   
    //     await rpc("/web/dataset/call_kw", {
    //         model: "tindahan_pos.session",
    //         method: "write",
    //         args: [
    //             [this.state.session.id],
    //             { state: "closed" }
    //         ],
    //         kwargs: {}, // always included
    //     });
       
    //     this.state.session = null;
    // }

    async confirmCloseSession() {
        if (!this.state.session) {
            alert("No active POS session.");
            return;
        }

        const actualCash = parseFloat(
            this.state.closingCashInput
        );

        if (isNaN(actualCash) || actualCash < 0) {
            alert("Please enter a valid actual cash amount.");
            return;
        }

        const sessionId = this.state.session.id;

        try {
            const report = await this.call(
                "tindahan_pos.session",
                "close_session",
                [
                    [sessionId],
                    actualCash,
                ]
            );

            

            console.log("Close session result:", report);

            if (!report) {
                alert("Failed to close POS session.");
                return;
            }

            this.state.report = {
                opening_cash: report.opening_cash,
                total_sales: report.total_sales,
                expected_cash: report.expected_cash,
                closing_input: report.closing_input,
                difference: report.difference,
            };

            this.state.session = null;
            this.state.showCloseDialog = false;
            this.state.showReport = true;

            console.log(
                "POS SESSION CLOSED:",
                sessionId
            );

        } catch (error) {
            console.error(
                "Error closing POS session:",
                error
            );

            alert(
                "Failed to close POS session."
            );
        }
    }

    async openCloseDialog() {
        console.log("CLOSE POS clicked");

        if (!this.state.session) {
            alert("No active POS session.");
            return;
        }

        try {
            // Get the latest session data
            const sessions = await this.call(
                "tindahan_pos.session",
                "search_read",
                [
                    [
                        ["id", "=", this.state.session.id]
                    ],
                    [
                        "id",
                        "name",
                        "opening_cash",
                        "total_sales"
                    ]
                ]
            );

            if (!sessions.length) {
                alert("Session not found.");
                return;
            }

            // Replace old session data with latest data
            this.state.session = sessions[0];

            console.log(
                "Updated session:",
                this.state.session
            );

            this.state.closingCashInput = "";
            this.state.showCloseDialog = true;

        } catch (error) {
            console.error(
                "Failed to load latest session:",
                error
            );

            alert(
                "Failed to load latest session data."
            );
        }
    }
    async confirmPayment() {
        const total = this.state.total || 0;
        const cash = this.state.cash || 0;

        if (cash < total) {
            alert("Insufficient cash.");
            return;
        }

        this.state.change = cash - total;

        // Your existing payOrder logic
        await this.payOrder();

        this.state.showPaymentModal = false;
    }



    closeReport() {
        this.state.showReport = false;
        this.state.session = null;
    }
    // =========================================================
    // FORMAT MONEY
    // =========================================================

    formatPrice(value) {

            return new Intl.NumberFormat(
                "en-PH",
                {
                    style: "currency",
                    currency: "PHP",
                }
            ).format(value || 0);
        }
    }



    registry
        .category("actions")
        .add(
            "tindahan_pos.pos_screen",
            TindahanPOS
        );
