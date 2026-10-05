
/* =====================================================
   AINHS ATTENDANCE SYSTEM
   TEACHER BASE JAVASCRIPT
===================================================== */

document.addEventListener("DOMContentLoaded", function () {

    // =====================================================
    // 1. GET ELEMENTS
    // =====================================================

    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");

    const notificationBtn = document.getElementById("notificationBtn");
    const notificationPanel = document.getElementById("notificationPanel");

    const profileBtn = document.getElementById("profileBtn");
    const profileDropdown = document.getElementById("profileDropdown");

    const viewAllNotifications = document.getElementById("viewAllNotifications");

    const teacherLogout = document.getElementById("teacherLogout");


    // =====================================================
    // 2. SIDEBAR TOGGLE
    // =====================================================

    if (sidebar && sidebarToggle) {

        sidebarToggle.addEventListener("click", function () {

            sidebar.classList.toggle("collapsed");

            const isCollapsed = sidebar.classList.contains("collapsed");

            sidebarToggle.setAttribute(
                "aria-expanded",
                String(!isCollapsed)
            );

            // Save sidebar state
            localStorage.setItem(
                "teacher-sidebar-collapsed",
                String(isCollapsed)
            );

        });


        // Restore sidebar state after page reload
        const savedSidebarState = localStorage.getItem(
            "teacher-sidebar-collapsed"
        );

        if (savedSidebarState === "true") {

            sidebar.classList.add("collapsed");

            sidebarToggle.setAttribute(
                "aria-expanded",
                "false"
            );

        } else {

            sidebarToggle.setAttribute(
                "aria-expanded",
                "true"
            );

        }

    }


    // =====================================================
    // 3. CLOSE NOTIFICATION PANEL
    // =====================================================

    function closeNotificationPanel() {

        if (!notificationPanel || !notificationBtn) {
            return;
        }

        notificationPanel.classList.remove("show");

        notificationBtn.setAttribute(
            "aria-expanded",
            "false"
        );

    }


    // =====================================================
    // 4. CLOSE PROFILE DROPDOWN
    // =====================================================

    function closeProfileDropdown() {

        if (!profileDropdown || !profileBtn) {
            return;
        }

        profileDropdown.classList.remove("show");

        profileBtn.setAttribute(
            "aria-expanded",
            "false"
        );

    }


    // =====================================================
    // 5. NOTIFICATION BUTTON
    // =====================================================

    if (notificationBtn && notificationPanel) {

        notificationBtn.addEventListener("click", function (event) {

            event.stopPropagation();

            const isOpen = notificationPanel.classList.contains("show");

            closeProfileDropdown();

            notificationPanel.classList.toggle(
                "show",
                !isOpen
            );

            notificationBtn.setAttribute(
                "aria-expanded",
                String(!isOpen)
            );

        });


        // Prevent clicks inside the panel from closing it
        notificationPanel.addEventListener("click", function (event) {

            event.stopPropagation();

        });

    }


    // =====================================================
    // 6. PROFILE DROPDOWN
    // =====================================================

    if (profileBtn && profileDropdown) {

        profileBtn.addEventListener("click", function (event) {

            event.stopPropagation();

            const isOpen = profileDropdown.classList.contains("show");

            closeNotificationPanel();

            profileDropdown.classList.toggle(
                "show",
                !isOpen
            );

            profileBtn.setAttribute(
                "aria-expanded",
                String(!isOpen)
            );

        });


        // Prevent clicks inside the dropdown from closing it
        profileDropdown.addEventListener("click", function (event) {

            event.stopPropagation();

        });

    }


    // =====================================================
    // 7. CLOSE PANELS WHEN CLICKING OUTSIDE
    // =====================================================

    document.addEventListener("click", function (event) {

        if (
            notificationPanel &&
            notificationBtn &&
            !notificationPanel.contains(event.target) &&
            !notificationBtn.contains(event.target)
        ) {

            closeNotificationPanel();

        }


        if (
            profileDropdown &&
            profileBtn &&
            !profileDropdown.contains(event.target) &&
            !profileBtn.contains(event.target)
        ) {

            closeProfileDropdown();

        }

    });


    // =====================================================
    // 8. CLOSE PANELS WITH ESCAPE KEY
    // =====================================================

    document.addEventListener("keydown", function (event) {

        if (event.key === "Escape") {

            closeNotificationPanel();

            closeProfileDropdown();

        }

    });


    // =====================================================
    // 9. TEACHER PAGE NAVIGATION
    // =====================================================

    /*
        Django page URLs will be provided by Teacher_Base.html.

        This keeps the JavaScript independent of hardcoded
        URL paths and Django URL names.
    */

    const teacherRoutes = window.TEACHER_ROUTES || {};


    function navigateTo(page) {

        const destination = teacherRoutes[page];

        if (destination) {

            window.location.href = destination;

        } else {

            console.warn(
                "Teacher route is not configured:",
                page
            );

        }

    }


    // Sidebar and profile dropdown navigation
    document.querySelectorAll("[data-page]").forEach(function (button) {

        button.addEventListener("click", function () {

            const page = this.dataset.page;

            if (!page) {
                return;
            }

            navigateTo(page);

        });

    });


    // =====================================================
    // 10. VIEW ALL NOTIFICATIONS
    // =====================================================

    if (viewAllNotifications) {

        viewAllNotifications.addEventListener("click", function () {

            closeNotificationPanel();

            navigateTo("notifications");

        });

    }


    // =====================================================
    // 11. TEACHER LOGOUT
    // =====================================================

    if (teacherLogout) {

        teacherLogout.addEventListener("click", function () {

            /*
                Logout should be handled by a Django POST
                endpoint with CSRF protection.

                We will connect this button when implementing
                the Teacher authentication backend.
            */

            console.warn(
                "Teacher logout endpoint is not configured yet."
            );

        });

    }

});
    