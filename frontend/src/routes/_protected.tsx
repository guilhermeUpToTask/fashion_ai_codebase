import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { isLoggedIn } from "@/hooks/useAuth";

export const Route = createFileRoute("/_protected")({
    component: ProtectedLayout,
    beforeLoad: async () => {
        if (!isLoggedIn()) {
            throw redirect({
                to: "/login",
            });
        }
    },
});

function ProtectedLayout() {
    return (
        <div className="flex flex-col min-h-screen">
            <main className="flex-1 p-4">
                <Outlet />
            </main>
        </div>
    );
}

export default ProtectedLayout; 