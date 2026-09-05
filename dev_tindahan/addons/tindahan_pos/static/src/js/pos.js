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
            search: "",          // ✅ added
            activeVariant: null, // ✅ added
            cash: "",      // ✅ REQUIRED
            change: 0,     // ✅ REQUIRED
            
        });



        onWillStart(async () => {
            await this.loadProducts();
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
    }


    // =========================================================
    // SAVE ORDER
    // =========================================================

    async saveOrder() {

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
                        name: "New",
                        line_ids: lines,
                    },
                ],
                kwargs: {},
            }
        );


        alert("Order saved!");

        this.clearCart();
    }

    async payOrder() {
        const cash = this.state.cash || 0;

        if (!this.state.cart.length) {
            alert("No items in cart.");
            return;
        }

        if (cash < this.state.total) {
            alert("Insufficient cash.");
            return;
        }

        await this.saveOrder();

        alert(`Change: ${this.formatPrice(this.state.change)}`);

        this.clearCart();
        this.state.cash = 0;
        this.state.change = 0;
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
