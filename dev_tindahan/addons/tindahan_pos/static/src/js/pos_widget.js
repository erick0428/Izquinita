
/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class PosWidget extends Component {
    static template = "tindahan_pos.PosWidget";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        const context = this.props.action.context || {};

        this.state = useState({
            products: [],
            search: "",
            loading: false,
            orderId: context.active_id || context.default_pos_id,
            items: [],
            total: 0,
            orderName: "",
            addingProductId: false,
            variants: [],
            selectedVariant: "all",
        });

        onWillStart(async () => {
            await this.loadProducts();

            if (this.state.orderId) {
                const order = await this.orm.call(
                    "tindahan_pos.pos",
                    "get_widget_order_data",
                    [[this.state.orderId]]
                );

                this.state.items = order.items || [];
                this.state.total = order.total || 0;
                this.state.orderName = order.name || "";
            }
        });
    }

    // =========================================
    // FILTER PRODUCTS BY VARIANT AND SEARCH
    // =========================================

    get filteredProducts() {
        const products = this.state.products || [];
        const search = (this.state.search || "")
            .toLowerCase()
            .trim();

        return products.filter((product) => {
            const matchesVariant =
                this.state.selectedVariant === "all" ||
                (product.variant || "") ===
                    this.state.selectedVariant;

            const matchesSearch =
                !search ||
                (product.name || "")
                    .toLowerCase()
                    .includes(search) ||
                (product.variant || "")
                    .toLowerCase()
                    .includes(search);

            return matchesVariant && matchesSearch;
        });
    }

    // =========================================
    // SELECT VARIANT TAB
    // =========================================

    selectVariant(variant) {
        this.state.selectedVariant = variant;
    }

    // =========================================
    // LOAD PRODUCTS
    // =========================================

    async loadProducts() {
        this.state.loading = true;

        try {
            const data = await this.orm.call(
                "tindahan_pos.pos",
                "get_product_widget_data",
                [],
                { search: this.state.search || "" }
            );

            this.state.products = data.products || [];

            // Generate unique variant tabs.
            this.state.variants = [
                ...new Set(
                    this.state.products
                        .map((product) => product.variant)
                        .filter((variant) => variant)
                ),
            ];

            // Return to All if the selected variant
            // is no longer present in the results.
            if (
                this.state.selectedVariant !== "all" &&
                !this.state.variants.includes(
                    this.state.selectedVariant
                )
            ) {
                this.state.selectedVariant = "all";
            }
        } catch (error) {
            console.error(
                "Failed to load POS products:",
                error
            );

            this.state.products = [];
            this.state.variants = [];

            this.notification.add(
                "Unable to load products. Check the Odoo server logs.",
                { type: "danger" }
            );
        } finally {
            this.state.loading = false;
        }
    }

    // =========================================
    // SEARCH PRODUCTS
    // =========================================

    async onSearchInput(event) {
        this.state.search = event.target.value;
        await this.loadProducts();
    }

    // =========================================
    // ADD PRODUCT
    // =========================================

    async addProduct(product) {
        if (!this.state.orderId) {
            this.notification.add(
                "No existing POS transaction was provided.",
                { type: "danger" }
            );
            return;
        }

        if (this.state.addingProductId) {
            return;
        }

        this.state.addingProductId = product.id;

        try {
            const order = await this.orm.call(
                "tindahan_pos.pos",
                "add_widget_product",
                [[this.state.orderId], product.id]
            );

            this.state.items = order.items || [];
            this.state.total = order.total || 0;
            this.state.orderName = order.name || "";

            this.notification.add(
                `${product.name} added to ${order.name}.`,
                { type: "success" }
            );
        } catch (error) {
            console.error(
                "Failed to add product:",
                error
            );

            this.notification.add(
                "Unable to add product to the existing order.",
                { type: "danger" }
            );
        } finally {
            this.state.addingProductId = false;
        }
    }
}

registry.category("actions").add(
    "tindahan_pos.pos_widget",
    PosWidget
);
