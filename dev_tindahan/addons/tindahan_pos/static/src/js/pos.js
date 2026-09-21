/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
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

            cash: "",
            change: 0,
            customer_name: "",

            session: null,

            openingCashInput: "",
            closingCashInput: "",

            showCloseDialog: false,
            showReport: false,
            report: null,
        });



        onWillStart(async () => {
            await this.loadProducts();
            await this.loadSession(); // 🔥 important
        });
    }


    // ✅ MOVE THIS INSIDE
    pressKey(key) {

        if (key === "C") {
            this.state.cash = "";
            this.state.change = 0;
            return;
        }

        if (key === "⌫") {
            this.state.cash = this.state.cash.slice(0, -1);
            this.computeChange();
            return;
        }

        if (key === "." && this.state.cash.includes(".")) return;

        if (this.state.cash === "0" && key !== ".") {
            this.state.cash = key;
        } else {
            this.state.cash += key;
        }

        this.computeChange();
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

            return;
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


        await rpc(
            "/web/dataset/call_kw",
            {
                model: "tindahan_pos.pos",
                method: "create",
                args: [
                    {
                        session_id: this.state.session.id,
                        name: "New",
                        customer_name: this.state.customer_name || "Walk-in Customer",
                        cash: cash,
                        change: change,
                        line_ids: lines,
                    },
                ],
                kwargs: {},
            }
        );


        alert("Order saved!");
        await this.loadSession();
        this.clearCart();
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
        // SAVE RECEIPT DATA BEFORE SAVING/CLEARING ORDER
        // -------------------------------------------------

        this.state.receipt = {
            order_name: "POS-" + Date.now(),

            customer_name:
                this.state.customer_name || "Walk-in Customer",

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

        await this.saveOrder(cash, change);

        // -------------------------------------------------
        // SHOW RECEIPT
        // -------------------------------------------------

        this.state.showReceipt = true;

        // Wait for OWL to render the receipt
        await new Promise(resolve => setTimeout(resolve, 100));

        // Open browser print dialog
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

        // Optional notification
        // alert(`Change: ${this.formatPrice(change)}`);
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

    async closeSession() {
        if (!this.state.session) {
            alert("No active session.");
            return;
        }
   
        await rpc("/web/dataset/call_kw", {
            model: "tindahan_pos.session",
            method: "write",
            args: [
                [this.state.session.id],
                { state: "closed" }
            ],
            kwargs: {}, // always included
        });
       
        this.state.session = null;
    }

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

            // Get latest session data
            const data = await this.call(
                "tindahan_pos.session",
                "read",
                [
                    [sessionId],
                    [
                        "opening_cash",
                        "total_sales"
                    ]
                ]
            );

            if (!data || !data.length) {
                alert("Session not found.");
                return;
            }

            const session = data[0];

            const openingCash = session.opening_cash || 0;
            const totalSales = session.total_sales || 0;

            const expectedCash =
                openingCash + totalSales;

            const difference =
                actualCash - expectedCash;


            // ==========================================
            // CLOSE SESSION IN DATABASE
            // ==========================================

            await this.call(
                "tindahan_pos.session",
                "write",
                [
                    [sessionId],
                    {
                        closing_cash: expectedCash,
                        closing_input: actualCash,
                        state: "closed",
                    }
                ]
            );


            // ==========================================
            // CREATE CLOSING REPORT
            // ==========================================

            this.state.report = {
                opening_cash: openingCash,
                total_sales: totalSales,
                expected_cash: expectedCash,
                closing_input: actualCash,
                difference: difference,
            };


            // ==========================================
            // IMPORTANT:
            // REMOVE ACTIVE SESSION FROM UI
            // ==========================================

            this.state.session = null;


            // Close the closing dialog
            this.state.showCloseDialog = false;

            // Show report
            this.state.showReport = true;


            console.log("POS SESSION CLOSED:", sessionId);

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
    openCloseDialog() {
        console.log("CLOSE POS clicked");
        console.log("Current session:", this.state.session);

        if (!this.state.session) {
            alert("No active POS session.");
            return;
        }

        this.state.closingCashInput = "";
        this.state.showCloseDialog = true;

        console.log("showCloseDialog:", this.state.showCloseDialog);
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
