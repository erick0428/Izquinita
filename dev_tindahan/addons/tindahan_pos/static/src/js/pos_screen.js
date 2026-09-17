/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class POSScreen extends Component {
    setup() {
        console.log("POSScreen loaded"); 
        this.orm = useService("orm");

        this.state = useState({
            products: [],
            variants: [],
            activeVariant: null,
            cart: [],
        });

        onWillStart(async () => {
            const products = await this.orm.searchRead(
                "tindahan_pos.product",
                [],
                ["id", "name", "srp", "variant_id"]
            );

            const variantsMap = {};
            products.forEach(p => {
                if (p.variant_id) {
                    variantsMap[p.variant_id[0]] = {
                        id: p.variant_id[0],
                        name: p.variant_id[1],
                    };
                }
            });

            const variants = Object.values(variantsMap);

            this.state.products = products || [];
            this.state.variants = variants;
            this.state.activeVariant = variants.length ? variants[0].id : null;
        });
    }

    selectVariant(id) {
        this.state.activeVariant = id;
    }

    addProduct(product) {
        const existing = this.state.cart.find(
            l => l.product_id === product.id
        );

        if (existing) {
            existing.qty += 1;
        } else {
            this.state.cart.push({
                product_id: product.id,
                name: product.name,
                price: product.srp,
                qty: 1,
            });
        }
    }

    get filteredProducts() {
        if (!this.state || !this.state.products) {
            return [];
        }

        return this.state.products.filter(p =>
            !this.state.activeVariant ||
            (p.variant_id && p.variant_id[0] === this.state.activeVariant)
        );
    }
}

POSScreen.template = "tindahan_pos.POSScreen_v2";

registry.category("actions").add("tindahan_pos.pos_screen1", POSScreen);