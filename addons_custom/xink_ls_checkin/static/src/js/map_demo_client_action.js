/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class MapDemoClientAction extends Component {
    static template = "xink_ls_checkin.map_demo_template";

    setup() {
        this.state = useState({
            employees: [],
            selectedEmployeeId: null,
            selectedDate: null,
            locations: [],
            totalCheckins: 0,
            loading: false,
            error: null,
        });

        onMounted(() => {
            this.loadEmployees();
            this.loadDataAndInitMap();
        });
    }

    onEmployeeChange(ev) {
        const selectedId = parseInt(ev.target.value);
        this.state.selectedEmployeeId = isNaN(selectedId) ? null : selectedId;
        this.state.error = null;
        this.loadDataAndInitMap();
    }

    onDateChange(ev) {
        const val = ev.target.value;
        this.state.selectedDate = val || null;
        this.state.error = null;
        this.loadDataAndInitMap();
    }

    async loadDataAndInitMap() {
        await this.loadLocations();
        if (this.state.locations.length > 0 && document.getElementById("map")) {
            await this.waitForLeaflet();
            this.initMap();
        }
    }

    async loadLocations() {
        this.state.loading = true;
        this.state.error = null;

        try {
            const result = await rpc("/xink_ls_checkin/get_locations", {
                employee_id: this.state.selectedEmployeeId,
                checkin_date: this.state.selectedDate,
            });
            this.state.locations = Array.isArray(result.data) ? result.data : [];
            this.state.totalCheckins = Array.isArray(result.data) ? result.data.length : 0;
        } catch (err) {
            this.state.error = "Không tải được dữ liệu địa điểm: " + (err.message || "Lỗi không xác định");
        } finally {
            this.state.loading = false;
        }
    }

    async loadEmployees() {
        this.state.loading = true;
        this.state.error = null;

        try {
            const employees = await rpc("/xink_ls_checkin/get_employees");
            this.state.employees = Array.isArray(employees) ? employees : [];
        } catch (err) {
            this.state.error = "Không tải được danh sách nhân viên: " + (err.message || "Lỗi không xác định");
        } finally {
            this.state.loading = false;
        }
    }

    async waitForLeaflet() {
        return new Promise((resolve) => {
            const checkLeaflet = () => {
                if (window.L && typeof window.L.markerClusterGroup === 'function') {
                    resolve();
                } else {
                    setTimeout(checkLeaflet, 100);
                }
            };
            checkLeaflet();
        });
    }

    initMap() {
        if (this.map && this.markerCluster) {
            this.map.removeLayer(this.markerCluster);
            this.map.remove();
            this.markers = [];
            this.markerCluster = null;
        }

        const map = L.map("map", {
            scrollWheelZoom: true,
        }).setView([14.0583, 108.2772], 6);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors | Demo by Nghia",
            maxZoom: 18,
        }).addTo(map);

        if (!L.markerClusterGroup) {
            this.state.error = "Không tải được plugin Leaflet MarkerCluster.";
            return;
        }

        const markers = L.markerClusterGroup({
            maxClusterRadius: 50,
            disableClusteringAtZoom: 15,
        });

        this.state.locations.forEach((loc) => {
            const lat = loc.in_latitude;
            const lng = loc.in_longitude;
            if (!lat || !lng) return;

            let iconColor;
            if (typeof loc.xink_potential_customer === 'boolean') {
                iconColor = loc.xink_potential_customer ? 'red' : 'green';
            } else {
                iconColor = 'green';
            }
            const markerIcon = this.makeIcon(iconColor);

            const marker = L.marker([lat, lng], {
                icon: markerIcon,
                locationId: loc.id,
            });

            const popupContent = `
                <div class="marker-popup">
                    <h6><i class="fa fa-store"></i> ${loc.xink_shop_name || ''}</h6>
                    <div class="info-item"><i class="fa fa-user"></i>
                        <strong>Nhân viên:</strong> ${loc.employee_id || ''}
                    </div>
                    <div class="info-item"><i class="fa fa-tag"></i>
                        <strong>Loại:</strong> ${loc.xink_potential_customer ? 'Khách hàng tiềm năng' : 'Khách hàng'}
                    </div>
                    <div class="info-item"><i class="fa fa-clock"></i>
                        <strong>Thời gian:</strong> ${loc.check_in || ''}
                    </div>
                </div>
            `;

            marker.bindPopup(popupContent, { maxWidth: 300, className: "custom-popup" });
            markers.addLayer(marker);
        });

        map.addLayer(markers);

        if (markers.getLayers().length > 1) {
            map.fitBounds(markers.getBounds().pad(0.1));
        } else if (markers.getLayers().length === 1) {
            map.setView(markers.getLayers()[0].getLatLng(), 15);
        } else {
            map.setView([14.0583, 108.2772], 6);
        }

        L.control.scale().addTo(map);
        this.map = map;
        this.markers = markers.getLayers();
        this.markerCluster = markers;

        setTimeout(() => map.invalidateSize(), 200);
    }

    makeIcon(color) {
        return L.icon({
            iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
            shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41],
        });
    }

    onLocationClick(ev) {
        if (!this.map || !this.markerCluster) return;

        const lat = parseFloat(ev.currentTarget.dataset.lat);
        const lng = parseFloat(ev.currentTarget.dataset.lng);
        const locationId = parseInt(ev.currentTarget.dataset.id);

        this.map.setView([lat, lng], 15, { animate: true, duration: 0.5 });

        const marker = this.markers.find(m => m.options.locationId === locationId);
        if (marker) {
            this.markerCluster.zoomToShowLayer(marker, () => {
                marker.openPopup();
                const el = marker.getElement();
                if (el) {
                    el.style.animation = "bounce 1s ease-in-out";
                    setTimeout(() => { el.style.animation = ""; }, 1000);
                }
            });
        }

        document.querySelectorAll(".clickable-row").forEach((row) =>
            row.classList.remove("table-active")
        );
        ev.currentTarget.classList.add("table-active");
    }
}

registry.category("actions").add("xink_ls_checkin.MapDemoClientAction", MapDemoClientAction);

// CSS động
const style = document.createElement("style");
style.textContent = `
    @keyframes bounce {
        0%, 20%, 60%, 100% { transform: translateY(0); }
        40% { transform: translateY(-20px); }
        80% { transform: translateY(-10px); }
    }
    .table-active {
        background-color: #d1ecf1 !important;
        border-color: #bee5eb !important;
    }
    .filter-bar {
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: #fff;
        padding: 10px;
        border-bottom: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .o_map_container {
        overflow: hidden;
    }
    .card-body {
        overflow: hidden;
    }
`;
document.head.appendChild(style);