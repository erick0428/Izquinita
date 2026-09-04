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
        });

        onWillStart(async () => {
            await this.loadProducts();
        });
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
        const variants = {};

        for (const product of products) {

            if (!product.variant_id) {
                continue;
            }

            const variantId = product.variant_id[0];
            const variantName = product.variant_id[1];

            if (!variants[variantId]) {

                variants[variantId] = {
                    id: variantId,
                    name: variantName,
                    products: [],
                };

            }

            variants[variantId].products.push(product);
        }

        this.state.variants = Object.values(variants);
    }


    // =========================================================
    // ADD PRODUCT
    // =========================================================

    addProduct(product) {

        const existing = this.state.cart.find(
            line => line.product_id === product.id
        );

        if (existing) {

            existing.quantity += 1;

        } else {

            this.state.cart.push({
                product_id: product.id,
                name: product.name,
                price: product.srp || 0,
                quantity: 1,
            });

        }

        this.calculateTotal();
    }


    // =========================================================
    // INCREASE QUANTITY
    // =========================================================

    increaseQuantity(line) {

        line.quantity += 1;

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

        const index = this.state.cart.indexOf(line);

        if (index !== -1) {

            this.state.cart.splice(index, 1);
        }

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

        this.state.cart.splice(
            0,
            this.state.cart.length
        );

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
