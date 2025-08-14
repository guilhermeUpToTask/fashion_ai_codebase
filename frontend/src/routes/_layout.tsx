import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";

import { isLoggedIn } from "@/hooks/useAuth";

export const Route = createFileRoute("/_layout")({
    component: Layout,
    beforeLoad: async () => {
        if (!isLoggedIn()) {
            throw redirect({
                to: "/login",
            });
        }
    },
});

function Layout() {
    return (
        <div className="flex flex-col h-screen">
            <div className="flex flex-1 flex-col p-4 overflow-y-auto">
                <Outlet />
            </div>
        </div>
    );
}

export default Layout;
