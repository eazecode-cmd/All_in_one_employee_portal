/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PortalAttendance = publicWidget.Widget.extend({
    selector: '.o_portal_attendance_page',
    events: {
        'click #o_portal_attendance_toggle_btn': '_onToggleAttendance',
    },

    _onToggleAttendance: function (ev) {
        const btn = ev.currentTarget;
        
        btn.disabled = true;
        btn.innerText = "Processing Location...";

        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this._submitAttendance(position.coords.latitude, position.coords.longitude, btn);
                },
                (error) => {
                    console.error("Geolocation error:", error);
                    // Fallback: Submit without location if denied
                    this._submitAttendance(null, null, btn);
                },
                { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
            );
        } else {
            this._submitAttendance(null, null, btn);
        }
    },

    _submitAttendance: function (lat, long, btn) {
        fetch('/my/attendance/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                params: {
                    latitude: lat,
                    longitude: long,
                }
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.result && !data.result.error) {
                // Success: Reload page to show new record in table
                location.reload();
            } else if (data.result && data.result.error) {
                alert(data.result.error);
                btn.disabled = false;
                btn.innerText = "Try Again";
            }
        })
        .catch(err => {
            console.error("Attendance failed:", err);
            alert("Connection error. Please try again.");
            btn.disabled = false;
        });
    },
});
