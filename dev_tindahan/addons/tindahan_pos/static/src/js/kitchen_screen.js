/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

console.log("🔥🔥 KITCHEN JS FILE LOADED 🔥🔥");
export class KitchenScreen extends Component {

    static template = "tindahan_pos.KitchenScreen";

    setup() {
        console.log("🔥🔥 KITCHEN SETUP 🔥🔥");
        this.orm = useService("orm");

        this.state = useState({
            orders: [],
            loading: true,
            lastUpdate: null,
        });

        this.refreshTimer = null;

        onMounted(async () => {
            console.log("🔥🔥 KITCHEN MOUNTED 🔥🔥");
            await this.loadOrders();

            // Refresh every 3 seconds
            this.refreshTimer = setInterval(
                () => this.loadOrders(),
                3000
            );
        });

        onWillUnmount(() => {
            console.log("🔥🔥 KITCHEN UNMOUNTED 🔥🔥");
            if (this.refreshTimer) {
                clearInterval(this.refreshTimer);
                this.refreshTimer = null;
            }
        });
    }

    // =====================================================
    // LOAD ORDERS
    // =====================================================

    async loadOrders() {
        console.log("🔥🔥 CALLING get_kitchen_orders 🔥🔥");
        try {

            const orders = await this.orm.call(
                "tindahan_pos.pos",
                "get_kitchen_orders",
                []
            );

            this.state.orders = orders;

            this.state.lastUpdate =
                new Date().toLocaleTimeString();

        } catch (error) {

            console.error(
                "Failed to load kitchen orders:",
                error
            );

        } finally {

            this.state.loading = false;
        }
    }

    // =====================================================
    // FILTER
    // =====================================================

    get newOrders() {

        return this.state.orders.filter(
            order => order.kitchen_status === "new"
        );
    }

    get preparingOrders() {

        return this.state.orders.filter(
            order => order.kitchen_status === "preparing"
        );
    }

    get readyOrders() {

        return this.state.orders.filter(
            order => order.kitchen_status === "ready"
        );
    }

    // =====================================================
    // START PREPARING
    // =====================================================

    startPreparing = async (order) => {
        try {
            console.log("START PREPARING:", order);

            await this.orm.call(
                "tindahan_pos.pos",
                "action_start_preparing",
                [[order.id]]
            );

            await this.loadOrders();

        } catch (error) {
            console.error(
                "START PREPARING ERROR:",
                error
            );

            alert("Unable to start this order.");
        }
    };

    // =====================================================
    // MARK READY
    // =====================================================

    markReady = async (order) => {
        try {
            console.log("MARK READY:", order);

            await this.orm.call(
                "tindahan_pos.pos",
                "action_mark_ready",
                [[order.id]]
            );

            await this.loadOrders();

        } catch (error) {
            console.error(
                "MARK READY ERROR:",
                error
            );

            alert("Unable to mark this order as ready.");
        }
    };

    // =====================================================
    // COMPLETE
    // =====================================================

    completeOrder = async (order) => {
        try {
            console.log("COMPLETE:", order);

            await this.orm.call(
                "tindahan_pos.pos",
                "action_complete",
                [[order.id]]
            );

            await this.loadOrders();

        } catch (error) {
            console.error(
                "COMPLETE ERROR:",
                error
            );

            alert("Unable to complete this order.");
        }
    };

    // =====================================================
    // FORMAT TIME
    // =====================================================

    formatTime(dateString) {

        if (!dateString) {
            return "";
        }

        const date = new Date(dateString);

        return date.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    // =====================================================
    // FORMAT QUANTITY
    // =====================================================

    formatQuantity(quantity) {

        if (Number.isInteger(quantity)) {
            return quantity;
        }

        return Number(quantity).toFixed(2);
    }
}

registry
    .category("actions")
    .add(
        "tindahan_pos.kitchen_screen",
        KitchenScreen
    );
console.log("🔥🔥 KITCHEN ACTION REGISTERED 🔥🔥");